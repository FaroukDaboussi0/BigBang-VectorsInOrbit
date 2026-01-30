from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class ExtractedFeatureSet:
    """
    Standalone object containing all raw and calculated 
    features for a single applicant.
    """
    application_id: str
    customer_id: str
    
    # Combined dictionary of raw input + engineered ratios
    # This is what the Orchestrator sees.
    all_features: Dict[str, Any]
    
    # These are ready to be sent to Qdrant
    risk_vector: List[float] = field(default_factory=list)
    fraud_vector: List[float] = field(default_factory=list)

@dataclass
class MemoryHit:
    """Represents a hit from Qdrant Memory (Risk or Fraud)"""
    collection: str
    score: float
    payload: Dict[str, Any]

@dataclass
class DecisionContext:
    """
    The full context for the Brain Orchestrator.
    It bundles the current applicant's features with historical memory.
    """
    applicant_features: Dict[str, Any]
    risk_memory: List[MemoryHit]
    fraud_memory: List[MemoryHit]
    hard_rule_violations: List[str] = field(default_factory=list)
    
    def to_llm_prompt_data(self) -> Dict[str, Any]:
        """Helper to format data for the LLM Service"""
        return {
            "applicant": self.applicant_features,
            "risk_twins": [h.payload for h in self.risk_memory],
            "fraud_twins": [h.payload for h in self.fraud_memory],
            "violations": self.hard_rule_violations
        }