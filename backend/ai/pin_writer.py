import logging
import random
import json
import re
from typing import Optional
from openai import OpenAI
from utils.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

SYSTEM_PROMPT = """You are a Pinterest content writer specializing in Amazon affiliate product descriptions. Write natural, conversational pin descriptions that drive clicks and saves.

GENERAL STRUCTURE:
1. Hook — attention-grabbing opening
2. Main benefit — what makes this product worthwhile
3. Key features or use case — specific, practical details
4. Target audience — who this is for
5. Call-to-action — save, shop, discover, click
6. Relevant hashtags — 3 to 8 only

RULES:
- Write naturally and conversationally, like a helpful friend sharing a find
- Focus on benefits before features
- Use Pinterest SEO keywords naturally — no keyword stuffing
- Keep descriptions between 150–300 characters
- End with a save, shop, discover, or click CTA
- Include 3–8 relevant hashtags
- Use emojis naturally where they fit (✨🔥📌🛒💡👀 etc.)
- Never use first person ("I", "me", "my") — use imperative or third person

CATEGORY FOCUS:

HOME DECOR:
Style, comfort, aesthetic appeal, space transformation

FASHION:
Style, outfit inspiration, seasonality, comfort and fit, trending looks

BEAUTY:
Results, skin or hair benefits, confidence, ease of use

KITCHEN:
Time-saving, organization, convenience, cooking efficiency

FITNESS / SPORTS:
Performance, health goals, motivation, ease of workouts

TECH / ELECTRONICS:
Productivity, innovation, convenience, problem-solving

TRAVEL / OUTDOORS:
Comfort, portability, organization, travel convenience

PARENTING / BABY:
Safety, convenience, time-saving, child comfort

PETS:
Pet happiness, safety, durability, ease of use

AMAZON AFFILIATE PRODUCTS (general):
Why people love it, everyday problems it solves, value for money, popularity, practical use cases

BANNED PHRASES — never use:
"Say goodbye to", "Level up your", "Game changer", "Game-changer",
"Unlock", "won't be the same", "Ditch the", "Tired of",
"Upgrade your", "Elevate your", "Transform your", "Revolutionize your",
"to the next level", "Must-have", "A must-have",
"I took a closer look at", "What stood out to me was", "The first thing I noticed was"

DESCRIPTION FORMULA:
[HOOK]
[MAIN BENEFIT]
[WHO IT IS FOR]
[CALL TO ACTION]

Then on a new line, the hashtags (3-8 only).

Return ONLY valid JSON:
{"description": "...", "hashtags": ["#tag1", "#tag2", ...]}"""

VISION_ANALYSIS_PROMPT = """Look at this product image and extract what's actually useful for writing a Pinterest description. Ignore the photo background and packaging unless they show the product in use. Focus on what matters for a buyer.

Return JSON:
{
  "product_type": "what specific type of product this is (e.g. 'wireless earbuds', 'push-up bra', 'meat thermometer')",
  "use_case": "what the product is used for (e.g. 'listening to music and calls', 'everyday bra for comfort and support', 'checking meat temperature while cooking')",
  "target_user": "who would buy this (e.g. 'commuters, travelers, audio fans', 'women wanting wireless full-coverage support', 'home cooks and grill enthusiasts')",
  "key_features": ["only features visible or clearly implied by the design — no speculation"],
  "photo_style": "one word: 'lifestyle' (shows product in use by people) or 'product' (product-only or white background)"
}

Be concise. If the photo is a white-background product shot, note that so the writer doesn't describe the photo itself."""

