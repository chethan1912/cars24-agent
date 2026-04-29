"""
Run this once after creating data/used_car_dataset_with_embeddings.csv.
Inserts all cars into SQLite and ChromaDB.
"""
import pandas as pd
import uuid
from db.database import get_db
from db.schemas import Car
from services.embedding_service import EmbeddingService
from datetime import datetime

CSV_PATH = "data/used_car_dataset_with_embeddings.csv"


def normalize_string(value):
    if pd.isna(value):
        return None
    return str(value).strip()


def parse_int(value, default=0):
    try:
        return int(float(value))
    except Exception:
        return default


def build_attributes_text(row):
    parts = [
        normalize_string(row.get("brand")),
        normalize_string(row.get("model")),
        normalize_string(row.get("year")),
        normalize_string(row.get("fuel_type")),
        normalize_string(row.get("transmission")),
        normalize_string(row.get("city")),
        normalize_string(row.get("description")),
        normalize_string(row.get("additional_info")),
    ]
    return " ".join([p for p in parts if p])


def seed():
    df = pd.read_csv(CSV_PATH)
    embedding_svc = EmbeddingService()

    with next(get_db()) as db:
        for _, row in df.iterrows():
            car_id = normalize_string(row.get("car_id")) or str(uuid.uuid4())
            make = normalize_string(
                row.get("brand")) or normalize_string(row.get("make"))
            model = normalize_string(row.get("model"))
            variant = normalize_string(row.get("variant"))
            year = parse_int(row.get("year"))
            fuel_type = normalize_string(row.get("fuel_type"))
            transmission = normalize_string(row.get("transmission"))
            km_driven = parse_int(row.get("km_driven"))
            price_onroad = parse_int(row.get("price"), default=0)
            city = normalize_string(row.get("city"))
            rto_state = normalize_string(row.get("rto_state"))
            available = True
            inspection_score = parse_int(
                row.get("inspection_score"), default=None)
            warranty_months_left = parse_int(
                row.get("warranty_months_left"), default=0)
            resale_index = float(row.get("resale_index")) if pd.notna(
                row.get("resale_index")) else None
            color = normalize_string(row.get("color"))
            owner_count = parse_int(row.get("owner"))
            insurance_valid_until = None
            updated_at = datetime.utcnow()
            inspection_summary = None

            car = Car(
                car_id=car_id,
                make=make,
                model=model,
                variant=variant,
                year=year,
                fuel_type=fuel_type,
                transmission=transmission,
                km_driven=km_driven,
                price_onroad=price_onroad,
                city=city,
                rto_state=rto_state,
                available=available,
                inspection_score=inspection_score,
                warranty_months_left=warranty_months_left,
                resale_index=resale_index,
                color=color,
                owner_count=owner_count,
                insurance_valid_until=insurance_valid_until,
                updated_at=updated_at,
                inspection_summary=inspection_summary,
            )
            db.merge(car)

            attributes_text = build_attributes_text(row)
            metadata = {
                "make": make,
                "model": model,
                "city": city,
                "price_onroad": price_onroad,
                "fuel_type": fuel_type,
            }
            embedding_svc.upsert_car(
                car_id=car_id,
                attributes_text=attributes_text,
                metadata=metadata,
            )
            print(f"Seeded: {car_id}")

        db.commit()
    print(f"Done. Seeded {len(df)} cars.")


if __name__ == "__main__":
    seed()
