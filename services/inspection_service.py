from sqlalchemy.orm import Session
from db.schemas import Car


class InspectionService:
    def __init__(self, db: Session):
        self.db = db

    def get_report(self, car_id: str) -> dict | None:
        car = self.db.query(Car).filter(Car.car_id == car_id).first()
        if not car:
            return None
        return {
            "car_id": car_id,
            "make_model": f"{car.make} {car.model} {car.year}",
            "inspection_score": car.inspection_score,
            "summary": car.inspection_summary,
            "km_driven": car.km_driven,
            "owner_count": car.owner_count,
            "warranty_months_left": car.warranty_months_left,
        }

    def format_for_llm(self, report: dict) -> str:
        """Compact string for injecting into LLM context."""
        flags = report["summary"].get("flags", [])
        flag_text = "; ".join(flags) if flags else "no issues flagged"
        return (
            f"Inspection score: {report['inspection_score']}/100. "
            f"Engine: {report['summary'].get('engine', 'n/a')}. "
            f"Suspension: {report['summary'].get('suspension', 'n/a')}. "
            f"AC: {report['summary'].get('ac', 'n/a')}. "
            f"Flags: {flag_text}. "
            f"Owners: {report['owner_count']}. "
            f"Warranty: {report['warranty_months_left']} months remaining."
        )
