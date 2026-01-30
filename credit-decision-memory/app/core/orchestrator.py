import re
from typing import List, Dict, Any
from app.models.pydantic_models import PipelineRequest, PipelineResponse, TwinPayload
from app.models.domain_models import ExtractedFeatureSet, DecisionContext
from app.core.feature_engine import FeatureEngine
from app.services.qdrant_service import QdrantService
from app.services.llm_service import LLMService

class CreditOrchestrator:
    def __init__(
        self, 
        feature_engine: FeatureEngine, 
        qdrant_service: QdrantService, 
        llm_service: LLMService
    ):
        self.engine = feature_engine
        self.qdrant = qdrant_service
        self.llm = llm_service

    async def process_application(self, request: PipelineRequest, ip_map: Dict, dev_map: Dict) -> PipelineResponse:
        """
        The full standalone pipeline execution.
        """
        # 1. Feature Extraction (Standalone Logic)
        feature_set: ExtractedFeatureSet = self.engine.create_feature_set(request, ip_map, dev_map)
        
        # 2. Rule-Based Guardrails (Hard Rejections)
        violations = self._check_hard_rules(feature_set.all_features)
        
        # 3. Memory Retrieval (Dual-Path Similarity)
        risk_history = self.qdrant.search_similarity(
            vector=feature_set.risk_vector, 
            collection_name=self.qdrant.RISK_COLLECTION
        )
        
        fraud_history = self.qdrant.search_similarity(
            vector=feature_set.fraud_vector, 
            collection_name=self.qdrant.FRAUD_COLLECTION
        )

        # 4. Contextual Labeling (v5 Calibration Logic)
        # We attach labels like 'CRITICAL' so the LLM understands the score numbers
        context = DecisionContext(
            applicant_features=feature_set.all_features,
            risk_memory=risk_history,
            fraud_memory=fraud_history,
            hard_rule_violations=violations
        )

        # 5. LLM Reasoning (Forensic Synthesis)
        llm_raw_response = self.llm.get_decision(context.to_llm_prompt_data())

        # 6. Response Parsing & Structuring
        return self._build_final_response(
            request.application.application_id, 
            llm_raw_response, 
            risk_history, 
            fraud_history
        )

    def _check_hard_rules(self, f: Dict[str, Any]) -> List[str]:
        """Hard-coded banking constraints"""
        rules = []
        if f.get('cibil_score', 0) < 300:
            rules.append("CIBIL score below absolute minimum (300)")
        if f.get('installment_to_income_ratio', 0) > 0.80:
            rules.append("Debt-to-Income obligations exceed 80%")
        if f.get('applicant_age', 0) < 18:
            rules.append("Applicant below legal age")
        return rules

    def _build_final_response(
        self, 
        app_id: str, 
        raw_text: str, 
        risk_hits: List[Any], 
        fraud_hits: List[Any]
    ) -> PipelineResponse:
        """Parses the LLM text into a clean Pydantic Response"""
        
        # Regex extraction for structured fields
        status_match = re.search(r"FINAL_STATUS:\s*\[?(APPROVED|REJECTED)\]?", raw_text)
        conf_match = re.search(r"CONFIDENCE_LEVEL:\s*(\d+)%", raw_text)
        expl_match = re.search(r"EXPLANATION:\s*(.*?)(?=SUGGESTIONS:|$)", raw_text, re.DOTALL)
        sugg_match = re.search(r"SUGGESTIONS:\s*(.*)", raw_text, re.DOTALL)

        decision = status_match.group(1) if status_match else "REJECTED"
        confidence = int(conf_match.group(1)) if conf_match else 50
        explanation = expl_match.group(1).strip() if expl_match else "Decision based on historical similarity."
        
        # Clean suggestions into a list
        suggestions = []
        if sugg_match:
            suggestions = [s.strip('- ').strip() for s in sugg_match.group(1).split('\n') if s.strip()]

        # Map Qdrant hits to TwinPayloads
        risk_twins = []
        for h in risk_hits:
            p = h.payload
            risk_twins.append(TwinPayload(
                similarity_score=round(float(h.score), 2),
                **p
            ))

        fraud_twins = []
        for h in fraud_hits:
            p = h.payload
            fraud_twins.append(TwinPayload(
                similarity_score=round(float(h.score), 2),
                **p  # This automatically fills unique_ips, fraud_type, mule_ratio, etc.
            ))

        return PipelineResponse(
            application_id=app_id,
            decision_status=decision,
            confidence_score=confidence,
            explanation=explanation,
            suggestions=suggestions,
            risk_twins=risk_twins,
            fraud_matches=fraud_twins
        )