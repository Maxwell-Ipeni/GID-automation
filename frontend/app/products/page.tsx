'use client';

import { useState } from 'react';
import ProductCard from '@/components/ProductCard';

const MOCK_PRODUCTS = [
  {
    asin: 'B0C1234567',
    title: 'Wireless Bluetooth Earbuds with Noise Cancelling, 48H Playtime',
    price: 29.99,
    rating: 4.5,
    reviewCount: 1234,
    imageUrl: '',
    source: 'bestsellers',
    trendScore: 92.5,
    affiliateUrl: 'https://amazon.com/dp/B0C1234567/?tag=affiliate-20',
  },
  {
    asin: 'B0D7654321',
    title: 'Smart Home Security Camera 2K, Night Vision, Motion Detection',
    price: 45.99,
    rating: 4.3,
    reviewCount: 856,
    imageUrl: '',
    source: 'movers',
    trendScore: 88.1,
    affiliateUrl: 'https://amazon.com/dp/B0D7654321/?tag=affiliate-20',
  },
  {
    asin: 'B0E9876543',
    title: 'Portable Charger Power Bank 26800mAh, Fast Charging',
    price: 39.99,
    rating: 4.6,
    reviewCount: 2103,
    imageUrl: '',
    source: 'new_releases',
    trendScore: 85.3,
    affiliateUrl: 'https://amazon.com/dp/B0E9876543/?tag=affiliate-20',
  },
];

export default function ProductsPage() {
  const [activeSource, setActiveSource] = useState<string | null>(null);

  const sources = ['bestsellers', 'movers', 'new_releases', 'deals'];

  const filteredProducts = activeSource
    ? MOCK_PRODUCTS.filter(p => p.source === activeSource)
    : MOCK_PRODUCTS;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Products</h1>
          <p className="text-gray-500 mt-1">Discovered Amazon products ready for publishing</p>
        </div>
        <button
          onClick={() => fetch('http://localhost:8000/api/products/refresh', { method: 'POST' })}
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

      {/* Products Grid */}
      {filteredProducts.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredProducts.map((product) => (
            <ProductCard
              key={product.asin}
              {...product}
              onPublish={() => alert(`Publishing ${product.title} to Pinterest`)}
            />
          ))}
        </div>
      ) : (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <span className="text-5xl">🛒</span>
          <h3 className="text-lg font-medium text-gray-900 mt-4">No products found</h3>
          <p className="text-gray-500 mt-2">Click "Refresh Products" to start discovering Amazon products</p>
        </div>
      )}
    </div>
  );
}
