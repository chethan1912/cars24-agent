from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Car(Base):
    __tablename__ = "cars"

    # e.g. "c24_bal_2021_blr_042"
    car_id = Column(String, primary_key=True)
    make = Column(String, nullable=False)               # "Maruti"
    model = Column(String, nullable=False)              # "Baleno"
    variant = Column(String)                            # "Delta MT"
    year = Column(Integer, nullable=False, index=True)
    # "petrol" | "diesel" | "cng"
    fuel_type = Column(String, nullable=False, index=True)
    # "manual" | "automatic"
    transmission = Column(String)
    km_driven = Column(Integer)
    price_onroad = Column(Integer, nullable=False, index=True)
    city = Column(String, nullable=False, index=True)
    rto_state = Column(String)
    available = Column(Boolean, default=True, index=True)
    inspection_score = Column(Float)                    # 0-100
    warranty_months_left = Column(Integer, default=0)
    # 0-1, higher = better resale
    resale_index = Column(Float)
    color = Column(String)
    owner_count = Column(Integer)
    insurance_valid_until = Column(DateTime)
    updated_at = Column(DateTime, index=True)

    # Inspection details stored as JSON
    inspection_summary = Column(JSON)
    # e.g. {"engine": "good", "suspension": "fair", "ac": "good", "electricals": "good",
    #        "flags": ["minor paint touch-up on rear bumper"]}


class TestDriveBooking(Base):
    __tablename__ = "test_drive_bookings"

    booking_id = Column(String, primary_key=True)
    session_id = Column(String, index=True)
    car_id = Column(String, index=True)
    buyer_address = Column(Text)
    time_slot = Column(String)
    status = Column(String, default="confirmed")
    created_at = Column(DateTime)
