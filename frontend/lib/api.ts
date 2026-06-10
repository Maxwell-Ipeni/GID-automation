const API_BASE = '';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || '';

const DEFAULT_TIMEOUT = 900000;
const AI_TIMEOUT = 300000;

async function fetchWithTimeout(url: string, options: RequestInit = {}, timeout = DEFAULT_TIMEOUT): Promise<Response> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return res;
  } finally {
    clearTimeout(id);
  }
}

interface Stats {
  products: { total: number; sources: Record<string, number> };
  pinterest: { total: number; queued: number; published: number; failed: number };
  scraping: { recent: any[] };
  trending: any[];
}

interface Product {
  convex_id: string;
  asin: string;
  title: string;
  category?: string;
  price?: number;
  rating?: number;
  review_count?: number;
  bestseller_rank?: number;
  trend_score?: number;
  image_url?: string;
  product_url?: string;
  affiliate_url?: string;
  source?: string;
}

interface PinterestPost {
  _id: string;
  productId: string;
  asin: string;
  imageUrl: string;
  generatedImageUrl?: string;
  pinTitle: string;
  pinDescription: string;
  hashtags?: string[];
  affiliateUrl: string;
  status: 'queued' | 'processing' | 'published' | 'failed';
  scheduledAt?: number;
  publishedAt?: number;
  pinId?: string;
  errorMessage?: string;
  boardId?: string;
  boardName?: string;
}

export async function getStats(): Promise<Stats> {
  const res = await fetchWithTimeout(`${API_BASE}/api/stats`);
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function getProducts(source?: string, minScore?: number, limit = 50): Promise<Product[]> {
  const params = new URLSearchParams();
  if (source) params.set('source', source);
  if (minScore !== undefined) params.set('min_score', minScore.toString());
  params.set('limit', limit.toString());
  
  const res = await fetchWithTimeout(`${API_BASE}/api/products?${params}`);
  if (!res.ok) throw new Error('Failed to fetch products');
  return res.json();
}

export async function getTrendingProducts(limit = 20): Promise<Product[]> {
  const res = await fetchWithTimeout(`${API_BASE}/api/trending?limit=${limit}`);
  if (!res.ok) throw new Error('Failed to fetch trending products');
  return res.json();
}

export async function getAffiliateLink(asin: string): Promise<{ asin: string; affiliate_link: string }> {
  const res = await fetchWithTimeout(`${API_BASE}/api/affiliate/${asin}`, {
    headers: {
      'Authorization': `Bearer ${API_KEY}`
    }
  });
  if (!res.ok) throw new Error('Failed to fetch affiliate link');
  return res.json();
}

export async function getPinterestQueue(status?: string): Promise<{ posts: PinterestPost[]; count: number }> {
  const params = status ? `?status=${status}` : '';
  const res = await fetchWithTimeout(`${API_BASE}/api/pinterest/queue${params}`);
  if (!res.ok) throw new Error('Failed to fetch Pinterest queue');
  return res.json();
}

export async function getScrapingStatus(): Promise<{ logs: any[]; count: number }> {
  const res = await fetchWithTimeout(`${API_BASE}/api/scraping/status`);
  if (!res.ok) throw new Error('Failed to fetch scraping status');
  return res.json();
}

export async function triggerScrape(): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE}/api/scheduler/scrape`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    }
  });
  if (!res.ok) throw new Error('Failed to trigger scrape');
  return res.json();
}

export async function triggerPublish(limit = 5): Promise<any> {
  const res = await fetchWithTimeout(`${API_BASE}/api/scheduler/publish?limit=${limit}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    }
  });
  if (!res.ok) throw new Error('Failed to trigger publish');
  return res.json();
}

export async function manualPublish(postId: string): Promise<{ ok: boolean; error?: string }> {
  const res = await fetchWithTimeout(`${API_BASE}/api/queue/publish/${postId}`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    }
  });
  if (!res.ok) throw new Error('Failed to publish');
  return res.json();
}

interface QueuePinterestPayload {
  product_id: string;
  asin: string;
  image_url: string;
  generated_image_url?: string;
  pin_title: string;
  pin_description: string;
  hashtags?: string[];
  affiliate_url: string;
  status: string;
  board_id?: string;
  board_name?: string;
}

export async function queuePinterestPost(post: QueuePinterestPayload): Promise<{ status: string; post_id: string }> {
  const res = await fetchWithTimeout(`${API_BASE}/api/pinterest/queue`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(post),
  });
  if (!res.ok) {
    const errorBody = await res.text();
    throw new Error(`Failed to queue post: ${res.status} ${errorBody}`);
  }
  return res.json();
}

export interface AiContent {
  title: string;
  description: string;
  hashtags: string[];
}

export async function generatePinContent(product: Product): Promise<AiContent> {
  const res = await fetchWithTimeout(`${API_BASE}/api/ai/generate-content`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      asin: product.asin,
      title: product.title,
      category: product.category || null,
      image_url: product.image_url || '',
      source: product.source || null,
    }),
  }, AI_TIMEOUT);
  if (!res.ok) throw new Error('Failed to generate content');
  return res.json();
}

