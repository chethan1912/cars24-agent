from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from db.schemas import Car
from db.database import get_db
from core.models import BuyerProfile
from typing import Optional


class InventoryService:
    def __init__(self, db: Session):
        self.db = db

    def filter_inventory(
        self,
        profile: BuyerProfile,
        year_min: int = 2017,
        km_max: int = 100000,
        limit: int = 200
    ) -> list[str]:
        """
        Apply hard constraints. Returns list of car_ids.
        Fast — runs on indexed columns only.
        Target: < 100ms.
        """
        query = self.db.query(Car.car_id).filter(
            Car.available == True,
            Car.city == profile.city,
            Car.price_onroad <= profile.budget_ceiling,
            Car.year >= year_min,
            Car.km_driven <= km_max,
        )

        # Fuel type filter — OR across preferences
        if profile.fuel_pref:
            query = query.filter(
                or_(*[Car.fuel_type == f for f in profile.fuel_pref])
            )

        result = query.limit(limit).all()
        car_ids = [row.car_id for row in result]

        # Auto-relax if too few results
        if len(car_ids) < 5:
            car_ids = self._relax_and_retry(profile, year_min, km_max, limit)

        return car_ids

    def _relax_and_retry(
        self, profile: BuyerProfile,
        year_min: int, km_max: int, limit: int
    ) -> list[str]:
        """
        Relax constraints in order of priority:
        1. Increase km_max by 20%
        2. Increase budget by 10%
        3. Drop year_min by 2 years
        Log which constraint was relaxed so LLM can mention it.
        """
        relaxations = [
            {"km_driven": km_max * 1.2},
            {"price_onroad": profile.budget_ceiling * 1.1},
            {"year": year_min - 2},
        ]
        for relax in relaxations:
            query = self.db.query(Car.car_id).filter(
                Car.available == True,
                Car.city == profile.city,
            )
            if "km_driven" in relax:
                query = query.filter(Car.km_driven <= relax["km_driven"])
            if "price_onroad" in relax:
                query = query.filter(Car.price_onroad <= relax["price_onroad"])
            if "year" in relax:
                query = query.filter(Car.year >= relax["year"])
            result = query.limit(limit).all()
            if len(result) >= 5:
                return [r.car_id for r in result]
        return []

    def get_car_details(self, car_ids: list[str]) -> list[dict]:
        """Fetch full car dicts for a list of IDs."""
        cars = self.db.query(Car).filter(Car.car_id.in_(car_ids)).all()
        return [
            {
                "car_id": c.car_id,
                "make": c.make,
                "model": c.model,
                "variant": c.variant,
                "year": c.year,
                "fuel_type": c.fuel_type,
                "km_driven": c.km_driven,
                "price_onroad": c.price_onroad,
                "inspection_score": c.inspection_score,
                "resale_index": c.resale_index,
                "owner_count": c.owner_count,
                "inspection_summary": c.inspection_summary,
                "warranty_months_left": c.warranty_months_left,
            }
            for c in cars
        ]
