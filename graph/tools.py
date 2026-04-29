from langchain_core.tools import tool
from services.inventory_service import InventoryService
from services.embedding_service import EmbeddingService
from services.emi_service import EMIService
from services.inspection_service import InspectionService
from services.booking_service import BookingService
from services.session_service import SessionService
from services.ranking_service import RankingService
import json

# Tools are functions decorated with @tool.
# They receive structured args and return structured dicts.
# All services are injected — tools are stateless.


def make_tools(
    inventory_svc: InventoryService,
    embedding_svc: EmbeddingService,
    emi_svc: EMIService,
    inspection_svc: InspectionService,
    booking_svc: BookingService,
    session_svc: SessionService,
    ranking_svc: RankingService,
):
    @tool
    def patch_context(session_id: str, patch: dict) -> dict:
        """
        Update fields in the session context.
        Use this when the user reveals new preferences or changes existing ones.
        patch is a dict of field: value pairs.
        Profile-level fields: use_case, city, budget_ceiling, fuel_pref, risk_tolerance.
        Top-level fields: stage, loan_prequalified, token_paid.
        """
        updated = session_svc.patch(session_id, patch)
        return {"status": "patched", "updated_fields": list(patch.keys())}

    @tool
    def sql_filter_inventory(session_id: str, year_min: int = 2017, km_max: int = 100000) -> dict:
        """
        Filter inventory using hard constraints from the session context.
        Returns a list of car_ids that match the buyer's city, budget, and fuel preference.
        Call this when you need to fetch a fresh candidate set.
        """
        context = session_svc.load(session_id)
        car_ids = inventory_svc.filter_inventory(
            context.profile, year_min, km_max)
        return {"candidate_ids": car_ids, "count": len(car_ids)}

    @tool
    def vector_rerank(session_id: str, candidate_ids: list[str], top_k: int = 10) -> dict:
        """
        Semantically re-rank candidate cars against the buyer profile.
        Call this after sql_filter_inventory with the returned candidate_ids.
        Returns top_k car_ids ordered by semantic fit.
        """
        context = session_svc.load(session_id)
        ranked = embedding_svc.rerank(candidate_ids, context.profile, top_k)
        return {"ranked_ids": [r["car_id"] for r in ranked], "scores": ranked}

    @tool
    def get_emi_estimate(car_id: str, price: int, tenure_months: int = 48) -> dict:
        """
        Calculate EMI for a specific car.
        Use this when the user asks about monthly payments or financing.
        price is the on-road price in rupees.
        tenure_months is the loan duration (24, 36, 48, or 60).
        """
        result = emi_svc.calculate(price, tenure_months)
        return result

    @tool
    def fetch_inspection_report(car_id: str) -> dict:
        """
        Fetch the inspection report for a specific car.
        Use this when the user asks about car condition, inspection details, or flags.
        """
        report = inspection_svc.get_report(car_id)
        if not report:
            return {"error": "Car not found"}
        return report

    @tool
    def schedule_test_drive(
        session_id: str,
        car_id: str,
        buyer_address: str,
        time_slot: str
    ) -> dict:
        """
        Book a home test drive for a car.
        Only call this when you have: car_id, buyer_address, and time_slot.
        If any are missing, ask the user first — do not call with placeholder values.
        time_slot: "morning" | "afternoon" | "evening"
        """
        booking = booking_svc.create_test_drive(
            session_id, car_id, buyer_address, time_slot)
        session_svc.patch(session_id, {"pending_test_drives": [car_id]})
        return booking

    @tool
    def llm_rank(session_id: str, candidate_ids: list[str]) -> dict:
        """
        Perform LLM-based final ranking on candidate cars.
        Call this after vector_rerank to get top 3 with personalised reasoning.
        Updates the session context with the shortlist.
        """
        context = session_svc.load(session_id)
        shortlist = ranking_svc.rank(candidate_ids, context.profile)
        session_svc.patch(
            session_id, {"shortlist": [s.model_dump() for s in shortlist]})
        return {"shortlist": [s.model_dump() for s in shortlist]}

    return [
        patch_context,
        sql_filter_inventory,
        vector_rerank,
        llm_rank,
        get_emi_estimate,
        fetch_inspection_report,
        schedule_test_drive,
    ]
