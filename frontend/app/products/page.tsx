'use client';

import { useEffect, useState } from 'react';
import ProductCard from '@/components/ProductCard';
import ContentPreviewModal from '@/components/ContentPreviewModal';
import { getProducts, getAffiliateLink, queuePinterestPost, triggerScrape, generatePinContent, generatePinImage } from '@/lib/api';
import type { Product, AiContent } from '@/lib/api';

const sources = ['bestsellers', 'movers', 'new_releases', 'deals'];

export default function ProductsPage() {
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeSource, setActiveSource] = useState<string | null>(null);
  const [queueing, setQueueing] = useState<string | null>(null);
  const [previewProduct, setPreviewProduct] = useState<Product | null>(null);
  const [previewContent, setPreviewContent] = useState<AiContent | null>(null);
  const [previewImageUrl, setPreviewImageUrl] = useState<string>('');
  const [generating, setGenerating] = useState(false);

  useEffect(() => {
    fetchProducts();
  }, [activeSource]);

  async function fetchProducts() {
    setLoading(true);
    try {
      const data = await getProducts(activeSource || undefined, undefined, 100);
      setProducts(data);
    } catch (err) {
      console.error('Failed to fetch products:', err);
    } finally {
      setLoading(false);
    }
  }

  async function handleRefresh() {
    try {
      await triggerScrape();
      setTimeout(fetchProducts, 2000);
    } catch (err) {
      console.error('Failed to trigger scrape:', err);
    }
  }

  async function handlePublish(product: Product) {
    setQueueing(product.asin);
    setGenerating(true);
    try {
      const { affiliate_link } = await getAffiliateLink(product.asin);

      const content = await generatePinContent(product);
      const imageResult = await generatePinImage(product, product.title || '', content.description, content.hashtags);

      setPreviewProduct(product);
      setPreviewContent(content);
      setPreviewImageUrl(imageResult.image_url);
      setQueueing(null);
      setGenerating(false);
    } catch (err) {
      console.error('Failed to generate content:', err);
      alert('AI generation failed. Try again.');
      setQueueing(null);
      setGenerating(false);
    }
  }

  async function handleConfirmQueue(content: AiContent, boardId?: string, boardName?: string) {
    if (!previewProduct || !previewContent) return;
    setGenerating(true);
    try {
      const { affiliate_link } = await getAffiliateLink(previewProduct.asin);
      await queuePinterestPost({
        product_id: previewProduct.convex_id,
        asin: previewProduct.asin,
        image_url: previewProduct.image_url || '',
        generated_image_url: previewImageUrl || undefined,
        pin_title: content.title,
        pin_description: content.description + '\n\n' + content.hashtags.join(' '),
        hashtags: content.hashtags,
        affiliate_url: affiliate_link,
        status: 'queued',
        board_id: boardId,
        board_name: boardName,
      });
      setPreviewProduct(null);
      setPreviewContent(null);
      setPreviewImageUrl('');
      alert('Product queued for Pinterest publishing!');
    } catch (err) {
      console.error('Failed to queue product:', err);
      alert('Failed to queue product');
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-500 mt-1">
            {products.length} products discovered from Amazon
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          🔄 Refresh Products
        </button>
      </div>

      {/* Source Filters */}
      <div className="flex space-x-2 overflow-x-auto pb-2">
        <button
          onClick={() => setActiveSource(null)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            !activeSource
              ? 'bg-gray-900 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          All Products
        </button>
        {sources.map((source) => (
          <button
            key={source}
            onClick={() => setActiveSource(source)}
            className={`px-4 py-2 rounded-lg text-sm font-medium whitespace-nowrap transition-colors ${
              activeSource === source
                ? 'bg-gray-900 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {source.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
          </button>
        ))}
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-16">
          <div className="text-center">
            <div className="animate-spin text-4xl mb-4">⚙️</div>
            <p className="text-gray-500">Loading products...</p>
          </div>
        </div>
      )}

      {/* Products Grid */}
      {!loading && products.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {products.map((product) => (
            <ProductCard
              key={product.asin}
              asin={product.asin}
              title={product.title || 'Unknown Product'}
              price={product.price}
              rating={product.rating}
              reviewCount={product.review_count}
              imageUrl={product.image_url}
              source={product.source}
              trendScore={product.trend_score}
              onPublish={() => handlePublish(product)}
              disabled={queueing === product.asin}
            />
          ))}
        </div>
      )}

      {/* Empty State */}
      {!loading && products.length === 0 && (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <span className="text-5xl">🛒</span>
          <h3 className="text-lg font-medium text-gray-900 mt-4">No products found</h3>
          <p className="text-gray-500 mt-2">Click "Refresh Products" to start discovering Amazon products</p>
        </div>
      )}

      {/* AI Content Preview Modal */}
      {previewProduct && previewContent && (
        <ContentPreviewModal
          product={previewProduct}
          content={previewContent}
          generatedImageUrl={previewImageUrl}
          onConfirm={handleConfirmQueue}
          onCancel={() => {
            setPreviewProduct(null);
            setPreviewContent(null);
            setPreviewImageUrl('');
          }}
          loading={generating}
        />
      )}

      {/* Loading overlay during AI generation */}
      {generating && !previewContent && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <div className="bg-white rounded-2xl p-8 text-center shadow-xl">
            <div className="animate-spin text-4xl mb-4">⚙️</div>
            <p className="text-gray-700 font-medium">Generating AI pin content...</p>
            <p className="text-gray-400 text-sm mt-1">Creating unique title, description, hashtags, and custom image</p>
          </div>
        </div>
      )}
    </div>
  );
}