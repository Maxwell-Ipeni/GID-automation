import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: {
    status: v.optional(
      v.union(
        v.literal("queued"),
        v.literal("processing"),
        v.literal("published"),
        v.literal("failed"),
      ),
    ),
    boardId: v.optional(v.string()),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    if (args.status && args.boardId) {
      return await ctx.db
        .query("pinterestPosts")
        .withIndex("by_status", (q) => q.eq("status", args.status!))
        .filter((q) => q.eq(q.field("boardId"), args.boardId!))
        .order("desc")
        .take(args.limit ?? 50);
    }
    if (args.status) {
      return await ctx.db
        .query("pinterestPosts")
        .withIndex("by_status", (q) => q.eq("status", args.status!))
        .order("desc")
        .take(args.limit ?? 50);
    }
    return await ctx.db
      .query("pinterestPosts")
      .order("desc")
      .take(args.limit ?? 50);
  },
});

export const queue = mutation({
  args: {
    productId: v.id("products"),
    asin: v.string(),
    imageUrl: v.string(),
    generatedImageUrl: v.optional(v.string()),
    pinTitle: v.string(),
    pinDescription: v.string(),
    hashtags: v.optional(v.array(v.string())),
    affiliateUrl: v.string(),
    scheduledAt: v.optional(v.number()),
    boardId: v.optional(v.string()),
    boardName: v.optional(v.string()),
    priority: v.optional(v.number()),
    trendKeyword: v.optional(v.string()),
    trendTimeframe: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("pinterestPosts")
      .withIndex("by_product", (q) => q.eq("productId", args.productId))
      .filter((q) =>
        q.or(q.eq(q.field("status"), "queued"), q.eq(q.field("status"), "processing")),
      )
      .first();
    if (existing) {
      if ((args.priority ?? 0) > (existing.priority ?? 0)) {
        await ctx.db.patch(existing._id, {
          priority: args.priority,
          trendKeyword: args.trendKeyword,
          trendTimeframe: args.trendTimeframe,
        });
      }
      return existing._id;
    }
    return await ctx.db.insert("pinterestPosts", {
      productId: args.productId,
      asin: args.asin,
      imageUrl: args.imageUrl,
      generatedImageUrl: args.generatedImageUrl,
      pinTitle: args.pinTitle,
      pinDescription: args.pinDescription,
      hashtags: args.hashtags,
      affiliateUrl: args.affiliateUrl,
      scheduledAt: args.scheduledAt,
      boardId: args.boardId,
      boardName: args.boardName,
      priority: args.priority,
      trendKeyword: args.trendKeyword,
      trendTimeframe: args.trendTimeframe,
      status: "queued",
    });
  },
});

export const publish = mutation({
  args: {
    postId: v.id("pinterestPosts"),
    pinId: v.string(),
    publishedAt: v.number(),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.postId, {
      status: "published",
      pinId: args.pinId,
      publishedAt: args.publishedAt,
    });
  },
});

export const markFailed = mutation({
  args: {
    postId: v.id("pinterestPosts"),
    errorMessage: v.string(),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.postId, {
      status: "failed",
      errorMessage: args.errorMessage,
    });
  },
});

export const markProcessing = mutation({
  args: {
    postId: v.id("pinterestPosts"),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.postId, {
      status: "processing",
    });
  },
});

export const retry = mutation({
  args: {
    postId: v.id("pinterestPosts"),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.postId, {
      status: "queued",
      errorMessage: undefined,
    });
  },
});

export const updateBoard = mutation({
  args: {
    postId: v.id("pinterestPosts"),
    boardId: v.string(),
    boardName: v.string(),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.postId, {
      boardId: args.boardId,
      boardName: args.boardName,
    });
  },
});

export const createBoard = mutation({
  args: {
    name: v.string(),
    description: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("pinterestBoards", {
      name: args.name,
      description: args.description,
      createdAt: Date.now(),
    });
  },
});

export const listBoards = query({
  args: {},
  handler: async (ctx) => {
    return await ctx.db.query("pinterestBoards").order("desc").collect();
  },
});

export const getStats = query({
  handler: async (ctx) => {
    const [total, queued, published, failed] = await Promise.all([
      ctx.db.query("pinterestPosts").collect().then((r) => r.length),
      ctx.db
        .query("pinterestPosts")
        .withIndex("by_status", (q) => q.eq("status", "queued"))
        .collect()
        .then((r) => r.length),
      ctx.db
        .query("pinterestPosts")
        .withIndex("by_status", (q) => q.eq("status", "published"))
        .collect()
        .then((r) => r.length),
      ctx.db
        .query("pinterestPosts")
        .withIndex("by_status", (q) => q.eq("status", "failed"))
        .collect()
        .then((r) => r.length),
    ]);
    return { total, queued, published, failed };
  },
});

