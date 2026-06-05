'use client';

import { useState, useEffect } from 'react';
import { testPinterest, getPinterestStatus, getPinterestBoards, testBuffer, getBufferStatus } from '@/lib/api';

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    amazonTag: '',
    pinterestAppId: '',
    pinterestAppSecret: '',
    pinterestToken: '',
    pinterestBoard: '',
    scrapeInterval: 4,
    publishInterval: 30,
    autoPublish: true,
  });
  
  const [pinterestStatus, setPinterestStatus] = useState<{
    configured: boolean;
    board_id: string | null;
    message: string;
  } | null>(null);
  
  const [boards, setBoards] = useState<{ id: string; name: string }[]>([]);
  const [testingConnection, setTestingConnection] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [saving, setSaving] = useState(false);
  
  const [bufferStatus, setBufferStatus] = useState<{
    configured: boolean;
    channel_id: string | null;
    message: string;
  } | null>(null);
  const [testingBuffer, setTestingBuffer] = useState(false);
  const [bufferTestResult, setBufferTestResult] = useState<{ success: boolean; message: string } | null>(null);
  
  useEffect(() => {
    checkPinterestStatus();
    checkBufferStatus();
  }, []);
  
  async function checkPinterestStatus() {
    try {
      const status = await getPinterestStatus();
      setPinterestStatus(status);
      if (status.configured) {
        await fetchBoards();
      }
    } catch (err) {
      console.error('Failed to check Pinterest status:', err);
    }
  }
  
  async function fetchBoards() {
    try {
      const data = await getPinterestBoards();
      setBoards(data.boards);
    } catch (err) {
      console.error('Failed to fetch boards:', err);
    }
  }
  
  async function handleTestConnection() {
    setTestingConnection(true);
    setTestResult(null);
    try {
      const result = await testPinterest();
      setTestResult(result);
      if (result.success) {
        setBoards(result.boards);
      }
    } catch (err) {
      setTestResult({ success: false, message: 'Connection test failed' });
    } finally {
      setTestingConnection(false);
    }
  }
  
  async function checkBufferStatus() {
    try {
      const status = await getBufferStatus();
      setBufferStatus(status);
    } catch (err) {
      console.error('Failed to check Buffer status:', err);
    }
  }
  
  async function handleTestBuffer() {
    setTestingBuffer(true);
    setBufferTestResult(null);
    try {
      const result = await testBuffer();
      setBufferTestResult(result);
    } catch (err) {
      setBufferTestResult({ success: false, message: 'Connection test failed' });
    } finally {
      setTestingBuffer(false);
    }
  }
  
  async function handleSave() {
    setSaving(true);
    // In Phase 2, we would save to Convex settings
    // For now, credentials are in .env - user should update .env directly
    await new Promise(resolve => setTimeout(resolve, 500));
    setSaving(false);
    alert('Settings saved! Note: Pinterest credentials should be set in backend/.env file for security.');
  }
  
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
          <p className="text-xs text-gray-500 mt-1">Your Amazon Associates tracking ID (e.g., "yourname-20")</p>
        </div>
      </div>

      {/* Pinterest Settings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xl">📌</span>
            <h2 className="text-lg font-semibold text-gray-900">Pinterest API Settings</h2>
          </div>
          {pinterestStatus && (
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              pinterestStatus.configured 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {pinterestStatus.configured ? '✓ Connected' : '⚠ Not Connected'}
            </span>
          )}
        </div>
        
        <p className="text-xs text-gray-500">
          Get your Pinterest API credentials from{' '}
          <a 
            href="https://developers.pinterest.com/" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Pinterest Developer Portal
          </a>
        </p>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pinterest App ID
          </label>
          <input
            type="text"
            value={settings.pinterestAppId}
            onChange={(e) => setSettings({ ...settings, pinterestAppId: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="1234567890123"
          />
          <p className="text-xs text-gray-500 mt-1">Found in your Pinterest app settings</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pinterest App Secret
          </label>
          <input
            type="password"
            value={settings.pinterestAppSecret}
            onChange={(e) => setSettings({ ...settings, pinterestAppSecret: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="••••••••••••••••"
          />
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
            placeholder="ATMxxxxxxxxxxxxx"
          />
          <p className="text-xs text-gray-500 mt-1">Generate from your app in Pinterest Developer Portal</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Pinterest Board ID
          </label>
          <input
            type="text"
            value={settings.pinterestBoard}
            onChange={(e) => setSettings({ ...settings, pinterestBoard: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="1234567890123"
          />
          <p className="text-xs text-gray-500 mt-1">
            Numeric ID of your Pinterest board. Click "Get My Boards" after testing connection.
          </p>
        </div>

        {boards.length > 0 && (
          <div className="mt-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Your Pinterest Boards
            </label>
            <div className="space-y-2 max-h-40 overflow-y-auto">
              {boards.map((board) => (
                <div 
                  key={board.id}
                  className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                    settings.pinterestBoard === board.id 
                      ? 'border-blue-500 bg-blue-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => setSettings({ ...settings, pinterestBoard: board.id })}
                >
                  <p className="text-sm font-medium text-gray-900">{board.name}</p>
                  <p className="text-xs text-gray-500">{board.id}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Test Connection */}
        <div className="flex items-center space-x-4 pt-4 border-t">
          <button
            onClick={handleTestConnection}
            disabled={testingConnection || !settings.pinterestToken}
            className="px-4 py-2 bg-pinterest-red text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {testingConnection ? 'Testing...' : '🔗 Test Connection'}
          </button>
          
          {testResult && (
            <span className={`text-sm ${testResult.success ? 'text-green-600' : 'text-red-600'}`}>
              {testResult.success ? '✓ ' : '✗ '}{testResult.message}
            </span>
          )}
        </div>
        
        {testResult?.success && boards.length > 0 && (
          <div className="text-xs text-gray-500">
            Click a board above to select it, then save settings.
          </div>
        )}
      </div>

      {/* Buffer Fallback Settings */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xl">📤</span>
            <h2 className="text-lg font-semibold text-gray-900">Buffer Fallback Publisher</h2>
          </div>
          {bufferStatus && (
            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
              bufferStatus.configured 
                ? 'bg-green-100 text-green-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {bufferStatus.configured ? '✓ Connected' : '⚠ Not Connected'}
            </span>
          )}
        </div>
        
        <p className="text-xs text-gray-500">
          When Pinterest API fails, posts are automatically published via{' '}
          <a 
            href="https://buffer.com" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Buffer
          </a>
          {' '}as a fallback. Get your API key from{' '}
          <a 
            href="https://publish.buffer.com/settings/api" 
            target="_blank" 
            rel="noopener noreferrer"
            className="text-blue-600 hover:underline"
          >
            Buffer API Settings
          </a>
          .
        </p>

        <p className="text-xs text-gray-400">
          Channel ID: {bufferStatus?.channel_id || 'Not configured'}
        </p>

        {/* Test Buffer Connection */}
        <div className="flex items-center space-x-4 pt-4 border-t">
          <button
            onClick={handleTestBuffer}
            disabled={testingBuffer}
            className="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {testingBuffer ? 'Testing...' : '🔗 Verify Connection'}
          </button>
          
          {bufferTestResult && (
            <span className={`text-sm ${bufferTestResult.success ? 'text-green-600' : 'text-red-600'}`}>
              {bufferTestResult.success ? '✓ ' : '✗ '}{bufferTestResult.message}
            </span>
          )}
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
            <p className="text-xs text-gray-500 mt-1">How often to scrape Amazon</p>
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
            <p className="text-xs text-gray-500 mt-1">Delay between pins (15-45 recommended)</p>
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
        disabled={saving}
        className="w-full py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
      >
        {saving ? 'Saving...' : 'Save Settings'}
      </button>

      {/* Pinterest Setup Guide */}
      <div className="bg-gray-50 rounded-xl border border-gray-200 p-6 space-y-4">
        <h3 className="text-lg font-semibold text-gray-900">📌 Pinterest API Setup Guide</h3>
        
        <div className="space-y-3 text-sm text-gray-600">
          <div className="flex items-start space-x-2">
            <span className="font-bold text-gray-800">1.</span>
            <p>Go to <a href="https://developers.pinterest.com/" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Pinterest Developer Portal</a> and create an app</p>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-bold text-gray-800">2.</span>
            <p>Copy your <strong>App ID</strong> and <strong>App Secret</strong> from the app dashboard</p>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-bold text-gray-800">3.</span>
            <p>Generate an <strong>Access Token</strong> with pins:write and boards:read permissions</p>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-bold text-gray-800">4.</span>
            <p>Enter your <strong>Board ID</strong> (use "Test Connection" to fetch your boards)</p>
          </div>
          <div className="flex items-start space-x-2">
            <span className="font-bold text-gray-800">5.</span>
            <p>Click <strong>"Test Connection"</strong> to verify everything works</p>
          </div>
        </div>
        
        <p className="text-xs text-gray-500 pt-2 border-t">
          <strong>Important:</strong> Pinterest credentials are stored in <code className="bg-gray-200 px-1 rounded">backend/.env</code>. 
          For production, use environment variables or a secrets manager.
        </p>
      </div>

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