import { mutation, query } from "./_generated/server";
import { v } from "convex/values";

export const generateAffiliateLink = mutation({
  args: {
    productId: v.id("products"),
    asin: v.string(),
    affiliateTag: v.string(),
  },
  handler: async (ctx, args) => {
    const affiliateUrl = `https://www.amazon.com/dp/${args.asin}/?tag=${args.affiliateTag}`;

    const existing = await ctx.db
      .query("affiliateLinks")
      .withIndex("by_asin", (q) => q.eq("asin", args.asin))
      .first();

    if (existing) {
      return existing;
    }

    const id = await ctx.db.insert("affiliateLinks", {
      productId: args.productId,
      asin: args.asin,
      affiliateUrl,
      clicks: 0,
      createdAt: Date.now(),
    });

    // Update product with affiliate URL
    const product = await ctx.db.get(args.productId);
    if (product) {
      await ctx.db.patch(args.productId, {
        affiliateUrl,
      });
    }

    return { _id: id, affiliateUrl };
  },
});

export const getByProduct = query({
  args: { productId: v.id("products") },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("affiliateLinks")
      .withIndex("by_product", (q) => q.eq("productId", args.productId))
      .first();
  },
});

export const trackClick = mutation({
  args: { linkId: v.id("affiliateLinks") },
  handler: async (ctx, args) => {
    const link = await ctx.db.get(args.linkId);
    if (link) {
      await ctx.db.patch(args.linkId, { clicks: link.clicks + 1 });
    }
  },
});
