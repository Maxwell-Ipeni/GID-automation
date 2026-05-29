'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function DashboardPage() {
  const [stats, setStats] = useState({
    products: 0,
    queued: 0,
    published: 0,
    failed: 0,
  });

  useEffect(() => {
    // In production, fetch from API
    fetch('http://localhost:8000/api/scraping/status')
      .then(r => r.json())
      .catch(() => {});
  }, []);

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
          + Add Products
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Products Discovered"
          value={stats.products}
          icon="🛒"
          color="blue"
        />
        <StatCard
          title="Queued for Publishing"
          value={stats.queued}
          icon="📌"
          color="yellow"
        />
        <StatCard
          title="Published to Pinterest"
          value={stats.published}
          icon="✅"
          color="green"
        />
        <StatCard
          title="Failed Posts"
          value={stats.failed}
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
              onClick={() => fetch('http://localhost:8000/api/products/refresh', { method: 'POST' })}
            />
            <ActionButton
              label="Publish Next Queued Pin"
              description="Post the next item in your Pinterest queue"
              icon="📌"
              onClick={() => {}}
            />
            <ActionButton
              label="Generate Affiliate Links"
              description="Create Amazon affiliate links for all products"
              icon="🔗"
              onClick={() => {}}
            />
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
          <div className="space-y-3">
            <StatusRow label="Amazon Scraper" status="active" />
            <StatusRow label="Pinterest Publisher" status="active" />
            <StatusRow label="Scheduler" status="active" />
            <StatusRow label="Database (Convex)" status="connected" />
          </div>
        </div>
      </div>

      {/* Recent Products / Activity */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
          <Link href="/products" className="text-sm text-blue-600 hover:text-blue-700">
            View all →
          </Link>
        </div>
        <div className="text-center py-8 text-gray-500">
          <p className="text-lg mb-2">No recent activity</p>
          <p className="text-sm">Start by scraping products from Amazon</p>
        </div>
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

function ActionButton({ label, description, icon, onClick }: { label: string; description: string; icon: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full flex items-start space-x-3 p-3 rounded-lg hover:bg-gray-50 transition-colors text-left"
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
    idle: 'bg-gray-100 text-gray-800',
    error: 'bg-red-100 text-red-800',
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
