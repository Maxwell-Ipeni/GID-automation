'use client';

import { useEffect, useState, useCallback } from 'react';
import {
  getTrends,
  syncTrends,
  getTrendProducts,
} from '@/lib/api';
import type { TrendData, PinterestPost } from '@/lib/api';

type TabSource = 'pinterest' | 'amazon';

const REGION_FLAGS: Record<string, string> = {
  us: '🇺🇸',
  uk: '🇬🇧',
  de: '🇩🇪',
  fr: '🇫🇷',
  it: '🇮🇹',
  es: '🇪🇸',
};

const REGION_LABELS: Record<string, string> = {
  us: 'US',
  uk: 'UK',
  de: 'DE',
  fr: 'FR',
  it: 'IT',
  es: 'ES',
};

function extractRegion(timeframe: string): string | null {
  for (const region of ['us', 'uk', 'de', 'fr', 'it', 'es']) {
    if (timeframe.endsWith(`_${region}`)) return region;
  }
  return null;
}

function parseTimeframeType(timeframe: string): string {
  if (timeframe.startsWith('week')) return 'This Week';
  if (timeframe.startsWith('amazon_daily')) return 'Amazon Daily';
  return 'Today';
}

export default function TrendsPage() {
  const [allTrends, setAllTrends] = useState<TrendData[]>([]);
  const [syncing, setSyncing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabSource>('pinterest');
  const [lastSync, setLastSync] = useState<string | null>(null);
  const [expandedKeyword, setExpandedKeyword] = useState<string | null>(null);
  const [trendProducts, setTrendProducts] = useState<Record<string, PinterestPost[]>>({});
  const [syncResult, setSyncResult] = useState<string | null>(null);
  const [regionFilter, setRegionFilter] = useState<string | null>(null);

  useEffect(() => {
    fetchTrends();
  }, []);

  async function fetchTrends() {
    setLoading(true);
    setError(null);
    try {
      const [pinterest, amazon] = await Promise.all([
        getTrends('pinterest'),
        getTrends('amazon'),
      ]);
      setAllTrends([...pinterest.trends, ...amazon.trends]);
    } catch (err) {
      console.error('Failed to fetch trends:', err);
      setError('Failed to load trends. Make sure the backend server is running.');
    } finally {
      setLoading(false);
    }
  }

  async function handleSync() {
    if (syncing) return;
    setSyncing(true);
    setSyncResult(null);
    try {
      const result = await syncTrends();
      const counts: string[] = [];
      for (const [key, val] of Object.entries(result.results ?? {})) {
        if (val && typeof val === 'object' && 'queued' in val && val.queued > 0) {
          counts.push(`${key}: ${val.queued} queued`);
        }
        if (val && typeof val === 'object' && 'count' in val && val.count > 0) {
          counts.push(`${key}: ${val.count} products`);
        }
      }
      setSyncResult(`Sync completed${counts.length ? ` — ${counts.join(', ')}` : ''}`);
      setLastSync(new Date().toLocaleTimeString());
      await fetchTrends();
    } catch (err) {
      console.error('Sync failed:', err);
      setSyncResult(`Sync failed — ${err instanceof Error ? err.message : 'check backend logs'}`);
    } finally {
      setSyncing(false);
    }
  }

  async function handleExpandKeyword(keyword: string) {
    if (expandedKeyword === keyword) {
      setExpandedKeyword(null);
      return;
    }
    setExpandedKeyword(keyword);
    if (!trendProducts[keyword]) {
      try {
        const result = await getTrendProducts(keyword);
        setTrendProducts((prev) => ({ ...prev, [keyword]: result.posts }));
      } catch (err) {
        console.error('Failed to fetch trend products:', err);
        setTrendProducts((prev) => ({ ...prev, [keyword]: [] }));
      }
    }
  }

  const filteredTrends = useCallback((): TrendData[] => {
    let filtered = allTrends.filter((t) => t.source === activeTab);
    if (regionFilter) {
      filtered = filtered.filter((t) => {
        const region = extractRegion(t.timeframe);
        return region === regionFilter;
      });
    }
    return filtered;
  }, [allTrends, activeTab, regionFilter]);

  const trends = filteredTrends();

  const availableRegions = new Set<string>();
  for (const t of allTrends) {
    if (t.source === activeTab) {
      const r = extractRegion(t.timeframe);
      if (r) availableRegions.add(r);
    }
  }
  const regionList = Array.from(availableRegions).sort();

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Trends</h1>
          <p className="text-gray-500 mt-1">
            Discover trending products from Pinterest &amp; Amazon across US, UK, DE, FR, IT, ES
            {lastSync && <span className="ml-2 text-xs text-gray-400">Last sync: {lastSync}</span>}
          </p>
        </div>
        <div className="flex items-center space-x-3">
          {syncResult && (
            <span className="text-sm text-green-600">{syncResult}</span>
          )}
          <button
            onClick={handleSync}
            disabled={syncing}
            className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            {syncing ? (
              <>
                <span className="animate-spin mr-2">⚙️</span>
                Syncing...
              </>
            ) : (
              '🔄 Sync Now'
            )}
          </button>
        </div>
      </div>

      {/* Source Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          <button
            onClick={() => setActiveTab('pinterest')}
            className={`py-4 px-1 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'pinterest'
                ? 'border-red-500 text-red-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            📌 Pinterest Trends
          </button>
          <button
            onClick={() => setActiveTab('amazon')}
            className={`py-4 px-1 border-b-2 text-sm font-medium transition-colors ${
              activeTab === 'amazon'
                ? 'border-orange-500 text-orange-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            🛒 Amazon Trends
          </button>
        </nav>
      </div>

      {/* Region Filter */}
      {regionList.length > 1 && (
        <div className="flex space-x-2 items-center">
          <span className="text-sm text-gray-500 font-medium">Region:</span>
          <button
            onClick={() => setRegionFilter(null)}
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              regionFilter === null
                ? 'bg-gray-800 text-white'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            All
          </button>
          {regionList.map((region) => (
            <button
              key={region}
              onClick={() => setRegionFilter(region)}
              className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium transition-colors ${
                regionFilter === region
                  ? 'bg-gray-800 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              <span className="mr-1">{REGION_FLAGS[region] || ''}</span>
              {REGION_LABELS[region] || region.toUpperCase()}
            </button>
          ))}
        </div>
      )}

      {/* Content */}
      {loading ? (
        <div className="flex items-center justify-center py-16">
          <div className="text-center">
            <div className="animate-spin text-4xl mb-4">⚙️</div>
            <p className="text-gray-500">Loading trends...</p>
          </div>
        </div>
      ) : error ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <span className="text-4xl">⚠️</span>
          <p className="text-red-500 mt-4">{error}</p>
          <button
            onClick={fetchTrends}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm"
          >
            Retry
          </button>
        </div>
      ) : trends.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-xl border border-gray-200">
          <span className="text-5xl">📊</span>
          <h3 className="text-lg font-medium text-gray-900 mt-4">
            {activeTab === 'pinterest'
              ? 'No Pinterest trends yet'
              : 'No Amazon trends yet'}
          </h3>
          <p className="text-gray-500 mt-2 text-sm">
            {activeTab === 'pinterest'
              ? 'Click "Sync Now" to fetch trending searches from Pinterest'
              : 'Click "Sync Now" to discover trending products from Amazon'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {trends.map((trend) => {
            const region = extractRegion(trend.timeframe);
            const timeframeType = parseTimeframeType(trend.timeframe);
            return (
              <div
                key={trend._id}
                className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden hover:shadow-md transition-shadow"
              >
                <button
                  onClick={() => handleExpandKeyword(trend.keyword)}
                  className="w-full flex items-center justify-between p-4 text-left"
                >
                  <div className="flex items-center space-x-4">
                    <span className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold">
                      {trend.rank}
                    </span>
                    <div>
                      <div className="flex items-center space-x-2">
                        <h3 className="font-medium text-gray-900">{trend.keyword}</h3>
                        {region && (
                          <>
                            <span className="text-lg">{REGION_FLAGS[region] || ''}</span>
                            <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                              {REGION_LABELS[region] || region.toUpperCase()}
                            </span>
                          </>
                        )}
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-50 text-blue-700">
                          {timeframeType}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500">
                        {trend.productCount > 0 ? (
                          <>
                            <span className="text-green-600 font-medium">{trend.productCount}</span> products found
                            {trend.queuedCount > 0 && (
                              <span className="ml-2">
                                · <span className="text-blue-600">{trend.queuedCount}</span> queued
                              </span>
                            )}
                            {trend.matchedAsins.length > 0 && (
                              <span className="ml-2">
                                · <span className="text-purple-600">{trend.matchedAsins.length}</span> matched
                              </span>
                            )}
                            {trend.discoveredAsins.length > 0 && (
                              <span className="ml-2">
                                · <span className="text-orange-600">{trend.discoveredAsins.length}</span> new
                              </span>
                            )}
                          </>
                        ) : (
                          <span className="text-gray-400">No products found</span>
                        )}
                      </p>
                    </div>
                  </div>
                  <span className="text-gray-400 text-xl">
                    {expandedKeyword === trend.keyword ? '▾' : '▸'}
                  </span>
                </button>

                {expandedKeyword === trend.keyword && (
                  <div className="border-t border-gray-100 px-4 py-3 bg-gray-50">
                    {trendProducts[trend.keyword] ? (
                      trendProducts[trend.keyword]!.length > 0 ? (
                        <div className="space-y-2">
                          {trendProducts[trend.keyword]!.map((post) => (
                            <div
                              key={post._id}
                              className="flex items-center space-x-3 p-2 bg-white rounded-lg border border-gray-200"
                            >
                              {(post.generatedImageUrl || post.imageUrl) ? (
                                <img
                                  src={post.generatedImageUrl || post.imageUrl}
                                  alt=""
                                  className="w-10 h-10 object-cover rounded"
                                />
                              ) : (
                                <div className="w-10 h-10 bg-gray-200 rounded flex items-center justify-center text-xs text-gray-500">
                                  {post.asin?.slice(0, 4)}
                                </div>
                              )}
                              <div className="flex-1 min-w-0">
                                <p className="text-sm font-medium text-gray-900 truncate">
                                  {post.pinTitle}
                                </p>
                                <p className="text-xs text-gray-500">ASIN: {post.asin}</p>
                              </div>
                              <StatusBadge status={post.status} />
                            </div>
                          ))}
                        </div>
                      ) : (
                        <p className="text-sm text-gray-500 text-center py-4">
                          No queued products for this keyword
                        </p>
                      )
                    ) : (
                      <div className="flex items-center justify-center py-4">
                        <div className="animate-spin text-xl">⚙️</div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    queued: 'bg-yellow-100 text-yellow-800',
    processing: 'bg-blue-100 text-blue-800',
    published: 'bg-green-100 text-green-800',
    failed: 'bg-red-100 text-red-800',
  };

  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
        colors[status] || 'bg-gray-100 text-gray-800'
      }`}
    >
      {status}
    </span>
  );
}
