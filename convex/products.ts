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
    } else {
      products = await ctx.db.query("products").collect();
    }

    if (args.minScore !== undefined) {
      products = products.filter((p) => (p.trendScore ?? 0) >= args.minScore!);
    }

    products.sort((a, b) => (b.trendScore ?? 0) - (a.trendScore ?? 0));

    return products.slice(0, args.limit ?? 50);
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
    source: v.string(),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("products")
      .withIndex("by_asin", (q) => q.eq("asin", args.asin))
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        title: args.title,
        category: args.category,
        currentPrice: args.price,
        rating: args.rating,
        reviewCount: args.reviewCount,
        bestsellerRank: args.bestsellerRank,
        trendScore: args.trendScore,
        imageUrl: args.imageUrl,
        source: args.source,
      });
      return existing._id;
    } else {
      return await ctx.db.insert("products", {
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
      });
    }
  },
});

export const remove = mutation({
  args: { id: v.id("products") },
  handler: async (ctx, args) => {
    await ctx.db.delete(args.id);
  },
});