CATEGORY_FOCUS = {
    "home": "Style, comfort, aesthetic appeal, space transformation",
    "kitchen": "Time-saving, organization, convenience, cooking efficiency",
    "electronics": "Productivity, innovation, convenience, problem-solving",
    "tech": "Productivity, innovation, convenience, problem-solving",
    "fashion": "Style, outfit inspiration, seasonality, comfort and fit, trending looks",
    "beauty": "Results, skin or hair benefits, confidence, ease of use",
    "sports": "Performance, health goals, motivation, ease of workouts",
    "fitness": "Performance, health goals, motivation, ease of workouts",
    "outdoors": "Comfort, portability, organization, travel convenience",
    "travel": "Comfort, portability, organization, travel convenience",
    "tools": "Practicality, durability, getting the job done right",
    "automotive": "Practicality, durability, vehicle care and upgrades",
    "toys": "Fun, engagement, learning, gift potential",
    "baby": "Safety, convenience, time-saving, child comfort",
    "pet": "Pet happiness, safety, durability, ease of use",
    "books": "Discovery, learning, inspiration, entertainment",
    "office": "Productivity, comfort, organization, workspace",
    "music": "Sound quality, experience, immersion, enjoyment",
    "food": "Taste, convenience, quality, enjoyment",
    "default": "Why people love it, everyday problems it solves, value for money, popularity, practical use cases",
}

FALLBACK_TEMPLATES = {
    "home": "✨ Transform your home with this stylish addition!",
    "kitchen": "🔪 Make cooking easier with this handy kitchen essential!",
    "electronics": "💡 Smart design that makes daily life more convenient.",
    "tech": "💡 Smart design that makes daily life more convenient.",
    "fashion": "👗 Add a versatile piece to your wardrobe that works for any occasion.",
    "beauty": "✨ A simple addition to your routine with real results.",
    "sports": "💪 Gear up and perform at your best with the right equipment.",
    "fitness": "💪 Gear up and perform at your best with the right equipment.",
    "outdoors": "🌲 Built for wherever your adventures take you.",
    "tools": "🔧 Reliable and ready for the job — no fuss, just results.",
    "automotive": "🚗 A practical upgrade every driver will appreciate.",
    "toys": "🎮 Hours of fun and engagement — the gift that keeps giving.",
    "baby": "👶 Parenting made a little easier with thoughtful design.",
    "pet": "🐾 Your furry friend deserves the best — treat them right.",
    "default": "🔥 A popular find that solves everyday problems effortlessly.",
}

BANNED_PHRASES = [
    "say goodbye to", "level up your", "game changer", "game-changer",
    "unlock", "won't be the same", "ditch the", "tired of",
    "upgrade your", "elevate your", "transform your", "revolutionize your",
    "to the next level", "must-have", "a must-have", "must have", "a must have",
    "i took a closer look at", "what stood out to me was",
    "the first thing i noticed was", "check out this amazing",
    "you won't believe", "you need this",
]


