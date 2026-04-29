from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class BuyerProfile(BaseModel):
    # "first_car" | "upgrade" | "family" | "commuter"
    use_case: Optional[str] = None
    city: Optional[str] = None
    budget_ceiling: Optional[int] = None    # hard max in rupees
    budget_soft: Optional[int] = None       # inferred preference
    # ["petrol"] | ["petrol","diesel"] | etc.
    fuel_pref: list[str] = []
    risk_tolerance: Optional[str] = None    # "low" | "mid" | "high"
    priority_weights: dict = Field(
        default={"resale": 0.33, "reliability": 0.33, "features": 0.34}
    )

    @property
    def intake_complete(self) -> bool:
        return all([
            self.use_case, self.city,
            self.budget_ceiling, self.fuel_pref,
            self.risk_tolerance
        ])


class ShortlistItem(BaseModel):
    car_id: str
    rank: int
    score: float
    reasoning: str                          # LLM-generated personalised reason


class ConversationSignal(BaseModel):
    # "viewed" | "emi_checked" | "budget_reduced" | "rejected"
    type: str
    car_id: Optional[str] = None
    metadata: dict = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SessionContext(BaseModel):
    session_id: str
    stage: Literal["intake", "retrieval", "explore", "converting"] = "intake"
    profile: BuyerProfile = Field(default_factory=BuyerProfile)
    shortlist: list[ShortlistItem] = []
    shortlist_valid_until: Optional[datetime] = None
    signals: list[ConversationSignal] = []
    pending_test_drives: list[str] = []
    loan_prequalified: bool = False
    token_paid: bool = False
    last_message_at: Optional[datetime] = None
