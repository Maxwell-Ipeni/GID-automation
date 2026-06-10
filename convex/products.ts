import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const list = query({
  args: {
    source: v.optional(v.string()),
    minScore: v.optional(v.number()),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    let products;

    if (args.source) {
      products = await ctx.db
        .query("products")
        .withIndex("by_source", (q) => q.eq("source", args.source!))
        .collect();
      products.sort((a, b) => (b.trendScore ?? 0) - (a.trendScore ?? 0));
      if (args.limit) products = products.slice(0, args.limit);
    } else {
      products = await ctx.db
        .query("products")
        .withIndex("by_trend_score")
        .order("desc")
        .take(args.limit ?? 50);
    }

    if (args.minScore !== undefined) {
      products = products.filter((p) => (p.trendScore ?? 0) >= args.minScore!);
    }

    return products;
  },
});

export const getSourceCounts = query({
  handler: async (ctx) => {
    const all = await ctx.db.query("products").collect();
    const sources: Record<string, number> = {};
    for (const p of all) {
      const s = p.source ?? "unknown";
      sources[s] = (sources[s] ?? 0) + 1;
    }
    return { total: all.length, sources };
  },
});

export const getTrending = query({
  args: { limit: v.optional(v.number()) },
  handler: async (ctx, args) => {
    const products = await ctx.db
      .query("products")
      .withIndex("by_trend_score")
      .order("desc")
      .take(args.limit ?? 20);
    return products;
  },
});

export const upsert = mutation({
  args: {
    asin: v.string(),
    title: v.string(),
    category: v.optional(v.string()),
    price: v.optional(v.number()),
    rating: v.optional(v.number()),
    reviewCount: v.optional(v.number()),
    bestsellerRank: v.optional(v.number()),
    trendScore: v.optional(v.number()),
    imageUrl: v.optional(v.string()),
    productUrl: v.string(),
    affiliateUrl: v.optional(v.string()),
    source: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("products")
      .withIndex("by_asin", (q) => q.eq("asin", args.asin))
      .first();

    if (existing) {
      const patch: Record<string, any> = {
        title: args.title,
        category: args.category,
        currentPrice: args.price,
        rating: args.rating,
        reviewCount: args.reviewCount,
        bestsellerRank: args.bestsellerRank,
        trendScore: args.trendScore,
        imageUrl: args.imageUrl,
        source: args.source,
      };
      if (args.affiliateUrl !== undefined) patch.affiliateUrl = args.affiliateUrl;
      await ctx.db.patch(existing._id, patch);
      return existing._id;
    } else {
      const insert: Record<string, any> = {
        asin: args.asin,
        title: args.title,
        category: args.category,
        currentPrice: args.price,
        rating: args.rating,
        reviewCount: args.reviewCount,
        bestsellerRank: args.bestsellerRank,
        trendScore: args.trendScore,
        imageUrl: args.imageUrl,
        productUrl: args.productUrl,
        source: args.source,
      };
      if (args.affiliateUrl !== undefined) insert.affiliateUrl = args.affiliateUrl;
      return await ctx.db.insert("products", insert);
    }
  },
});

export const remove = mutation({
  args: { id: v.id("products") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});

export const listByAsins = query({
  args: { asins: v.array(v.string()) },
  handler: async (ctx, args) => {
    const products = [];
    for (const asin of args.asins) {
      const p = await ctx.db
        .query("products")
        .withIndex("by_asin", (q) => q.eq("asin", asin))
        .first();
      if (p) products.push(p);
    }
    return products;
  },
});

export const listByTitle = query({
  args: { title: v.string() },
  handler: async (ctx, args) => {
    const all = await ctx.db.query("products").collect();
    return all.filter((p) => p.title === args.title);
  },
});

export const getBySources = query({
  args: {
    sources: v.array(v.string()),
    limit: v.number(),
  },
  handler: async (ctx, args) => {
    const all: any[] = [];
    for (const source of args.sources) {
      let products = await ctx.db
        .query("products")
        .withIndex("by_source", (q) => q.eq("source", source))
        .collect();
      products.sort((a, b) => (b.trendScore ?? 0) - (a.trendScore ?? 0));
      all.push(...products.slice(0, args.limit));
    }
    return all;
  },
});
