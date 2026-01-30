import json
from groq import Groq
from typing import Dict, Any, List
from app.core.config import SETTINGS # Assuming we store keys in config

class LLMService:
    def __init__(self, api_key: str = SETTINGS.GROQ_API_KEY, model_name: str = "llama-3.3-70b-versatile"):
        self.client = Groq(api_key=api_key)
        self.model = model_name

    def get_decision(self, context_data: Dict[str, Any]) -> str:
        """
        Communicates with Groq to get the final underwriter decision.
        context_data: Formatted dictionary from OrchestratorContext
        """
        
        system_prompt = (
            "You are a Senior Forensic Underwriter and Credit Risk Specialist. "
            "Your task is to provide a final decision on a loan application by "
            "comparing the current applicant against the bank's 'Historical Memory'. "
            "You must balance financial risk with behavioral fraud anomalies."
        )

        user_prompt = self._build_forensic_prompt(context_data)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.0, # Precision is mandatory
                max_tokens=800
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error communicating with LLM: {str(e)}"

    def _build_forensic_prompt(self, data: Dict[str, Any]) -> str:
        """Constructs the high-density prompt for Llama 3.3"""
        
        applicant = data.get("applicant", {})
        risk_twins = data.get("risk_twins", [])
        fraud_twins = data.get("fraud_twins", [])
        violations = data.get("violations", [])

        # Format Memory hits into strings
        risk_memory_str = "\n".join([
            f"- Twin (Similarity: {t.get('score', 0):.2f}): Status {t.get('loan_status')}, CIBIL {t.get('cibil_score')}"
            for t in risk_twins
        ]) if risk_twins else "No similar financial profiles found."

        fraud_memory_str = "\n".join([
            f"- Anomaly Match (Similarity: {t.get('score', 0):.2f}): Type {t.get('fraud_type')}, Outcome {t.get('loan_status')}"
            for t in fraud_twins
        ]) if fraud_twins else "No similar fraud patterns found."

        # Construct the Prompt
        prompt = f"""
        ### NEW APPLICANT SUMMARY
        - CIBIL Score: {applicant.get('cibil_score')}
        - Claimed Monthly Income: ${applicant.get('monthly_income')}
        - Loan Amount Requested: ${applicant.get('loan_amount_requested')}
        - Device Sharing Score: {applicant.get('max_device_sharing_score')}
        - Midnight Application: {"Yes" if applicant.get('midnight_app_flag') == 1 else "No"}

        ### HARD RULE VIOLATIONS (Pre-processed)
        {", ".join(violations) if violations else "None"}

        ### HISTORICAL FINANCIAL TWINS (Risk Memory)
        {risk_memory_str}

        ### HISTORICAL ANOMALIES (Fraud Memory)
        {fraud_memory_str}

        ### DECISION LOGIC GUIDELINES
        1. FRAUD OVERRIDE: If a Fraud Match similarity is > 0.90, REJECT regardless of CIBIL score.
        2. LIFESTYLE CHECK: Look at 'Income vs Spend' ratios. If the applicant claims high income but twins with low spend were rejected for 'Income Misrepresentation', flag it.
        3. BUFFER: If Fraud Match similarity is < 0.85 and Credit Twins were 'Approved', lean towards APPROVAL.
        4. DEVICE SCORE: A score of 1.0 is PERFECT and SAFE. Do NOT penalize for a score of 1.
        5. SIMILARITY WEIGHT: If any Twin has a similarity > 0.95, that twin represents the "Ground Truth" of how this bank handles such cases.
        6. STATUS CONFLICT: If twins are split between Approved and Declined, prioritize 'Approved' if the applicant's CIBIL is > 650 and Debt-to-Income is < 40%.
        7. SIMILARITY CHECK: Do NOT say similarity is low if scores are > 0.90. 0.90+ is VERY HIGH.
        4. BE DECISIVE.

        ### REQUIRED OUTPUT FORMAT (Strict)
        FINAL_STATUS: [APPROVED or REJECTED]
        CONFIDENCE_LEVEL: [0-100]%
        EXPLANATION: [3-5 sentences analyzing the match between current data and historical memory]
        SUGGESTIONS: [List 2-3 specific verification steps for the agent]
        """
        return prompt