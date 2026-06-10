import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const SCHEDULER_TIMEOUT = 60000;

export async function POST(req: NextRequest) {
  const body = await req.json();
  const { source } = body;
  const params = source ? `?source=${source}` : '';
  const authHeader = req.headers.get('Authorization');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), SCHEDULER_TIMEOUT);

  try {
    const res = await fetch(`${BACKEND_URL}/api/scheduler/scrape${params}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      signal: controller.signal,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      return NextResponse.json(
        { error: 'Scrape operation timeout' },
        { status: 504 }
      );
    }
    return NextResponse.json(
      { error: 'Failed to trigger scrape' },
      { status: 500 }
    );
  } finally {
    clearTimeout(timeout);
  }
}