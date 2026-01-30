### Endpoint Documentation

#### 1. Document Extraction Endpoints
These endpoints handle the OCR and AI forensic extraction for specific document types.

| Endpoint | Method | Input | Description |
| :--- | :--- | :--- | :--- |
| `/extract/national-id` | `POST` | `files: UploadFile[]` | Performs Qdrant visual verification AND Gemini data extraction. Returns visual scores and extracted text. |
| `/extract/salary-slip` | `POST` | `files: UploadFile[]` | Extracts income and employer details using Gemini. |
| `/extract/tax-declaration` | `POST` | `files: UploadFile[]` | Extracts annual taxable income and dependents. |
| `/extract/bank-statement` | `POST` | `files: UploadFile[]` | Extracts EMI and salary credit history. |
| `/extract/property-doc` | `POST` | `files: UploadFile[]` | Extracts residency and ownership status. |
| `/extract/bank-transactions`| `POST` | `files: UploadFile[]` | Extracts high-granularity transaction history and merchant info. |

**Response Format (Extraction):**
```json
{
  "document_analysis": { "is_authentic": true, "is_valid": true, ... },
  "extracted_data": { ... },
  "cross_validation_anchors": { ... },
  "confidence_score": 0.95
}
```

#### 2. Cross-Validation Endpoint
This endpoint executes the comparison logic (fuzzy matching and fraud flagging) between the results of the previous extractions.

| Endpoint | Method | Input | Description |
| :--- | :--- | :--- | :--- |
| `/cross-validate` | `POST` | `JSON Body` | Compares "National ID" against "Salary Slip" anchors and calculates the final decision. |

**Request Body Example:**
```json
{
  "extraction_results": {
    "National ID Card": { "extracted_data": {...}, "cross_validation_anchors": {...} },
    "Salary Slip / Certificate": { ... }
  },
  "qdrant_validation_summary": { "results": [...] },
  "failed_visual_check": false
}
```

**Response Format (Validation):**
```json
{
  "status": "success",
  "report": {
    "overall_fraud_flag": false,
    "identity_score": 0.98,
    "final_decision": "Verified",
    "issues": []
  },
  "data": {
    "application_id": "uuid-v4",
    "customer_id": "...",
    "application_date": "2024-..."
  }
}
```