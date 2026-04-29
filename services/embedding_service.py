from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
from core.models import BuyerProfile
from db.chroma import get_chroma_client

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
COLLECTION_NAME = "cars24_inventory"


class EmbeddingService:
    def __init__(self):
        self.model = SentenceTransformer(EMBEDDING_MODEL)
        self.client = get_chroma_client()
        self.collection = self.client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

    def build_buyer_profile_text(self, profile: BuyerProfile) -> str:
        """
        Convert structured profile into a natural language string for embedding.
        This must use the SAME vocabulary as the car attributes_text in the collection.
        """
        use_case_map = {
            "first_car": "first time buyer beginner reliable easy to maintain",
            "upgrade": "feature rich premium upgrade comfortable",
            "family": "spacious family safe reliable boot space",
            "commuter": "fuel efficient city driving low running cost",
        }
        risk_map = {
            "low": "strong resale value warranty coverage peace of mind",
            "mid": "balanced quality fair price decent features",
            "high": "best price budget lowest cost",
        }
        use_text = use_case_map.get(profile.use_case or "", "")
        risk_text = risk_map.get(profile.risk_tolerance or "", "")
        fuel_text = " ".join(profile.fuel_pref or [])
        city_text = profile.city or ""

        return f"{use_text} {risk_text} {fuel_text} {city_text}".strip()

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()

    def rerank(
        self,
        candidate_ids: list[str],
        profile: BuyerProfile,
        top_k: int = 10
    ) -> list[dict]:
        """
        Query ChromaDB restricted to candidate_ids from SQL filter.
        Returns top_k results ordered by semantic similarity to buyer profile.
        """
        if not candidate_ids:
            return []

        profile_text = self.build_buyer_profile_text(profile)
        query_embedding = self.embed(profile_text)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, len(candidate_ids)),
            where={"car_id": {"$in": candidate_ids}},
            include=["metadatas", "distances"]
        )

        ranked = []
        for i, car_id in enumerate(results["ids"][0]):
            ranked.append({
                "car_id": car_id,
                # cosine → similarity
                "similarity_score": 1 - results["distances"][0][i],
                "metadata": results["metadatas"][0][i],
            })

        return ranked

    def upsert_car(self, car_id: str, attributes_text: str, metadata: dict) -> None:
        """Called during seeding to add/update a car in ChromaDB."""
        embedding = self.embed(attributes_text)
        self.collection.upsert(
            ids=[car_id],
            embeddings=[embedding],
            metadatas=[{"car_id": car_id, **metadata}],
            documents=[attributes_text]
        )

    def delete_car(self, car_id: str) -> None:
        """Called when a car is sold — remove from vector store."""
        self.collection.delete(ids=[car_id])
