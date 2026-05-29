'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.push('/dashboard');
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="text-center">
        <span className="text-4xl">🚀</span>
        <p className="mt-4 text-gray-500">Redirecting to dashboard...</p>
      </div>
    </div>
  );
}
