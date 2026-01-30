import os
import json
import re
import uuid
import google.generativeai as genai
import io
import numpy as np
import tempfile
from enum import Enum
from typing import List, Dict, Any, Optional, Type, Union
from pydantic import BaseModel, Field, create_model
from PIL import Image
from difflib import SequenceMatcher
from datetime import datetime
from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from collections import Counter
from qdrant_client import QdrantClient
from fastembed import ImageEmbedding


class IDCardVerifier:
    def __init__(self, url, api_key, collection_name="id_verification_system", threshold=0.80):
        self.qc = QdrantClient(url=url, api_key=api_key)
        self.model = ImageEmbedding(model_name="Qdrant/clip-ViT-B-32-vision")
        self.collection_name = collection_name
        self.threshold = threshold

    def predict(self, image_path):
        if not os.path.exists(image_path):
            return {"status": "error", "message": f"File '{image_path}' not found."}
        query_vector = list(self.model.embed([image_path]))[0].tolist()
        response = self.qc.query_points(collection_name=self.collection_name, query=query_vector, limit=20)
        points = response.points
        if not points:
            return {"is_valid": False, "verdict": "not valid", "side": "unknown", "avg_score": 0.0}
        scores = [res.score for res in points]
        avg_score = np.mean(scores)
        sides = [res.payload.get('side', 'unknown') for res in points]
        most_common_side = Counter(sides).most_common(1)[0][0]
        return {
            "is_valid": avg_score >= self.threshold,
            "verdict": "valid" if avg_score >= self.threshold else "not valid",
            "side": most_common_side,
            "avg_score": round(float(avg_score), 4),
            "top_match_filename": points[0].payload.get('filename', 'N/A')
        }

class DocumentType(str, Enum):
    NATIONAL_ID = "National ID Card"
    SALARY_SLIP = "Salary Slip / Certificate"
    TAX_DECLARATION = "Tax Declaration (DUR)"
    BANK_STATEMENT = "Bank Statements (6 Months)"
    PROPERTY_DOC = "Property Title / Utility Bill"
    BANK_TRANSACTIONS = "Detailed Transaction History"

class DocumentAnalysis(BaseModel):
    is_authentic: bool
    is_valid: bool
    validation_reasoning: str
    document_type_detected: str

class ValidationIssue(BaseModel):
    field: str
    message: str
    severity: str 
    score: float 

class CrossValidationReport(BaseModel):
    overall_fraud_flag: bool
    identity_score: float
    income_match_flag: bool
    issues: List[ValidationIssue]
    final_decision: str
    qdrant_id_validation: Optional[Dict[str, Any]] = None

class SchemaFactory:
    @staticmethod
    def create_response_model(doc_info: Dict[str, Any]) -> Type[BaseModel]:
        doc_name = doc_info['document_name_latin'].replace(' ', '').replace('/', '_')
        dataset_fields = {f: (Optional[str], Field(None)) for f in doc_info['extracted_fields']}
        DataModel = create_model(f"{doc_name}Data", **dataset_fields)
        anchor_fields = {f: (Optional[str], Field(None)) for f in doc_info['cross_validation_anchors']}
        AnchorModel = create_model(f"{doc_name}Anchors", **anchor_fields)

        class FinalResponse(BaseModel):
            document_analysis: DocumentAnalysis
            extracted_data: DataModel
            cross_validation_anchors: AnchorModel
            confidence_score: float
        return FinalResponse

class PromptEngine:
    @staticmethod
    def build_prompt(doc_info: Dict[str, Any], schema_json: str, image_count: int) -> str:
        return f"""
    ### ROLE
    You are a Senior Bank Underwriting AI specializing in forensic document analysis and structured data extraction.
    ### CONTEXT
    - **Document Type**: {doc_info['document_name_latin']} ({doc_info.get('document_name_arabic', 'N/A')})
    - **Process Instruction**: {doc_info['helper_text']}
    ### MULTI-IMAGE ANALYSIS
    I have provided {image_count} image(s) for this document. 
    1. Analyze ALL images collectively to extract the required information.
    2. If data is split, merge them into a single record.
    3. Perform forensic inspection across all provided pages to ensure consistency.
    ### OBJECTIVES
    1. **Liveness Check**: Inspect for signs of digital manipulation.
    2. **Validity Check**: Ensure the document is official and not expired.
    3. **Structured Extraction**: Extract fields exactly as they appear.
    4. **Anchor Extraction**: Identify key identity links.
    ### OUTPUT GUARANTEE
    You must respond ONLY with a valid JSON object matching this schema:
    {schema_json}
    """