export async function generatePinImage(product: Product, title: string, description?: string, hashtags?: string[]): Promise<{ image_url: string; filename: string | null }> {
  const res = await fetchWithTimeout(`${API_BASE}/api/ai/generate-image`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      asin: product.asin,
      title: title,
      category: product.category || null,
      image_url: product.image_url || '',
      source: product.source || null,
      description: description || null,
      hashtags: hashtags || null,
    }),
  }, AI_TIMEOUT);
  if (!res.ok) throw new Error('Failed to generate image');
  return res.json();
}

export async function testPinterest(): Promise<{ success: boolean; message: string; boards: { id: string; name: string }[] }> {
  const res = await fetchWithTimeout(`${API_BASE}/api/pinterest/test`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    }
  });
  if (!res.ok) throw new Error('Failed to test Pinterest connection');
  return res.json();
}

export interface Board {
  id: string;
  name: string;
}

export async function getPinterestBoards(): Promise<{ boards: Board[]; count: number }> {
  const res = await fetchWithTimeout(`${API_BASE}/api/pinterest/boards`);
  if (!res.ok) throw new Error('Failed to fetch Pinterest boards');
  return res.json();
}

export async function createPinterestBoard(name: string, description?: string): Promise<{ id: string; name: string }> {
  const res = await fetchWithTimeout(`${API_BASE}/api/pinterest/boards/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name, description: description || `Curated ${name.toLowerCase()}` }),
  });
  if (!res.ok) throw new Error('Failed to create board');
  return res.json();
}

export async function getPinterestStatus(): Promise<{ configured: boolean; board_id: string | null; message: string }> {
  const res = await fetchWithTimeout(`${API_BASE}/api/pinterest/status`);
  if (!res.ok) throw new Error('Failed to get Pinterest status');
  return res.json();
}

interface BufferStatus {
  configured: boolean;
  channel_id: string | null;
  message: string;
}

interface SchedulerJob {
  id: string;
  next_run: string | null;
  interval: string;
}

interface SystemStatus {
  scraper: any;
  publisher: any;
  database: { status: string; last_run: string | null; message: string };
  scheduler: {
    status: string;
    last_run: string | null;
    message: string;
    schedule: SchedulerJob[];
  };
}

export async function getBufferStatus(): Promise<BufferStatus> {
  const res = await fetchWithTimeout(`${API_BASE}/api/buffer/status`);
  if (!res.ok) throw new Error('Failed to get Buffer status');
  return res.json();
}

export async function testBuffer(): Promise<{ success: boolean; message: string }> {
  const res = await fetchWithTimeout(`${API_BASE}/api/buffer/test`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    }
  });
  if (!res.ok) throw new Error('Failed to test Buffer connection');
  return res.json();
}

export async function getSystemStatus(): Promise<SystemStatus> {
  const res = await fetchWithTimeout(`${API_BASE}/api/system/status`);
  if (!res.ok) throw new Error('Failed to fetch system status');
  return res.json();
}

// Trend types
export interface TrendData {
  _id: string;
  keyword: string;
  rank: number;
  source: 'pinterest' | 'amazon';
  timeframe: string;
  matchedAsins: string[];
  discoveredAsins: string[];
  productCount: number;
  queuedCount: number;
  processedAt: number;
}

interface TrendsResponse {
  trends: TrendData[];
  count: number;
}

export async function getTrends(source?: string, timeframe?: string): Promise<TrendsResponse> {
  const params = new URLSearchParams();
  if (source) params.set('source', source);
  if (timeframe) params.set('timeframe', timeframe);
  const res = await fetchWithTimeout(`${API_BASE}/api/trends?${params}`);
  if (!res.ok) throw new Error('Failed to fetch trends');
  return res.json();
}

interface TrendSyncResult {
  status: string;
  results: Record<string, any>;
}

export async function syncTrends(): Promise<TrendSyncResult> {
  const res = await fetchWithTimeout(`${API_BASE}/api/trends/sync`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    }
  }, 240000);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.error || 'Failed to sync trends');
  }
  return res.json();
}

interface TrendProductsResponse {
  posts: PinterestPost[];
  count: number;
}

export async function getTrendProducts(keyword?: string, timeframe?: string): Promise<TrendProductsResponse> {
  const params = new URLSearchParams();
  if (keyword) params.set('keyword', keyword);
  if (timeframe) params.set('timeframe', timeframe);
  const res = await fetchWithTimeout(`${API_BASE}/api/trends/products?${params}`);
  if (!res.ok) throw new Error('Failed to fetch trend products');
  return res.json();
}

export type { Stats, Product, PinterestPost, BufferStatus, SchedulerJob, SystemStatus, TrendsResponse, TrendSyncResult, TrendProductsResponse };