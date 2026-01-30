from fastapi import APIRouter, Depends, HTTPException
from app.models.pydantic_models import PipelineRequest, PipelineResponse, ManualReviewAction
from app.core.orchestrator import CreditOrchestrator
from app.api.deps import get_orchestrator, get_density_maps
from app.services.qdrant_service import QdrantService
from app.core.feature_engine import FeatureEngine

router = APIRouter()

@router.post("/analyze", response_model=PipelineResponse)
async def analyze_application(
    request: PipelineRequest,
    orchestrator: CreditOrchestrator = Depends(get_orchestrator),
    maps: dict = Depends(get_density_maps)
):
    """
    Step 1: AI Analysis
    Takes raw application + transactions and returns an AI recommendation.
    """
    try:
        # maps contains {'ip': ip_density, 'device': device_density}
        result = await orchestrator.process_application(
            request, 
            ip_map=maps['ip'], 
            dev_map=maps['device']
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline Error: {str(e)}")

@router.post("/finalize")
async def finalize_decision(
    action: ManualReviewAction,
    request_data: PipelineRequest, # We need the data to re-generate vectors for memory
    orchestrator: CreditOrchestrator = Depends(get_orchestrator),
    maps: dict = Depends(get_density_maps)
):
    """
    Step 2: Human-in-the-Loop (Self-Learning)
    Saves the final human decision into Qdrant memory.
    """
    try:
        # 1. Re-generate the features and vectors
        feature_set = orchestrator.engine.create_feature_set(
            request_data, 
            ip_density_map=maps['ip'],      
            device_density_map=maps['device'] 
        )
        
        # 2. Update the payload with the Human's final status
        payload = feature_set.all_features.copy()
        payload['loan_status'] = action.final_status
        payload['human_notes'] = action.notes
        
        # 3. Upsert to both Risk and Fraud collections to "teach" the memory
        orchestrator.qdrant.add_to_memory(
            application_id=action.application_id,
            vector=feature_set.risk_vector,
            payload=payload,
            collection_name=orchestrator.qdrant.RISK_COLLECTION
        )
        
        # If the human marked it as fraud, ensure it's in the fraud memory
        if "Fraudulent" in action.final_status:
            orchestrator.qdrant.add_to_memory(
                application_id=action.application_id,
                vector=feature_set.fraud_vector,
                payload=payload,
                collection_name=orchestrator.qdrant.FRAUD_COLLECTION
            )

        return {"message": "Memory updated successfully", "application_id": action.application_id}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Memory Update Failed: {str(e)}")