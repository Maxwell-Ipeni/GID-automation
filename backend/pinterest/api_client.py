"""
Pinterest API Client
Handles all Pinterest API interactions including creating pins and fetching boards.
"""

import httpx
import logging
from typing import Optional, Dict, List, Any
from utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class PinterestApiError(Exception):
    """Custom exception for Pinterest API errors."""
    def __init__(self, message: str, status_code: Optional[int] = None):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class PinterestApiClient:
    """Client for interacting with Pinterest API v5."""
    
    BASE_URL = "https://api.pinterest.com/v5"
    
    def __init__(
        self,
        access_token: Optional[str] = None,
        app_id: Optional[str] = None,
        app_secret: Optional[str] = None
    ):
        self.access_token = access_token or settings.PINTEREST_ACCESS_TOKEN
        self.app_id = app_id or settings.PINTEREST_APP_ID
        self.app_secret = app_secret or settings.PINTEREST_APP_SECRET
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-load HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise errors appropriately."""
        if response.status_code >= 400:
            error_msg = f"Pinterest API error: {response.status_code}"
            try:
                error_data = response.json()
                if "message" in error_data:
                    error_msg = error_data["message"]
                elif "error" in error_data:
                    error_msg = error_data["error"]
            except Exception:
                pass
            raise PinterestApiError(error_msg, response.status_code)
        return response.json() if response.text else {}
    
    async def test_connection(self) -> bool:
        """
        Test if the API credentials are valid by attempting to list boards.
        Returns True if successful, raises PinterestApiError if failed.
        """
        try:
            boards = await self.get_boards()
            return len(boards) >= 0
        except Exception as e:
            logger.error(f"Pinterest connection test failed: {e}")
            raise
    
    async def get_boards(self) -> List[Dict[str, Any]]:
        """
        Get list of user's boards.
        
        Returns:
            List of board dicts with keys: id, name, description, url, etc.
        """
        try:
            response = await self.client.get(f"{self.BASE_URL}/boards")
            data = self._handle_response(response)
            return data.get("items", [])
        except PinterestApiError:
            raise
        except Exception as e:
            logger.error(f"Failed to get boards: {e}")
            raise PinterestApiError(f"Failed to get boards: {str(e)}")
    
    async def get_board_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find a board by name.
        
        Returns:
            Board dict if found, None if not found.
        """
        boards = await self.get_boards()
        name_lower = name.lower().strip()
        for board in boards:
            if board.get("name", "").lower().strip() == name_lower:
                return board
        return None
    
    async def get_board_id_by_name(self, name: str) -> Optional[str]:
        """
        Find a board ID by name.
        
        Returns:
            Board ID string if found, None if not found.
        """
        board = await self.get_board_by_name(name)
        return board.get("id") if board else None
    
    async def create_pin(
        self,
        board_id: str,
        title: str,
        description: str,
        link: str,
        image_url: str,
        scheduled_at: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a pin on Pinterest using image_url (Pinterest fetches the image).
        
        Args:
            board_id: Pinterest board ID
            title: Pin title (max 100 chars)
            description: Pin description (max 500 chars)
            link: Affiliate link URL in the link field
            image_url: URL of the product image (Pinterest will fetch it)
            scheduled_at: Optional Unix timestamp for scheduling
        
        Returns:
            Dict with pin data including "id" and "url"
        """
        # Truncate to Pinterest limits
        title = title[:100] if len(title) > 100 else title
        description = description[:500] if len(description) > 500 else description
        
        payload = {
            "board_id": str(board_id),
            "title": title,
            "description": description,
            "link": link,
            "media": {
                "source_type": "image_url",
                "url": image_url,
            },
        }
        
        if scheduled_at:
            payload["scheduled_at"] = str(scheduled_at)
        
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/pins",
                json=payload,
            )
            data = self._handle_response(response)
            logger.info(f"Created Pinterest pin: {data.get('id')}")
            return data
        except PinterestApiError:
            raise
        except Exception as e:
            logger.error(f"Failed to create pin: {e}")
            raise PinterestApiError(f"Failed to create pin: {str(e)}")
    
    async def get_trending_keywords(
        self,
        region: str = "US",
        date_range: str = "today",
    ) -> List[Dict[str, Any]]:
        """
        Get trending keywords from Pinterest Trends API.

        Args:
            region: Geographic region (e.g. "US", "GB", "CA")
            date_range: "today" or "week"

        Returns:
            List of dicts with keys: keyword, rank, etc.
        """
        try:
            params = {"region": region, "date_range": date_range}
            response = await self.client.get(
                f"{self.BASE_URL}/trends/keywords",
                params=params,
            )
            data = self._handle_response(response)
            return data.get("items", [])
        except PinterestApiError:
            raise
        except Exception as e:
            logger.error(f"Failed to get trending keywords: {e}")
            raise PinterestApiError(f"Failed to get trending keywords: {str(e)}")

    async def search_pins(
        self,
        query: str,
        limit: int = 25,
    ) -> List[Dict[str, Any]]:
        """
        Search pins by keyword. Returns pins sorted by relevance.

        Args:
            query: Search keyword
            limit: Max pins to return (max 50)

        Returns:
            List of pin dicts with keys: id, title, link, media, etc.
        """
        try:
            params = {"query": query, "limit": min(limit, 50)}
            response = await self.client.get(
                f"{self.BASE_URL}/pins/search",
                params=params,
            )
            data = self._handle_response(response)
            return data.get("items", [])
        except PinterestApiError:
            raise
        except Exception as e:
            logger.error(f"Failed to search pins: {e}")
            raise PinterestApiError(f"Failed to search pins: {str(e)}")

    async def create_pin_simple(
        self,
        board_id: str,
        title: str,
        description: str,
        affiliate_url: str,
        product_image_url: str,
        category: Optional[str] = None,
        rating: Optional[float] = None,
        price: Optional[float] = None,
        review_count: Optional[int] = None,
        scheduled_at: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a pin with auto-generated content optimized for affiliate marketing.
        
        This is a convenience method that handles content generation internally.
        """
        from pinterest.content_generator import generate_pin_content
        
        content = generate_pin_content(
            title=title,
            affiliate_url=affiliate_url,
            product_image_url=product_image_url,
            category=category,
            rating=rating,
            price=price,
            review_count=review_count,
        )
        
        return await self.create_pin(
            board_id=board_id,
            title=content["title"],
            description=content["description"],
            link=content["link"],
            image_url=product_image_url,
            scheduled_at=scheduled_at,
        )
    
    async def create_board(self, name: str, description: str = "") -> Dict[str, Any]:
        """Create a new Pinterest board.

        Args:
            name: Board name (max 100 chars)
            description: Board description

        Returns:
            Board data dict with 'id' key
        """
        try:
            response = await self.client.post(f"{self.BASE_URL}/boards", json={
                "name": name[:100],
                "description": description[:500],
            })
            data = self._handle_response(response)
            logger.info(f"Created Pinterest board: {data.get('id')} — {name}")
            return data
        except PinterestApiError:
            raise
        except Exception as e:
            logger.error(f"Failed to create board '{name}': {e}")
            raise PinterestApiError(f"Failed to create board: {str(e)}")

    async def get_pin(self, pin_id: str) -> Dict[str, Any]:
        """
        Get details of a specific pin.
        
        Returns:
            Pin data dict
        """
        try:
            response = await self.client.get(f"{self.BASE_URL}/pins/{pin_id}")
            return self._handle_response(response)
        except PinterestApiError:
            raise
        except Exception as e:
            logger.error(f"Failed to get pin {pin_id}: {e}")
            raise PinterestApiError(f"Failed to get pin: {str(e)}")
    
    async def delete_pin(self, pin_id: str) -> bool:
        """
        Delete a pin.
        
        Returns:
            True if successful
        """
        try:
            response = await self.client.delete(f"{self.BASE_URL}/pins/{pin_id}")
            return response.status_code == 204
        except PinterestApiError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete pin {pin_id}: {e}")
            raise PinterestApiError(f"Failed to delete pin: {str(e)}")
    
    def is_configured(self) -> bool:
        """Check if all required credentials are configured."""
        return bool(
            self.access_token 
            and self.access_token != "your_pinterest_access_token"
            and self.access_token != ""
            and settings.PINTEREST_BOARD_ID
            and settings.PINTEREST_BOARD_ID != "your_pinterest_board_id"
            and settings.PINTEREST_BOARD_ID != ""
        )
    
    @property
    def board_id(self) -> str:
        """Get configured board ID."""
        return settings.PINTEREST_BOARD_ID