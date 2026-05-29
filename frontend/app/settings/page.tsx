'use client';

import { useState } from 'react';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    amazonTag: 'your-amazon-affiliate-tag-20',
    pinterestToken: '••••••••••••••••',
    pinterestBoard: 'your-board-id',
    scrapeInterval: 4,
    publishInterval: 30,
    autoPublish: true,
  });

  const handleSave = () => {
    alert('Settings saved! (In production, these would be persisted to Convex DB)');
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-500 mt-1">Configure your Amazon affiliate and Pinterest automation</p>
      </div>

      {/* Amazon Settings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        <div className="flex items-center space-x-2">
          <span className="text-xl">🛒</span>
          <h2 className="text-lg font-semibold text-gray-900">Amazon Affiliate Settings</h2>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Amazon Affiliate Tag
          </label>
          <input
            type="text"
            value={settings.amazonTag}
            onChange={(e) => setSettings({ ...settings, amazonTag: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="your-tag-20"
          />
          <p className="text-xs text-gray-500 mt-1">Your Amazon Associates tracking ID</p>
        </div>
      </div>

      {/* Pinterest Settings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        <div className="flex items-center space-x-2">
          <span className="text-xl">📌</span>
          <h2 className="text-lg font-semibold text-gray-900">Pinterest API Settings</h2>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pinterest Access Token
          </label>
          <input
            type="password"
            value={settings.pinterestToken}
            onChange={(e) => setSettings({ ...settings, pinterestToken: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="pina-xxxxxxxx"
          />
          <p className="text-xs text-gray-500 mt-1">From Pinterest Developer API</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Board ID
          </label>
          <input
            type="text"
            value={settings.pinterestBoard}
            onChange={(e) => setSettings({ ...settings, pinterestBoard: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="board-id"
          />
        </div>
      </div>

      {/* Scheduling Settings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        <div className="flex items-center space-x-2">
          <span className="text-xl">⏰</span>
          <h2 className="text-lg font-semibold text-gray-900">Scheduling</h2>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Scrape Interval (hours)
            </label>
            <input
              type="number"
              value={settings.scrapeInterval}
              onChange={(e) => setSettings({ ...settings, scrapeInterval: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              min={1}
              max={24}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Publish Interval (minutes)
            </label>
            <input
              type="number"
              value={settings.publishInterval}
              onChange={(e) => setSettings({ ...settings, publishInterval: parseInt(e.target.value) })}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              min={5}
              max={120}
            />
          </div>
        </div>

        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-700">Auto-Publish</p>
            <p className="text-xs text-gray-500">Automatically publish queued pins</p>
          </div>
          <button
            onClick={() => setSettings({ ...settings, autoPublish: !settings.autoPublish })}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
              settings.autoPublish ? 'bg-blue-600' : 'bg-gray-300'
            }`}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                settings.autoPublish ? 'translate-x-6' : 'translate-x-1'
              }`}
            />
          </button>
        </div>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors"
      >
        Save Settings
      </button>

      {/* Danger Zone */}
      <div className="bg-red-50 rounded-xl border border-red-200 p-6">
        <h2 className="text-lg font-semibold text-red-900 mb-2">Danger Zone</h2>
        <p className="text-sm text-red-700 mb-4">These actions are irreversible.</p>
        <div className="flex space-x-3">
          <button className="px-4 py-2 bg-red-600 text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors">
            Clear All Products
          </button>
          <button className="px-4 py-2 bg-red-100 text-red-700 text-sm font-medium rounded-lg hover:bg-red-200 transition-colors">
            Reset Queue
          </button>
        </div>
      </div>
    </div>
  );
}
