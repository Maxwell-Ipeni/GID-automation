'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { getStats, getTrendingProducts, getScrapingStatus, getBufferStatus, getSystemStatus, triggerScrape, triggerPublish } from '@/lib/api';
import type { Stats, Product, SystemStatus } from '@/lib/api';

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [bufferStatus, setBufferStatus] = useState<{ configured: boolean; message: string } | null>(null);
  const [loading, setLoading] = useState(true);
  const [publishing, setPublishing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
    const dataInterval = setInterval(fetchData, 30000);
    return () => clearInterval(dataInterval);
  }, []);

  useEffect(() => {
    const fetchSystemStatus = async () => {
      try {
        const [status, bufferRes] = await Promise.all([
          getSystemStatus(),
          getBufferStatus(),
        ]);
        setSystemStatus(status);
        setBufferStatus(bufferRes);
      } catch {}
    };
    fetchSystemStatus();
    const statusInterval = setInterval(fetchSystemStatus, 3000);
    return () => clearInterval(statusInterval);
  }, []);

  async function fetchData() {
    try {
      const [statsData, trendingData, scrapingData] = await Promise.all([
        getStats(),
        getTrendingProducts(5),
        getScrapingStatus(),
      ]);
      setStats({
        ...statsData,
        scraping: { recent: scrapingData.logs },
        trending: trendingData,
      });
      setError(null);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
      setError('Failed to connect to backend. Make sure the server is running.');
    } finally {
      setLoading(false);
    }
  }

  async function handleScrape() {
    if (!confirm('Manually trigger Amazon product scraping? This may take a few minutes.')) return;
    try {
      await triggerScrape();
      await fetchData();
    } catch (err) {
      console.error('Failed to trigger scrape:', err);
    }
  }

  async function handlePublish() {
    if (publishing) return;
    setPublishing(true);
    try {
      await triggerPublish(3);
      await fetchData();
    } catch (err) {
      console.error('Failed to trigger publish:', err);
    } finally {
      setPublishing(false);
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <div className="animate-spin text-4xl mb-4">⚙️</div>
          <p className="text-gray-500">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center">
          <span className="text-4xl">⚠️</span>
          <p className="mt-4 text-red-500">{error}</p>
          <button onClick={fetchData} className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg">
            Retry
          </button>
        </div>
      </div>
    );
  }

  const pinterestStats = stats?.pinterest || { total: 0, queued: 0, published: 0, failed: 0 };
  const productsCount = stats?.products?.total || 0;

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-500 mt-1">Overview of your affiliate automation system</p>
        </div>
        <Link
          href="/products"
          className="inline-flex items-center px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          View Products
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Products Discovered"
          value={productsCount}
          icon="🛒"
          color="blue"
        />
        <StatCard
          title="Queued for Publishing"
          value={pinterestStats.queued}
          icon="📌"
          color="yellow"
        />
        <StatCard
          title="Published to Pinterest"
          value={pinterestStats.published}
          icon="✅"
          color="green"
        />
        <StatCard
          title="Failed Posts"
          value={pinterestStats.failed}
          icon="❌"
          color="red"
        />
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
          <div className="space-y-3">
            <ActionButton
              label="Refresh Products from Amazon"
              description="Scrape best sellers, movers & shakers, and deals"
              icon="🔄"
              onClick={handleScrape}
            />
        <ActionButton
          label={publishing ? 'Publishing...' : 'Publish Next Queued Pin'}
          description={publishing ? 'Please wait...' : 'Post the next item in your Pinterest queue'}
          icon="📌"
          onClick={handlePublish}
          disabled={publishing}
        />
      </div>
    </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
        <div className="space-y-3">
          <StatusRow
            label="Amazon Scraper"
            status={systemStatus?.scraper?.status === 'scraping' ? 'scraping' : (stats?.scraping?.recent?.[0]?.status || 'idle')}
          />
          <StatusRow
            label="Pinterest Publisher"
            status={systemStatus?.publisher?.status === 'publishing' ? 'publishing' : (systemStatus?.publisher?.status || 'idle')}
          />
          <StatusRow
            label="Scheduler"
            status={systemStatus?.scheduler?.status || 'idle'}
          />
          <StatusRow
            label="Database (Convex)"
            status={systemStatus?.database?.status || 'disconnected'}
          />
          <StatusRow
            label="Buffer Fallback"
            status={bufferStatus?.configured ? 'connected' : 'disconnected'}
          />
        </div>
        {systemStatus?.scheduler?.schedule && systemStatus.scheduler.schedule.length > 0 && (
          <div className="mt-4 pt-4 border-t border-gray-100">
            <h3 className="text-sm font-medium text-gray-700 mb-2">Upcoming Runs</h3>
            <div className="space-y-2">
              {systemStatus.scheduler.schedule.map((job) => (
                <ScheduleRow key={job.id} job={job} />
              ))}
            </div>
          </div>
        )}
      </div>
      </div>

      {/* Trending Products */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Trending Products</h2>
          <Link href="/products" className="text-sm text-blue-600 hover:text-blue-700">
            View all →
          </Link>
        </div>
        {stats?.trending && stats.trending.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
            {stats.trending.slice(0, 5).map((product: Product) => (
              <div key={product.asin} className="border rounded-lg p-3 hover:shadow-md transition-shadow">
                {product.image_url && (
                  <img src={product.image_url} alt={product.title} className="w-full h-24 object-contain mb-2" />
                )}
                <p className="text-sm font-medium line-clamp-2">{product.title}</p>
                <div className="mt-2 flex items-center justify-between">
                  {product.price && <span className="text-sm font-bold">${product.price}</span>}
                  {product.trend_score && (
                    <span className="text-xs bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                      Score: {product.trend_score.toFixed(1)}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p className="text-lg mb-2">No trending products yet</p>
            <p className="text-sm">Products will appear here after the first scrape</p>
          </div>
        )}
      </div>

      {/* Recent Scraping Logs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
          <Link href="/queue" className="text-sm text-blue-600 hover:text-blue-700">
            View queue →
          </Link>
        </div>
        {stats?.scraping?.recent && stats.scraping.recent.length > 0 ? (
          <div className="space-y-2">
            {stats.scraping.recent.map((log: any, index: number) => (
              <div key={index} className="flex items-center justify-between py-2 border-b last:border-0">
                <div>
                  <span className="text-sm font-medium capitalize">{log.source}</span>
                  <span className="text-sm text-gray-500 ml-2">
                    {log.productsFound || 0} products found
                  </span>
                </div>
                <StatusBadge status={log.status} />
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            <p className="text-sm">No scraping activity yet</p>
          </div>
        )}
      </div>
    </div>
  );
}

function StatCard({ title, value, icon, color }: { title: string; value: number; icon: string; color: string }) {
  const colors: Record<string, string> = {
    blue: 'bg-blue-50 border-blue-200',
    yellow: 'bg-yellow-50 border-yellow-200',
    green: 'bg-green-50 border-green-200',
    red: 'bg-red-50 border-red-200',
  };

  return (
    <div className={`rounded-xl border p-6 ${colors[color] || colors.blue}`}>
      <div className="flex items-center justify-between">
        <span className="text-3xl">{icon}</span>
      </div>
      <p className="text-3xl font-bold text-gray-900 mt-2">{value}</p>
      <p className="text-sm text-gray-600 mt-1">{title}</p>
    </div>
  );
}

function ActionButton({ label, description, icon, onClick, disabled }: { label: string; description: string; icon: string; onClick: () => void; disabled?: boolean }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`w-full flex items-start space-x-3 p-3 rounded-lg transition-colors text-left ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:bg-gray-50'}`}
    >
      <span className="text-xl mt-0.5">{icon}</span>
      <div>
        <p className="text-sm font-medium text-gray-900">{label}</p>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
    </button>
  );
}

function StatusRow({ label, status }: { label: string; status: string }) {
  const statusColors: Record<string, string> = {
    active: 'bg-green-100 text-green-800',
    connected: 'bg-blue-100 text-blue-800',
    disconnected: 'bg-gray-100 text-gray-800',
    idle: 'bg-gray-100 text-gray-800',
    error: 'bg-red-100 text-red-800',
    completed: 'bg-green-100 text-green-800',
    running: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
    scraping: 'bg-orange-100 text-orange-800',
    publishing: 'bg-blue-100 text-blue-800',
  };

  return (
    <div className="flex items-center justify-between py-2">
      <span className="text-sm text-gray-700">{label}</span>
      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[status] || statusColors.idle}`}>
        {status}
      </span>
    </div>
  );
}

function ScheduleRow({ job }: { job: { id: string; next_run: string | null; interval: string } }) {
  const jobLabels: Record<string, string> = {
    scrape_job: 'Next Scrape',
    publish_job: 'Next Publish',
    trends_job: 'Next Trends',
  };

  function formatTime(iso: string | null): string {
    if (!iso) return '—';
    const diff = new Date(iso).getTime() - Date.now();
    if (diff <= 0) return 'Any moment';
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    const parts: string[] = [];
    if (h > 0) parts.push(`${h}h`);
    if (m > 0) parts.push(`${m}m`);
    if (parts.length === 0) return '<1m';
    const rel = parts.join(' ') + ' left';
    const abs = new Date(iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    return `${rel} (${abs})`;
  }

  return (
    <div className="flex items-center justify-between text-sm">
      <span className="text-gray-600">{jobLabels[job.id] || job.id}</span>
      <span className="text-gray-900 font-medium">{formatTime(job.next_run)}</span>
    </div>
  );
}

function StatusBadge({ status }: { status: string }) {
  const statusColors: Record<string, string> = {
    active: 'bg-green-100 text-green-800',
    connected: 'bg-blue-100 text-blue-800',
    disconnected: 'bg-gray-100 text-gray-800',
    completed: 'bg-green-100 text-green-800',
    running: 'bg-yellow-100 text-yellow-800',
    failed: 'bg-red-100 text-red-800',
    idle: 'bg-gray-100 text-gray-800',
    scraping: 'bg-orange-100 text-orange-800',
    publishing: 'bg-blue-100 text-blue-800',
  };

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[status] || statusColors.idle}`}>
      {status}
    </span>
  );
}