class LoanUnderwriter:
    def __init__(self, config_json: str, api_key: str):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel("gemini-2.0-flash")
        self.config = json.loads(config_json)
        self.registry = {doc['document_name_latin']: doc for doc in self.config['documents']}

    def _clean_json(self, text: str) -> str:
        match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
        return match.group(1) if match else text.strip()

    def process(self, doc_type: DocumentType, images: List[Image.Image]):
        doc_info = self.registry.get(doc_type.value)
        ResponseModel = SchemaFactory.create_response_model(doc_info)
        prompt = PromptEngine.build_prompt(doc_info, json.dumps(ResponseModel.model_json_schema(), indent=2), len(images))
        content = [prompt] + images
        response = self.model.generate_content(content)
        return ResponseModel.model_validate_json(self._clean_json(response.text))

class CrossValidationEngine:
    def __init__(self):
        self.issues: List[ValidationIssue] = []

    def _fuzzy_match(self, str1: str, str2: str) -> float:
        if not str1 or not str2: return 0.0
        return SequenceMatcher(None, str1.upper(), str2.upper()).ratio()

    def run_pipeline(self, results: Dict[DocumentType, Any], qdrant_id_val: Optional[Dict[str, Any]], skip_national_id_llm: bool):
        fraud_detected = False
        if skip_national_id_llm:
            self.issues.append(ValidationIssue(field="National ID Card", message="Failed Qdrant visual verification", severity="CRITICAL", score=0.0))
            fraud_detected = True
        
        name_score = 0.0
        if DocumentType.NATIONAL_ID in results and DocumentType.SALARY_SLIP in results:
            id_data = results[DocumentType.NATIONAL_ID].extracted_data
            id_name = f"{id_data.first_name} {id_data.last_name}"
            salary_name = getattr(results[DocumentType.SALARY_SLIP].cross_validation_anchors, 'full_name', "")
            name_score = self._fuzzy_match(id_name, salary_name)
            if name_score < 0.85:
                fraud_detected = True

        decision = "Rejected" if fraud_detected else ("Flagged" if len(self.issues) > 0 else "Verified")
        return CrossValidationReport(
            overall_fraud_flag=fraud_detected,
            identity_score=name_score,
            income_match_flag=True,
            issues=self.issues,
            final_decision=decision,
            qdrant_id_validation=qdrant_id_val
        )

class DataMapper:
    @staticmethod
    def to_dataset_row(engine_results: Dict[DocumentType, Any]) -> Dict[str, Any]:
        id_data = engine_results.get(DocumentType.NATIONAL_ID).extracted_data if DocumentType.NATIONAL_ID in engine_results else None
        trans_data = engine_results.get(DocumentType.BANK_TRANSACTIONS).extracted_data if DocumentType.BANK_TRANSACTIONS in engine_results else None

        return {
            "application_id": str(uuid.uuid4()),
            "customer_id": getattr(trans_data, 'customer_id', None) or (id_data.id_number if id_data else None),
            "application_date": datetime.now().strftime("%Y-%m-%d"),
            "recent_transaction_amount": getattr(trans_data, 'transaction_amount', None),
            "recent_merchant": getattr(trans_data, 'merchant_name', None),
            "transaction_status": getattr(trans_data, 'transaction_status', None),
            "inferred_category": getattr(trans_data, 'merchant_category', None)
        }


app = FastAPI(title="Loan Document Underwriting API")

