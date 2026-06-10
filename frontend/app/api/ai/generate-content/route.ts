import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';
const AI_TIMEOUT = 120000;

export async function POST(req: NextRequest) {
  const body = await req.json();
  const authHeader = req.headers.get('Authorization');
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), AI_TIMEOUT);

  try {
    const res = await fetch(`${BACKEND_URL}/api/ai/generate-content`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(authHeader ? { Authorization: authHeader } : {}),
      },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error) {
    if (error instanceof Error && error.name === 'AbortError') {
      return NextResponse.json(
        { error: 'AI generation timeout' },
        { status: 504 }
      );
    }
    return NextResponse.json(
      { error: 'Failed to generate content' },
      { status: 500 }
    );
  } finally {
    clearTimeout(timeout);
  }
}