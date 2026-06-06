import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

export default defineSchema({
  products: defineTable({
    asin: v.string(),
    title: v.string(),
    category: v.optional(v.string()),
    currentPrice: v.optional(v.number()),
    originalPrice: v.optional(v.number()),
    rating: v.optional(v.number()),
    reviewCount: v.optional(v.number()),
    bestsellerRank: v.optional(v.number()),
    trendScore: v.optional(v.number()),
    discountPercentage: v.optional(v.number()),
    imageUrl: v.optional(v.string()),
    productUrl: v.string(),
    source: v.string(),
    affiliateUrl: v.optional(v.string()),
  })
    .index("by_asin", ["asin"])
    .index("by_trend_score", ["trendScore"])
    .index("by_source", ["source"])
    .index("by_category", ["category"]),

  affiliateLinks: defineTable({
    productId: v.id("products"),
    asin: v.string(),
    affiliateUrl: v.string(),
    shortUrl: v.optional(v.string()),
    clicks: v.number(),
    createdAt: v.number(),
  })
    .index("by_product", ["productId"])
    .index("by_asin", ["asin"]),

  pinterestPosts: defineTable({
    productId: v.id("products"),
    asin: v.string(),
    imageUrl: v.string(),
    generatedImageUrl: v.optional(v.string()),
    pinTitle: v.string(),
    pinDescription: v.string(),
    hashtags: v.optional(v.array(v.string())),
    affiliateUrl: v.string(),
    status: v.union(
      v.literal("queued"),
      v.literal("processing"),
      v.literal("published"),
      v.literal("failed"),
    ),
    scheduledAt: v.optional(v.number()),
    publishedAt: v.optional(v.number()),
    pinId: v.optional(v.string()),
    errorMessage: v.optional(v.string()),
    boardId: v.optional(v.string()),
    boardName: v.optional(v.string()),
  })
    .index("by_status", ["status"])
    .index("by_product", ["productId"])
    .index("by_product_status", ["productId", "status"])
    .index("by_scheduled", ["scheduledAt"])
    .index("by_board", ["boardId"]),

  scrapingLogs: defineTable({
    source: v.string(),
    status: v.union(
      v.literal("running"),
      v.literal("completed"),
      v.literal("failed"),
    ),
    productsFound: v.number(),
    errors: v.optional(v.array(v.string())),
    startedAt: v.number(),
    completedAt: v.optional(v.number()),
  })
    .index("by_source", ["source"])
    .index("by_status", ["status"])
    .index("by_started", ["startedAt"]),

  pinterestBoards: defineTable({
    name: v.string(),
    description: v.optional(v.string()),
    pinterestId: v.optional(v.string()),
    createdAt: v.number(),
  })
    .index("by_name", ["name"]),

  settings: defineTable({
    key: v.string(),
    value: v.any(),
  })
    .index("by_key", ["key"]),
});