export const listQueuedProductIds = query({
  handler: async (ctx) => {
    const posts = await ctx.db
      .query("pinterestPosts")
      .withIndex("by_status", (q) => q.eq("status", "queued"))
      .collect();
    const processing = await ctx.db
      .query("pinterestPosts")
      .withIndex("by_status", (q) => q.eq("status", "processing"))
      .collect();
    const ids = new Set<string>();
    for (const p of [...posts, ...processing]) {
      if (p.productId) ids.add(p.productId);
    }
    return Array.from(ids);
  },
});

export const listTrendingProductIds = query({
  handler: async (ctx) => {
    const posts = await ctx.db
      .query("pinterestPosts")
      .collect();
    const ids = new Set<string>();
    for (const p of posts) {
      if (p.trendKeyword && p.productId) {
        ids.add(p.productId as string);
      }
    }
    return Array.from(ids);
  },
});

export const getQueueBalance = query({
  handler: async (ctx) => {
    const queued = await ctx.db
      .query("pinterestPosts")
      .withIndex("by_status", (q) => q.eq("status", "queued"))
      .collect();

    const balance: Record<string, number> = {
      trending: 0,
      bestsellers: 0,
      new_releases: 0,
      movers: 0,
      deals: 0,
    };

    for (const post of queued) {
      if (post.trendKeyword) {
        balance.trending = (balance.trending ?? 0) + 1;
      } else if (post.productId) {
        const product = await ctx.db.get(post.productId);
        if (product) {
          const source = (product as any).source ?? "unknown";
          if (source in balance) {
            balance[source] = (balance[source] ?? 0) + 1;
          }
        }
      }
    }

    return balance;
  },
});

export const getQueueCount = query({
  handler: async (ctx) => {
    const posts = await ctx.db
      .query("pinterestPosts")
      .withIndex("by_status", (q) => q.eq("status", "queued"))
      .collect();
    return posts.length;
  },
});

export const remove = mutation({
  args: { id: v.id("pinterestPosts") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

export const listByPriority = query({
  args: { status: v.optional(v.string()), limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const s = args.status ?? "queued";
    const posts = await ctx.db
      .query("pinterestPosts")
      .withIndex("by_status", (q) => q.eq("status", s))
      .collect();
    posts.sort((a, b) => {
      const pA = a.priority ?? 0;
      const pB = b.priority ?? 0;
      if (pB !== pA) return pB - pA;
      return (b._creationTime ?? 0) - (a._creationTime ?? 0);
    });
    return posts.slice(0, args.limit ?? 50);
  },
});

export const trendsSave = mutation({
  args: {
    keyword: v.string(),
    rank: v.number(),
    source: v.union(v.literal("pinterest"), v.literal("amazon")),
    timeframe: v.string(),
    matchedAsins: v.array(v.string()),
    discoveredAsins: v.array(v.string()),
    productCount: v.number(),
    queuedCount: v.number(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("pinterestTrends")
      .withIndex("by_source_timeframe", (q) =>
        q.eq("source", args.source).eq("timeframe", args.timeframe),
      )
      .filter((q) => q.eq(q.field("keyword"), args.keyword))
      .first();
    if (existing) {
      await ctx.db.patch(existing._id, {
        rank: args.rank,
        matchedAsins: args.matchedAsins,
        discoveredAsins: args.discoveredAsins,
        productCount: args.productCount,
        queuedCount: args.queuedCount,
        processedAt: Date.now(),
      });
      return existing._id;
    }
    return await ctx.db.insert("pinterestTrends", {
      keyword: args.keyword,
      rank: args.rank,
      source: args.source,
      timeframe: args.timeframe,
      matchedAsins: args.matchedAsins,
      discoveredAsins: args.discoveredAsins,
      productCount: args.productCount,
      queuedCount: args.queuedCount,
      processedAt: Date.now(),
    });
  },
});

export const trendsList = query({
  args: {
    source: v.optional(v.union(v.literal("pinterest"), v.literal("amazon"))),
    timeframe: v.optional(v.string()),
  },
  handler: async (ctx, args) => {
    let trends;
    if (args.source && args.timeframe) {
      trends = await ctx.db
        .query("pinterestTrends")
        .withIndex("by_source_timeframe", (q) =>
          q.eq("source", args.source!).eq("timeframe", args.timeframe!),
        )
        .collect();
    } else if (args.source) {
      trends = await ctx.db
        .query("pinterestTrends")
        .filter((q) => q.eq(q.field("source"), args.source!))
        .collect();
    } else {
      trends = await ctx.db.query("pinterestTrends").collect();
    }
    trends.sort((a, b) => a.rank - b.rank);
    return trends;
  },
});

export const listByTrendKeyword = query({
  args: {
    keyword: v.string(),
    timeframe: v.optional(v.string()),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    let posts = await ctx.db.query("pinterestPosts").collect();
    posts = posts.filter((p) => p.trendKeyword === args.keyword);
    if (args.timeframe) {
      posts = posts.filter((p) => p.trendTimeframe === args.timeframe);
    }
    posts.sort((a, b) => (b._creationTime ?? 0) - (a._creationTime ?? 0));
    return posts.slice(0, args.limit ?? 50);
  },
});
