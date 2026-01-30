import numpy as np
from typing import List, Dict, Any

def clean_numerical_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively converts NumPy types to standard Python types.
    Essential for Qdrant and FastAPI JSON serialization.
    """
    clean_data = {}
    for k, v in payload.items():
        if isinstance(v, (np.int64, np.integer)):
            clean_data[k] = int(v)
        elif isinstance(v, (np.float64, np.floating)):
            # Replace NaN or Inf with 0.0 to prevent JSON errors
            if np.isnan(v) or np.isinf(v):
                clean_data[k] = 0.0
            else:
                clean_data[k] = float(v)
        elif isinstance(v, dict):
            clean_data[k] = clean_numerical_payload(v)
        else:
            clean_data[k] = v
    return clean_data

def get_similarity_label(score: float) -> str:
    """
    Converts a raw cosine similarity score into a forensic label.
    Used by the Orchestrator to guide the LLM's attention.
    """
    if score >= 0.95:
        return "CRITICAL IDENTICAL MATCH"
    elif score >= 0.90:
        return "HIGH SIMILARITY"
    elif score >= 0.80:
        return "MODERATE SIMILARITY"
    else:
        return "LOW SIMILARITY / NEUTRAL"

def normalize_vector(vector: List[float]) -> List[float]:
    """Ensures a vector contains no NaNs and is ready for search"""
    return [0.0 if np.isnan(x) or np.isinf(x) else float(x) for x in vector]