"""
Pin Design Reference
Extracted from user's sample pins in /home/mg/Downloads/pinterest/
Reference for generating high-quality, traffic-driving Pinterest pins.

=== LAYOUT (from 5 sample pins at 736x1104, 2:3 ratio) ===
- Product image: 75-91% of pin height (typically 82%)
- Text area: 9-25% of pin height (dense)
- No rounded corners on product image
- No drop shadows on product image
- Clean, modern, minimal styling

=== COLOR PALETTES ===

WARM / LIFESTYLE (home, kitchen, food, baby, closet, bathroom, bedroom)
- Background gradient: #f5f0eb (top light beige) → #e7ddd4 (bottom)
- Text color: #453d35 (dark brown, high readability)
- Accent: #b09783 (warm taupe)
- Badge: pink/rose tone #f0d0d0
- 61% light, 30% mid, 2% dark
- Average luminance: 197 (bright overall)
- Average saturation: 0.22 (desaturated, earthy)

DARK / BOLD (sports, boxing, energetic)
- Background: near-black #0e0c0d
- Text color: white/light gray
- Accent: brick red #9b493a or deep red #9a1c1b
- Light gray badge #d0d0d0 top-left
- 29% light, 25% mid, 55% dark
- Average luminance: 109 (dark overall)
- High contrast (88.5 vs 53-65 for warm pins)

ELEGANT (fashion, beauty)
- Soft warm tones: #f0e8e0 gradient
- Dark text on light bg
- Rose/gold accents

MINIMAL (tech, electronics, office)
- Clean white/light gray
- Thin accent line
- Dark text on light bg

=== TEXT LAYOUT ===
- Text region: bottom 9-25% of pin (180-375px on a 1500px pin)
- 5-6 horizontal bands of text within the text region
- Dense text: 83-85% of text area has text pixels
- Title is benefit-focused with emojis
- 14-59 emoji-like clusters per image (star ratings, checkmarks, sparkles)
- "Amazon Finds" branding in bottom-right corner badge

=== SAMPLE TITLES (from filenames) ===
1. "Closet Space Saver That Instantly Organizes Your Wardrobe ✨"
2. "Home Boxing Setup That Makes Workouts Fun 🥊✨"
3. "Small Bedroom Glow-Up on a Budget ✨ Amazon Finds"
4. "Rustproof Shower Caddy Set for a Clean & Organized Bathroom"
5. "Auplf Motion Sensor LED Light Strip 19_68ft Under Bed Lights..."

Pattern: Benefit + Product + Context + Emoji(s)

=== DESIGN RULES ===
1. No rounded corners on product images
2. No drop shadows
3. Product fills 78-85% of pin height (1170-1275px on 1500px pin)
4. Text area is 15-22% dense bottom strip (225-330px)
5. Background: warm desaturated beige for lifestyle, dark for bold
6. Bottom-right "Amazon Finds" badge (60x60px)
7. Dark text on light backgrounds (warm templates)
8. Light text on dark backgrounds (bold templates)
9. High contrast for readability
10. Emojis in titles for visual appeal
"""

# Load this module to print the reference
if __name__ == "__main__":
    print(__doc__)
