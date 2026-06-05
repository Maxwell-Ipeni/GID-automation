import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const logStart = mutation({
  args: {
    source: v.string(),
    startedAt: v.number(),
  },
  handler: async (ctx, args) => {
    return await ctx.db.insert("scrapingLogs", {
      source: args.source,
      status: "running",
      productsFound: 0,
      startedAt: args.startedAt,
    });
  },
});

export const logComplete = mutation({
  args: {
    logId: v.id("scrapingLogs"),
    productsFound: v.number(),
    completedAt: v.number(),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.logId, {
      status: "completed",
      productsFound: args.productsFound,
      completedAt: args.completedAt,
    });
  },
});

export const logFailed = mutation({
  args: {
    logId: v.id("scrapingLogs"),
    errors: v.array(v.string()),
    completedAt: v.number(),
  },
  handler: async (ctx, args) => {
    await ctx.db.patch(args.logId, {
      status: "failed",
      errors: args.errors,
      completedAt: args.completedAt,
    });
  },
});

export const getRecent = query({
  args: {
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    const logs = await ctx.db
      .query("scrapingLogs")
      .withIndex("by_started")
      .order("desc")
      .take(args.limit ?? 10);
    return logs;
  },
});

export const getBySource = query({
  args: {
    source: v.string(),
    limit: v.optional(v.number()),
  },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("scrapingLogs")
      .withIndex("by_source", (q) => q.eq("source", args.source))
      .order("desc")
      .take(args.limit ?? 10);
  },
});

export const getLastRun = query({
  args: { source: v.string() },
  handler: async (ctx, args) => {
    const logs = await ctx.db
      .query("scrapingLogs")
      .withIndex("by_source", (q) => q.eq("source", args.source))
      .order("desc")
      .first();
    return logs;
  },
});