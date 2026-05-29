'use client';

import clsx from 'clsx';

interface ProductCardProps {
  asin: string;
  title: string;
  price?: number;
  rating?: number;
  reviewCount?: number;
  imageUrl?: string;
  source?: string;
  trendScore?: number;
  onPublish?: () => void;
  affiliateUrl?: string;
}

export default function ProductCard({
  asin,
  title,
  price,
  rating,
  reviewCount,
  imageUrl,
  source,
  trendScore,
  onPublish,
  affiliateUrl,
}: ProductCardProps) {
  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow">
      <div className="aspect-[4/3] bg-gray-100 relative overflow-hidden">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={title}
            className="w-full h-full object-contain"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400">
            <svg className="w-12 h-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}
        {source && (
          <span className={clsx(
            'absolute top-2 left-2 px-2 py-0.5 rounded text-xs font-medium',
            source === 'bestsellers' && 'bg-yellow-100 text-yellow-800',
            source === 'movers' && 'bg-green-100 text-green-800',
            source === 'new_releases' && 'bg-blue-100 text-blue-800',
            source === 'deals' && 'bg-red-100 text-red-800',
          )}>
            {source.replace('_', ' ')}
          </span>
        )}
        {trendScore && (
          <span className="absolute top-2 right-2 bg-purple-100 text-purple-800 px-2 py-0.5 rounded text-xs font-medium">
            Score: {trendScore.toFixed(1)}
          </span>
        )}
      </div>
      <div className="p-4">
        <h3 className="font-medium text-sm text-gray-900 line-clamp-2 mb-2" title={title}>
          {title}
        </h3>
        <div className="flex items-center justify-between mb-2">
          {price && (
            <span className="text-lg font-bold text-gray-900">${price.toFixed(2)}</span>
          )}
          {rating && (
            <span className="flex items-center text-sm text-gray-600">
              <span className="text-yellow-400 mr-1">★</span>
              {rating.toFixed(1)}
              {reviewCount && <span className="ml-1 text-gray-400">({reviewCount})</span>}
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {onPublish && (
            <button
              onClick={onPublish}
              className="flex-1 bg-pinterest-red text-white text-sm font-medium py-2 px-3 rounded-lg hover:bg-red-700 transition-colors"
            >
              📌 Pin to Pinterest
            </button>
          )}
          {affiliateUrl && (
            <a
              href={affiliateUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="flex-1 bg-amazon-orange text-white text-sm font-medium py-2 px-3 rounded-lg hover:bg-orange-600 transition-colors text-center"
            >
              🔗 Affiliate Link
            </a>
          )}
        </div>
      </div>
    </div>
  );
}
