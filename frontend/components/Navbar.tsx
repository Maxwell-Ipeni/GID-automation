'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import clsx from 'clsx';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: '📊' },
  { name: 'Products', href: '/products', icon: '🛒' },
  { name: 'Pinterest Queue', href: '/queue', icon: '📌' },
  { name: 'Settings', href: '/settings', icon: '⚙️' },
];

export default function Navbar() {
  const pathname = usePathname();

  return (
    <nav className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/dashboard" className="flex items-center space-x-2">
              <span className="text-2xl">🚀</span>
              <span className="font-bold text-xl text-gray-900">Get It Done</span>
            </Link>
            <div className="hidden sm:ml-8 sm:flex sm:space-x-4">
              {navigation.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className={clsx(
                    'inline-flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors',
                    pathname === item.href
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  )}
                >
                  <span className="mr-1.5">{item.icon}</span>
                  {item.name}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
              ● Running
            </span>
          </div>
        </div>
      </div>
      {/* Mobile Navigation */}
      <div className="sm:hidden border-t border-gray-200">
        <div className="flex justify-around py-2">
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className={clsx(
                'flex flex-col items-center px-2 py-1 text-xs font-medium',
                pathname === item.href
                  ? 'text-blue-700'
                  : 'text-gray-500'
              )}
            >
              <span className="text-lg">{item.icon}</span>
              {item.name}
            </Link>
          ))}
        </div>
      </div>
    </nav>
  );
}
