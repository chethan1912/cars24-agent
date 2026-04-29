import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from db.schemas import TestDriveBooking


class BookingService:
    def __init__(self, db: Session):
        self.db = db

    def create_test_drive(
        self,
        session_id: str,
        car_id: str,
        buyer_address: str,
        time_slot: str
    ) -> dict:
        booking = TestDriveBooking(
            booking_id=f"TD_{uuid.uuid4().hex[:8].upper()}",
            session_id=session_id,
            car_id=car_id,
            buyer_address=buyer_address,
            time_slot=time_slot,
            status="confirmed",
            created_at=datetime.utcnow()
        )
        self.db.add(booking)
        self.db.commit()
        return {
            "booking_id": booking.booking_id,
            "car_id": car_id,
            "time_slot": time_slot,
            "address": buyer_address,
            "status": "confirmed",
        }
