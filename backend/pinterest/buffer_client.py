"""
Buffer API Client
Fallback publisher using Buffer.com's API for social media scheduling.
"""

import logging
from typing import Dict, Optional
from utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

BUFFER_API_URL = "https://api.buffer.com"

CREATE_POST_MUTATION = """
mutation CreatePost($input: CreatePostInput!) {
  createPost(input: $input) {
    ... on PostActionSuccess {
      post {
        id
        text
        dueAt
      }
    }
    ... on MutationError {
      message
    }
  }
}
"""


class BufferApiError(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class BufferClient:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.BUFFER_API_KEY
        self._client = None

    @property
    def client(self):
        if self._client is None:
            import httpx
            self._client = httpx.AsyncClient(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    async def test_connection(self) -> Dict:
        """Test Buffer API connection by fetching account info."""
        query = """
        query {
          account {
            id
            email
          }
        }
        """
        try:
            response = await self.client.post(
                BUFFER_API_URL,
                json={"query": query},
            )
            data = response.json()

            if response.status_code >= 400:
                return {
                    "success": False,
                    "message": f"Buffer API error: {response.status_code}",
                }

            account = data.get("data", {}).get("account")
            if account:
                return {
                    "success": True,
                    "message": f"Connected! Account: {account.get('email', 'unknown')}",
                    "account": account,
                }

            errors = data.get("errors", [])
            msg = errors[0].get("message", "Unknown error") if errors else "Invalid response"
            return {"success": False, "message": msg}

        except Exception as e:
            return {"success": False, "message": str(e)}

    def has_pinterest_channel(self) -> bool:
        return bool(
            settings.BUFFER_PINTEREST_CHANNEL_ID
            and settings.BUFFER_PINTEREST_CHANNEL_ID not in ("", "your_buffer_channel_id")
        )

    def has_twitter_channel(self) -> bool:
        return bool(
            settings.BUFFER_TWITTER_CHANNEL_ID
            and settings.BUFFER_TWITTER_CHANNEL_ID not in ("", "your_buffer_twitter_channel_id")
        )

    def is_configured(self) -> bool:
        return bool(
            self.api_key
            and self.api_key not in ("", "your_buffer_api_key")
            and (self.has_pinterest_channel() or self.has_twitter_channel())
        )

    @staticmethod
    def _truncate_for_twitter(text: str, link: Optional[str] = None) -> str:
        """Truncate text to fit Twitter's character limit, preserving the link."""
        max_chars = settings.TWITTER_MAX_CHARS
        if link:
            link_part = f"\n\n{link}"
            available = max_chars - len(link_part)
            if len(text) > available:
                text = text[: available - 1] + "…"
            return f"{text}{link_part}"
        return text[:max_chars]

    async def create_pin(
        self,
        channel_id: str,
        text: str,
        image_url: str,
        link: Optional[str] = None,
        is_twitter: bool = False,
    ) -> str:
        """
        Create a post via Buffer's API for a specific channel.

        Args:
            channel_id: Buffer channel ID
            text: Post content
            image_url: Public URL of the image
            link: Optional destination URL
            is_twitter: If True, truncates text to Twitter's character limit

        Returns:
            Buffer post ID

        Raises:
            BufferApiError on failure
        """
        body = text
        if is_twitter:
            body = self._truncate_for_twitter(text, link)
            link = None
        elif link:
            body = f"{text}\n\n{link}"
        variables = {
            "input": {
                "text": body,
                "channelId": channel_id,
                "schedulingType": "automatic",
                "mode": "shareNow",
                "assets": [
                    {
                        "image": {
                            "url": image_url,
                        }
                    }
                ],
            }
        }

        try:
            response = await self.client.post(
                BUFFER_API_URL,
                json={
                    "query": CREATE_POST_MUTATION,
                    "variables": variables,
                },
            )
            data = response.json()

            if response.status_code >= 400:
                error_msg = f"Buffer API error: {response.status_code}"
                try:
                    err = data.get("errors", [{}])[0]
                    error_msg = err.get("message", error_msg)
                except (IndexError, KeyError, TypeError):
                    pass
                raise BufferApiError(error_msg)

            result = data.get("data", {}).get("createPost")

            if result is None:
                errors = data.get("errors", [])
                msg = errors[0].get("message", "Unknown GraphQL error") if errors else "No response data"
                raise BufferApiError(msg)

            if "message" in result:
                raise BufferApiError(result["message"])

            post = result.get("post", {})
            post_id = post.get("id")
            if not post_id:
                raise BufferApiError("No post ID returned from Buffer")

            logger.info(f"Created Buffer post: {post_id}")
            return post_id

        except BufferApiError:
            raise
        except Exception as e:
            raise BufferApiError(f"Failed to create Buffer post: {str(e)}")
