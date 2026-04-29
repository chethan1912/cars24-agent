import json
import anthropic
from services.inventory_service import InventoryService
from core.models import BuyerProfile, ShortlistItem
from core.config import settings

RANKING_PROMPT = """You are a Cars24 buying assistant. Given a buyer profile and a list of candidate cars, select the top 3 best matches and explain why each one is right for this specific buyer.

Buyer profile:
{profile_json}

Candidate cars:
{cars_json}

Return ONLY a JSON array with exactly 3 objects. No other text. Format:
[
  {{
    "car_id": "...",
    "rank": 1,
    "score": 0.0-1.0,
    "reasoning": "2 sentence personalised reason why this car fits this buyer specifically"
  }},
  ...
]

Rules:
- reasoning must reference specific buyer attributes (use_case, city, risk_tolerance)
- score reflects overall fit, not just price
- do not repeat generic phrases like "popular choice" or "great deal"
"""


class RankingService:
    def __init__(self, inventory_service: InventoryService):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.inventory = inventory_service

    def rank(
        self,
        candidate_ids: list[str],
        profile: BuyerProfile
    ) -> list[ShortlistItem]:
        """
        Takes up to 10 candidate car IDs (already vector-ranked).
        Returns top 3 ShortlistItems with LLM-generated reasoning.
        """
        cars = self.inventory.get_car_details(candidate_ids[:10])
        if not cars:
            return []

        prompt = RANKING_PROMPT.format(
            profile_json=json.dumps(profile.model_dump(), indent=2),
            cars_json=json.dumps(cars, indent=2)
        )

        raw = self.client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        ).content[0].text

        try:
            # Strip any accidental markdown fences
            clean = raw.strip().strip("```json").strip("```").strip()
            ranked = json.loads(clean)
            return [ShortlistItem(**item) for item in ranked[:3]]
        except Exception as e:
            # Fallback: return top 3 from vector ranking without reasoning
            return [
                ShortlistItem(
                    car_id=cars[i]["car_id"],
                    rank=i+1,
                    score=0.7 - (i * 0.1),
                    reasoning="Selected based on your profile."
                )
                for i in range(min(3, len(cars)))
            ]
