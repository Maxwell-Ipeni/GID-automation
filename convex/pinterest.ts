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
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
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
    pinTitle: v.string(),
    pinDescription: v.string(),
    affiliateUrl: v.string(),
    scheduledAt: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("pinterestPosts", {
      ...args,
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

export const getStats = query({
  handler: async (ctx) => {
    const all = await ctx.db.query("pinterestPosts").collect();
    return {
      total: all.length,
      queued: all.filter((p) => p.status === "queued").length,
      published: all.filter((p) => p.status === "published").length,
      failed: all.filter((p) => p.status === "failed").length,
    };
  },
});
