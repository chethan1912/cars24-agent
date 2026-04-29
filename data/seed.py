"""
Run this once after populating data/sample_cars.json.
Inserts all cars into Postgres AND ChromaDB.
"""
import json
import asyncio
from db.postgres import get_db
from db.schemas import Car
from services.embedding_service import EmbeddingService
from datetime import datetime


def seed():
    with open("data/sample_cars.json") as f:
        cars = json.load(f)

    embedding_svc = EmbeddingService()

    with next(get_db()) as db:
        for car_data in cars:
            attributes_text = car_data.pop("attributes_text")

            # Insert into Postgres
            car = Car(**{k: v for k, v in car_data.items()
                      if k != "attributes_text"})
            db.merge(car)

            # Insert into ChromaDB
            embedding_svc.upsert_car(
                car_id=car_data["car_id"],
                attributes_text=attributes_text,
                metadata={
                    "make": car_data["make"],
                    "model": car_data["model"],
                    "city": car_data["city"],
                    "price_onroad": car_data["price_onroad"],
                    "fuel_type": car_data["fuel_type"],
                }
            )
            print(f"Seeded: {car_data['car_id']}")

        db.commit()
    print(f"Done. Seeded {len(cars)} cars.")


if __name__ == "__main__":
    seed()
