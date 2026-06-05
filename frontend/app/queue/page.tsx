'use client';

import { useEffect, useState } from 'react';
import { getPinterestQueue, triggerPublish, getStats } from '@/lib/api';
import type { PinterestPost } from '@/lib/api';

type TabType = 'queued' | 'published' | 'failed' | 'all';

export default function QueuePage() {
  const [posts, setPosts] = useState<PinterestPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>('all');
  const [stats, setStats] = useState({ total: 0, queued: 0, published: 0, failed: 0 });
  const [running, setRunning] = useState(false);

  useEffect(() => {
    fetchQueue();
    fetchStats();
    const interval = setInterval(() => {
      fetchQueue();
      fetchStats();
    }, 30000);
    return () => clearInterval(interval);
  }, [activeTab]);

  async function fetchQueue() {
    setLoading(true);
    try {
      const status = activeTab === 'all' ? undefined : activeTab;
      const data = await getPinterestQueue(status);
      setPosts(data.posts);
    } catch (err) {
      console.error('Failed to fetch queue:', err);
    } finally {
      setLoading(false);
    }
  }

  async function fetchStats() {
    try {
      const data = await getStats();
      setStats(data.pinterest);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }

  async function handleRunPublisher() {
    if (running) return;
    if (!confirm('Run Pinterest publisher? This will attempt to publish queued posts.')) return;
    
    setRunning(true);
    try {
      await triggerPublish(5);
      await fetchQueue();
      await fetchStats();
    } catch (err) {
      console.error('Failed to run publisher:', err);
    } finally {
      setRunning(false);
    }
  }

  const tabs: { key: TabType; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'queued', label: 'Queued' },
    { key: 'published', label: 'Published' },
    { key: 'failed', label: 'Failed' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pinterest Publishing Queue</h1>
          <p className="text-gray-500 mt-1">Manage and monitor your Pinterest publishing pipeline</p>
        </div>
        <button
          onClick={handleRunPublisher}
          disabled={running}
          className="inline-flex items-center px-4 py-2 bg-pinterest-red text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50"
        >
          {running ? '⏳ Running...' : '▶ Run Publisher'}
        </button>
      </div>

      {/* Queue Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <SummaryCard label="Total" value={stats.total} color="gray" />
        <SummaryCard label="Queued" value={stats.queued} color="yellow" />
        <SummaryCard label="Published" value={stats.published} color="green" />
        <SummaryCard label="Failed" value={stats.failed} color="red" />
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`py-4 px-1 border-b-2 text-sm font-medium transition-colors ${
                activeTab === tab.key
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Queue Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <div className="animate-spin text-4xl mb-4">⚙️</div>
                <p className="text-gray-500">Loading...</p>
              </div>
            </div>
          ) : posts.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50">
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Title</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Board</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Scheduled</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {posts.map((post) => (
                  <tr key={post._id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      {(post.generatedImageUrl || post.imageUrl) ? (
                        <img src={post.generatedImageUrl || post.imageUrl} alt="" className="w-12 h-12 object-cover rounded" />
                      ) : (
                        <div className="w-12 h-12 bg-gray-100 rounded flex items-center justify-center text-gray-400 text-xs font-medium">
                          {post.asin?.slice(0, 4)}
                        </div>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <p className="text-sm font-medium text-gray-900 line-clamp-2">{post.pinTitle}</p>
                      <p className="text-xs text-gray-500 mt-1">ASIN: {post.asin}</p>
                    </td>
                    <td className="px-6 py-4">
                      <StatusBadge status={post.status} />
                      {post.status === 'published' && post.pinId?.startsWith('buffer_') && (
                        <span className="ml-1.5 inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700">
                          Buffer
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {post.boardName ? (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700">
                          {post.boardName}
                        </span>
                      ) : (
                        <span className="text-xs text-gray-400">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {post.scheduledAt ? new Date(post.scheduledAt).toLocaleString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="px-6 py-12 text-center">
              <span className="text-4xl block mb-2">📌</span>
              <p className="text-sm text-gray-500">No items in queue</p>
              <p className="text-xs mt-1">Products will appear here when queued for publishing</p>
            </div>
          )}
        </div>
      </div>

      {/* Publishing Strategy */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Publishing Strategy</h2>
        <div className="space-y-3">
          <StrategyStep number={1} text="Product discovered and scraped from Amazon" />
          <StrategyStep number={2} text="Queued for Pinterest publishing with board assignment" />
          <StrategyStep number={3} text="Board resolved by category (or user override in preview)" />
          <StrategyStep number={4} text="Designer pin image generated (category-specific template)" />
          <StrategyStep number={5} text="Board auto-created on Pinterest if it doesn't exist yet" />
          <StrategyStep number={6} text="Publish to Pinterest — board selected by category" />
          <StrategyStep number={7} text="If Pinterest fails, fall back to Buffer.com" />
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    gray: 'bg-gray-50 border-gray-200 text-gray-800',
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    green: 'bg-green-50 border-green-200 text-green-800',
    red: 'bg-red-50 border-red-200 text-red-800',
  };

  return (
    <div className={`rounded-xl border p-4 ${colors[color] || colors.gray}`}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-sm">{label}</p>
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
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${colors[status] || 'bg-gray-100 text-gray-800'}`}>
      {status}
    </span>
  );
}

function StrategyStep({ number, text }: { number: number; text: string }) {
  return (
    <div className="flex items-center space-x-3">
      <span className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-sm font-bold">
        {number}
      </span>
      <span className="text-sm text-gray-700">{text}</span>
    </div>
  );
}