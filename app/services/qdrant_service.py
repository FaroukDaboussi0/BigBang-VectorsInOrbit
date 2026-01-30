from qdrant_client import QdrantClient
from qdrant_client.http import models
from typing import List, Dict, Any
import numpy as np
from app.models.domain_models import MemoryHit

class QdrantService:
    def __init__(self, url: str, api_key: str):
        self.client = QdrantClient(url=url, api_key=api_key)
        
        # Collection Names
        self.RISK_COLLECTION = "credit_decision_memory"
        self.FRAUD_COLLECTION = "fraud_anomaly_memory"

    def search_similarity(self, vector: List[float], collection_name: str, limit: int = 3) -> List[MemoryHit]:
        """
        Generic search function to find the 'Past Ghosts' in memory.
        """
        try:
            search_result = self.client.query_points(
                collection_name=collection_name,
                query=vector,
                limit=limit,
                with_payload=True
            )

            hits = []
            for hit in search_result.points:
                hits.append(MemoryHit(
                    collection=collection_name,
                    score=hit.score,
                    payload=hit.payload
                ))
            return hits
        
        except Exception as e:
            print(f"Qdrant Search Error on {collection_name}: {e}")
            return []

    def add_to_memory(self, application_id: str, vector: List[float], payload: Dict[str, Any], collection_name: str):
        """
        The 'Self-Learning' component. Saves a finalized decision back to vector storage.
        """
        try:
            # Clean payload: Qdrant/JSON doesn't like NumPy types (int64, float64)
            clean_payload = {}
            for k, v in payload.items():
                if isinstance(v, (np.int64, np.integer)):
                    clean_payload[k] = int(v)
                elif isinstance(v, (np.float64, np.floating)):
                    clean_payload[k] = float(v)
                elif v is None:
                    clean_payload[k] = "N/A"
                else:
                    clean_payload[k] = v

            self.client.upsert(
                collection_name=collection_name,
                points=[
                    models.PointStruct(
                        id=application_id, # Using application_id as the unique Point ID
                        vector=vector,
                        payload=clean_payload
                    )
                ]
            )
            return True
        except Exception as e:
            print(f"Qdrant Upsert Error on {collection_name}: {e}")
            return False

    def check_health(self) -> bool:
        """Dashboard utility to check if memory is live"""
        try:
            self.client.get_collections()
            return True
        except:
            return False