class PinContentAI:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.NVIDIA_API_KEY,
            base_url=settings.NVIDIA_API_BASE,
        )
        self.model = settings.NVIDIA_MODEL
        self.vision_model = settings.NVIDIA_VISION_MODEL
        self.fallback_model = settings.NVIDIA_FALLBACK_MODEL

    def is_configured(self) -> bool:
        return bool(settings.NVIDIA_API_KEY)

    def _contains_banned_phrases(self, text: str) -> bool:
        lower = text.lower()
        return any(phrase in lower for phrase in BANNED_PHRASES)

    def _analyze_image(self, image_url: str) -> Optional[dict]:
        if not image_url:
            return None
        try:
            response = self.client.chat.completions.create(
                model=self.vision_model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": VISION_ANALYSIS_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {"url": image_url},
                            },
                        ],
                    }
                ],
                temperature=0.3,
                max_tokens=500,
            )
            raw = response.choices[0].message.content
            if not raw:
                return None
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                required = ["product_type", "use_case", "target_user", "key_features", "photo_style"]
                if all(k in result for k in required):
                    logger.info(f"Vision analysis: {result.get('product_type', 'unknown')}")
                    return result
            logger.warning(f"Incomplete vision response: {raw[:200]}")
            return None
        except Exception as e:
            logger.warning(f"Vision analysis failed: {e}")
            return None

    def _get_category_focus(self, category: str) -> str:
        for key, focus in CATEGORY_FOCUS.items():
            if key in (category or "").lower():
                return focus
        return CATEGORY_FOCUS["default"]

    def _build_prompt(self, product: dict, vision: Optional[dict] = None) -> str:
        title = product.get("title", "")
        category = (product.get("category") or "general").lower()
        cat_focus = self._get_category_focus(category)

        lines = [f"Product: {title}"]
        lines.append(f"Category focus: {cat_focus}")

        if vision:
            lines.append("")
            lines.append("Product info from image:")
            lines.append(f"- Type: {vision.get('product_type', 'N/A')}")
            lines.append(f"- Use case: {vision.get('use_case', 'N/A')}")
            lines.append(f"- For: {vision.get('target_user', 'N/A')}")
            features = vision.get("key_features", [])
            if features:
                lines.append(f"- Key features: {', '.join(features)}")
            photo_style = vision.get("photo_style", "")
            if photo_style == "product":
                lines.append("(Photo is a product-only shot — focus on the product title and category for content.)")
        else:
            lines.append("")
            lines.append("(Write based on the product title and category.)")

        lines.append("")
        lines.append("Write a pin description and 3-8 hashtags following the system instructions.")
        return "\n".join(lines)

    def _call_llm(self, model: str, messages: list, temperature: float = 0.8) -> Optional[dict]:
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=500,
            )
            raw = response.choices[0].message.content
            if not raw:
                raise ValueError("Empty response from LLM")
            json_match = re.search(r'\{.*\}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON found in response")
            result = json.loads(json_match.group())
            desc = result.get("description")
            tags = result.get("hashtags")
            if not desc or not tags:
                raise ValueError("Missing required fields in response")
            return {"description": desc, "hashtags": tags}
        except Exception as e:
            logger.warning(f"LLM call failed on {model}: {e}")
            return None

    def generate_content(self, product: dict) -> dict:
        title = product.get("title", "")
        if not self.is_configured():
            logger.warning("NVIDIA AI not configured, using fallback")
            return self._fallback_content(product)

        image_url = product.get("image_url", "")
        vision = self._analyze_image(image_url)

        user_prompt = self._build_prompt(product, vision)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        result = self._call_llm(self.model, messages)

        if result is None:
            logger.warning("Primary model failed, trying fallback model")
            result = self._call_llm(self.fallback_model, messages, temperature=0.9)

        if result:
            desc = result.get("description", "")
            if self._contains_banned_phrases(desc):
                logger.warning("Banned phrases detected, regenerating")
                messages[1]["content"] = user_prompt + "\n\nIMPORTANT: Review the banned phrases list carefully and avoid every single one."
                redo = self._call_llm(self.model, messages, temperature=0.9)
                if redo:
                    result = redo

            return {
                "title": title,
                "description": result.get("description") or "",
                "hashtags": result.get("hashtags") or [],
            }

        logger.error("All AI models failed, using fallback template")
        return self._fallback_content(product)

    def _fallback_content(self, product: dict) -> dict:
        title = product.get("title", "")
        category = (product.get("category", "") or "").lower()

        hook = FALLBACK_TEMPLATES.get("default")
        for key, text in FALLBACK_TEMPLATES.items():
            if key in category:
                hook = text
                break

        cat_slug = category.replace(" ", "").replace("/", "") if category else "products"
        tags = ["#affiliate", "#amazonfinds", f"#{cat_slug}"]
        extras = {
            "home": ["#homedecor", "#homeideas"],
            "kitchen": ["#kitchengadgets", "#cooking"],
            "fashion": ["#fashion", "#style"],
            "beauty": ["#beauty", "#selfcare"],
            "electronics": ["#tech", "#gadgets"],
            "tech": ["#tech", "#gadgets"],
            "sports": ["#fitness", "#sports"],
            "outdoors": ["#outdoors", "#adventure"],
            "tools": ["#tools", "#diy"],
            "pet": ["#pets", "#doglife"],
        }
        for key, extra in extras.items():
            if key in category:
                tags.extend(extra)
                break
        tags.extend(["#shopnow", "#deals"])

        return {
            "title": title,
            "description": f"{hook} Check the link to learn more! 🛒",
            "hashtags": tags[:8],
        }