CONFIG = {"documents": [
    {"document_name_latin": "National ID Card", "extracted_fields": ["first_name", "last_name", "id_number"], "cross_validation_anchors": ["id_number", "full_name"], "helper_text": "Identity."},
    {"document_name_latin": "Salary Slip / Certificate", "extracted_fields": ["monthly_income"], "cross_validation_anchors": ["full_name"], "helper_text": "Income."},
    {"document_name_latin": "Tax Declaration (DUR)", "document_name_arabic": "التصريح الوحيد بالدخل", "extracted_fields": ["number_of_dependents", "annual_taxable_income"], "cross_validation_anchors": ["full_name", "id_number"], "helper_text": "Legal dependents count."},
    {"document_name_latin": "Bank Statements (6 Months)", "document_name_arabic": "كشوفات البنكي", "extracted_fields": ["existing_emis_monthly", "total_salary_credits"], "cross_validation_anchors": ["account_holder_name", "employer_name_in_transactions"], "helper_text": "Financial liabilities."},
    {"document_name_latin": "Property Title / Utility Bill", "document_name_arabic": "شهادة ملكية", "extracted_fields": ["property_ownership_status", "residential_address"], "cross_validation_anchors": ["full_name", "residential_address"], "helper_text": "Residence status."},
    {"document_name_latin": "Detailed Transaction History", "extracted_fields": ["transaction_id", "customer_id", "transaction_date", "transaction_type", "transaction_amount", "merchant_category", "merchant_name", "transaction_location", "account_balance_after_transaction", "is_international_transaction", "device_used", "ip_address", "transaction_status", "transaction_source_destination", "transaction_notes"], "cross_validation_anchors": ["customer_id", "transaction_id"], "helper_text": "Extract all transaction details."}
]}

verifier = IDCardVerifier(url="YOUR_URL", api_key="YOUR_KEY")
underwriter = LoanUnderwriter(json.dumps(CONFIG), "YOUR_GEMINI_KEY")

async def files_to_images(files: List[UploadFile]) -> List[Image.Image]:
    images = []
    for file in files:
        content = await file.read()
        images.append(Image.open(io.BytesIO(content)))
    return images


@app.post("/extract/national-id")
async def extract_national_id(files: List[UploadFile] = File(...)):
    try:
        qdrant_results = []
        is_invalid_qdrant = False
        for f in files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                content = await f.read()
                tmp.write(content)
                tmp_path = tmp.name
            await f.seek(0)
            res = verifier.predict(tmp_path)
            qdrant_results.append(res)
            if not res["is_valid"]: is_invalid_qdrant = True
            os.unlink(tmp_path)
        
        images = await files_to_images(files)
        extraction = underwriter.process(DocumentType.NATIONAL_ID, images)
        return {"extraction": extraction.dict(), "qdrant_validation": qdrant_results, "failed_visual_check": is_invalid_qdrant}
    except Exception as e: raise HTTPException(500, detail=str(e))

@app.post("/extract/salary-slip")
async def extract_salary_slip(files: List[UploadFile] = File(...)):
    images = await files_to_images(files)
    return underwriter.process(DocumentType.SALARY_SLIP, images)

@app.post("/extract/tax-declaration")
async def extract_tax_declaration(files: List[UploadFile] = File(...)):
    images = await files_to_images(files)
    return underwriter.process(DocumentType.TAX_DECLARATION, images)

@app.post("/extract/bank-statement")
async def extract_bank_statement(files: List[UploadFile] = File(...)):
    images = await files_to_images(files)
    return underwriter.process(DocumentType.BANK_STATEMENT, images)

@app.post("/extract/property-doc")
async def extract_property_doc(files: List[UploadFile] = File(...)):
    images = await files_to_images(files)
    return underwriter.process(DocumentType.PROPERTY_DOC, images)

@app.post("/extract/bank-transactions")
async def extract_bank_transactions(files: List[UploadFile] = File(...)):
    images = await files_to_images(files)
    return underwriter.process(DocumentType.BANK_TRANSACTIONS, images)


class CrossValidationRequest(BaseModel):
    extraction_results: Dict[str, Any] 
    qdrant_validation_summary: Optional[Dict[str, Any]] = None
    failed_visual_check: bool = False

@app.post("/cross-validate")
async def cross_validate(payload: CrossValidationRequest):
    try:
        processed_results = {}
        for doc_name, data in payload.extraction_results.items():
            processed_results[DocumentType(doc_name)] = type('obj', (object,), {
                'extracted_data': type('obj', (object,), data.get('extracted_data', {})),
                'cross_validation_anchors': type('obj', (object,), data.get('cross_validation_anchors', {}))
            })

        engine = CrossValidationEngine()
        report = engine.run_pipeline(
            processed_results, 
            payload.qdrant_validation_summary, 
            payload.failed_visual_check
        )
        
        return {
            "status": "success" if not report.overall_fraud_flag else "flagged",
            "report": report.dict(),
            "data": DataMapper.to_dataset_row(processed_results)
        }
    except Exception as e: raise HTTPException(500, detail=str(e))