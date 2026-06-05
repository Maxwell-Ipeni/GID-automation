"""
Product Scoring Engine
Ranks products based on various factors like trending velocity, sales rank, etc.
Uses weighted scoring formula to determine which products to prioritize for Pinterest.
"""

from typing import List, Dict
from scraping.amazon_scraper import AmazonProduct
import math

class ProductScorer:
    WEIGHT_BESTSELLER_RANK = 0.35
    WEIGHT_DISCOUNT = 0.25
    WEIGHT_RATING = 0.20
    WEIGHT_REVIEWS = 0.20
    
    MAX_REVIEW_COUNT = 50000
    MAX_RANK = 100

    def __init__(self):
        pass
    
    def rank_products(self, products: List[AmazonProduct]) -> List[AmazonProduct]:
        """
        Rank products by trend score and return sorted list (highest first).
        Updates each product's trend_score attribute.
        """
        for product in products:
            product.trend_score = self.calculate_trend_score_from_product(product)
        
        return sorted(products, key=lambda p: p.trend_score or 0, reverse=True)
    
    def calculate_trend_score_from_product(self, product: AmazonProduct) -> float:
        """
        Calculate trend score for an AmazonProduct.
        """
        score = 0.0
        
        rank_score = self._calculate_rank_score(product.bestseller_rank)
        score += rank_score * self.WEIGHT_BESTSELLER_RANK
        
        discount_score = self._calculate_discount_score(product.price, product.bestseller_rank)
        score += discount_score * self.WEIGHT_DISCOUNT
        
        rating_score = self._calculate_rating_score(product.rating)
        score += rating_score * self.WEIGHT_RATING
        
        review_score = self._calculate_review_score(product.review_count)
        score += review_score * self.WEIGHT_REVIEWS
        
        return round(score, 4)
    
    def _calculate_rank_score(self, rank: int | None) -> float:
        """
        Calculate rank score (0-100).
        Rank 1 = 100, Rank 100 = 0.
        Lower rank numbers are better.
        """
        if rank is None or rank <= 0:
            return 0.0
        
        if rank > self.MAX_RANK:
            rank = self.MAX_RANK
        
        return float(100 - ((rank - 1) / (self.MAX_RANK - 1)) * 100)
    
    def _calculate_discount_score(self, price: float | None, rank: int | None) -> float:
        """
        Calculate discount score based on price and rank.
        Products with lower ranks that also have discounts score higher.
        """
        if price is None or price <= 0:
            return 0.0
        
        if rank is not None and rank <= 10:
            return min(100.0, 50.0 + (50.0 * (1 - rank / 10)))
        
        return 25.0
    
    def _calculate_rating_score(self, rating: float | None) -> float:
        """
        Calculate rating score (0-100).
        Rating out of 5 stars.
        """
        if rating is None:
            return 0.0
        
        return (rating / 5.0) * 100
    
    def _calculate_review_score(self, review_count: int | None) -> float:
        """
        Calculate review score (0-100) using logarithmic scale.
        More reviews = more social proof = higher score.
        """
        if review_count is None or review_count <= 0:
            return 0.0
        
        if review_count >= self.MAX_REVIEW_COUNT:
            return 100.0
        
        return (math.log10(review_count + 1) / math.log10(self.MAX_REVIEW_COUNT + 1)) * 100
    
    def calculate_trend_score(self, product_data: Dict) -> float:
        """
        Calculate a trend score for a product from raw data dict.
        Used for updating scores in database.
        """
        rank = product_data.get("bestsellerRank") or product_data.get("bestseller_rank")
        rating = product_data.get("rating")
        review_count = product_data.get("reviewCount") or product_data.get("review_count")
        price = product_data.get("currentPrice") or product_data.get("price")
        
        score = 0.0
        
        rank_score = self._calculate_rank_score(rank)
        score += rank_score * self.WEIGHT_BESTSELLER_RANK
        
        discount_score = self._calculate_discount_score(price, rank)
        score += discount_score * self.WEIGHT_DISCOUNT
        
        rating_score = self._calculate_rating_score(rating)
        score += rating_score * self.WEIGHT_RATING
        
        review_score = self._calculate_review_score(review_count)
        score += review_score * self.WEIGHT_REVIEWS
        
        return round(score, 4)
    
    def get_top_products(self, products: List[AmazonProduct], limit: int = 20) -> List[AmazonProduct]:
        """
        Get top N products by trend score.
        """
        ranked = self.rank_products(products)
        return ranked[:limit]