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
  },
  handler: async (ctx, args) => {
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
    const all = await ctx.db.query("pinterestPosts").collect();
    return {
      total: all.length,
      queued: all.filter((p) => p.status === "queued").length,
      published: all.filter((p) => p.status === "published").length,
      failed: all.filter((p) => p.status === "failed").length,
    };
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
