from app.services.qdrant_service import QdrantService
from app.services.llm_service import LLMService
from app.core.feature_engine import FeatureEngine
from app.core.orchestrator import CreditOrchestrator
from app.core.config import SETTINGS

# Initialize services as singletons
qdrant_svc = QdrantService(url=SETTINGS.QDRANT_URL, api_key=SETTINGS.QDRANT_API_KEY)
llm_svc = LLMService(api_key=SETTINGS.GROQ_API_KEY)
engine_svc = FeatureEngine(
    risk_scaler_path="models/risk_scaler.joblib", 
    fraud_scaler_path="models/fraud_scaler.joblib"
)

orchestrator = CreditOrchestrator(engine_svc, qdrant_svc, llm_svc)

def get_orchestrator():
    return orchestrator

def get_density_maps():
    # In a real app, these would come from Redis or a Database
    # For now, we return empty dicts or pre-loaded JSON
    return {'ip': {}, 'device': {}}