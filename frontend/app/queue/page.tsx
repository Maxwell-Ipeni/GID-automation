'use client';

export default function QueuePage() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Pinterest Publishing Queue</h1>
          <p className="text-gray-500 mt-1">Manage and monitor your Pinterest publishing pipeline</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => fetch('http://localhost:8000/api/scheduler/publish', { method: 'POST' })}
            className="inline-flex items-center px-4 py-2 bg-pinterest-red text-white text-sm font-medium rounded-lg hover:bg-red-700 transition-colors"
          >
            ▶ Run Publisher
          </button>
        </div>
      </div>

      {/* Queue Summary */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        <SummaryCard label="Queued" value={0} color="yellow" />
        <SummaryCard label="Processing" value={0} color="blue" />
        <SummaryCard label="Published" value={0} color="green" />
        <SummaryCard label="Failed" value={0} color="red" />
      </div>

      {/* Queue Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Queue Items</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Product</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Scheduled</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td colSpan={4} className="px-6 py-12 text-center text-gray-500">
                  <span className="text-4xl block mb-2">📌</span>
                  <p className="text-sm">No items in queue</p>
                  <p className="text-xs mt-1">Products will appear here when queued for publishing</p>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Publishing Strategy */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Publishing Strategy</h2>
        <div className="space-y-3">
          <StrategyStep number={1} text="Queue Product" />
          <StrategyStep number={2} text="Wait Random Interval (15-45 min)" />
          <StrategyStep number={3} text="Generate Unique Content" />
          <StrategyStep number={4} text="Publish Single Pin" />
          <StrategyStep number={5} text="Wait Again" />
        </div>
      </div>
    </div>
  );
}

function SummaryCard({ label, value, color }: { label: string; value: number; color: string }) {
  const colors: Record<string, string> = {
    yellow: 'bg-yellow-50 border-yellow-200 text-yellow-800',
    blue: 'bg-blue-50 border-blue-200 text-blue-800',
    green: 'bg-green-50 border-green-200 text-green-800',
    red: 'bg-red-50 border-red-200 text-red-800',
  };

  return (
    <div className={`rounded-xl border p-4 ${colors[color] || colors.yellow}`}>
      <p className="text-2xl font-bold">{value}</p>
      <p className="text-sm">{label}</p>
    </div>
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
