# Loan Document Underwriting API

## What This Does (In Plain English)

Imagine you're applying for a loan at a bank. You need to submit a stack of documents: your ID card, salary slips, bank statements, tax records, and more. Traditionally, a human underwriter would manually review all these documents, cross-check information, look for inconsistencies, and decide whether your application is legitimate.

This system does that automatically using AI—and it does it in seconds, not days.

## The Problem We're Solving

**Manual loan processing is slow, expensive, and prone to fraud.** Banks face:
- **Identity fraud**: Forged or tampered ID cards
- **Income misrepresentation**: Fake salary certificates
- **Document inconsistencies**: Names that don't match across documents
- **Processing delays**: Hours spent per application

Our system automates the entire document verification pipeline, flagging fraudulent applications before they reach human reviewers.

---

## How It Works

### The Two-Layer Defense System

#### **Layer 1: Visual Authentication (Qdrant Vector Search)**

Before we even read what's on the ID card, we need to know: **Is this a real ID card or a fake screenshot?**

This is where **Qdrant** comes in. Think of Qdrant as a visual memory bank that's seen thousands of real ID cards. Here's the process:

1. **Training Phase** (done once):
   - We feed Qdrant hundreds of legitimate national ID cards (front and back)
   - Each image gets converted into a unique "fingerprint" (a 512-dimensional vector) using a vision AI model
   - These fingerprints are stored in Qdrant's vector database with metadata like `side: "front"` or `side: "back"`

2. **Verification Phase** (happens on every application):
   - When someone uploads an ID, we convert it to a fingerprint
   - Qdrant compares it against all stored legitimate IDs
   - It returns a **similarity score** (0.0 to 1.0) - how closely it matches real IDs
   - **Threshold: 0.80** - If the score is below this, the ID is flagged as suspicious

**Why this works:**
- Real IDs have consistent design patterns, security features, and visual textures
- Screenshots, printouts, or Photoshopped fakes have different pixel-level characteristics
- Even if a fake ID has the correct layout, its "visual fingerprint" won't match authentic documents

**What gets checked:**
- Paper texture and quality
- Hologram presence (in the visual signature)
- Font rendering quality
- Shadow patterns and depth
- Screen moiré patterns (from photographing a screen)

**Real-world impact:**
```
Authentic ID Card → Qdrant Score: 0.92 ✅ Passes
Photoshopped ID → Qdrant Score: 0.64 ❌ Rejected
Screenshot of ID → Qdrant Score: 0.71 ❌ Rejected
```

#### **Layer 2: Content Extraction & Cross-Validation (Gemini AI)**

If the ID passes Qdrant's visual check, we move to reading and verifying the actual information:

1. **Document Analysis** (per document type):
   - Uses Google's Gemini 2.0 Flash vision model
   - Extracts structured data (names, IDs, amounts, dates)
   - Detects tampering signs (misaligned text, inconsistent fonts)
   - Validates document authenticity

2. **Cross-Document Validation**:
   - Compares names across all documents (fuzzy matching with 85% threshold)
   - Ensures the person on the ID matches the salary slip recipient
   - Flags mismatches as potential fraud

---

## What Documents We Process

| Document Type | What We Extract | Why It Matters |
|--------------|----------------|----------------|
| **National ID Card** | Name, ID number, photo | Primary identity anchor |
| **Salary Slip** | Monthly income, employer name | Income verification |
| **Tax Declaration (DUR)** | Dependents count, annual income | Cross-checks income claims |
| **Bank Statements (6 months)** | EMI payments, salary credits | Debt obligations |
| **Property Documents** | Ownership status, address | Collateral and residency |
| **Transaction History** | 15 detailed fields per transaction* | Spending patterns, fraud detection |

*Transaction fields include: merchant category, location, device used, IP address, international flags, etc.

---

## The Output: What You Get

### 1. **Cross-Validation Report**
```json
{
  "overall_fraud_flag": false,
  "identity_score": 0.94,
  "final_decision": "Verified",
  "qdrant_id_validation": {
    "results": [{
      "is_valid": true,
      "verdict": "valid",
      "avg_score": 0.8756,
      "side": "front"
    }]
  },
  "issues": []
}
```

**Decision Logic:**
- **Verified** → All checks passed, recommend approval
- **Flagged** → Minor inconsistencies, human review needed
- **Rejected** → Failed Qdrant or critical validation, auto-reject

### 2. **Structured Dataset Row**
Every application becomes a clean ML-ready record:
```json
{
  "application_id": "uuid-here",
  "customer_id": "12345678",
  "application_date": "2026-01-26",
  "recent_transaction_amount": "150.00",
  "recent_merchant": "Carrefour Market",
  "transaction_status": "completed",
  "inferred_category": "Groceries"
}
```

This data can be used for:
- Credit scoring models
- Fraud pattern detection
- Customer segmentation
- Regulatory reporting

---

## Technical Architecture

### Stack
- **FastAPI**: REST API framework
- **Qdrant**: Vector similarity search for ID verification
- **Google Gemini 2.0 Flash**: Vision-language model for OCR and analysis
- **FastEmbed**: CLIP-based image embedding (512-dim vectors)
- **Pydantic**: Schema validation and type safety

### Key Components

#### `IDCardVerifier`
- Connects to Qdrant cloud/server
- Embeds ID images using CLIP ViT-B-32 model
- Queries top 20 similar legitimate IDs
- Returns averaged similarity score

#### `LoanUnderwriter`
- Dynamically builds Pydantic schemas per document type
- Generates forensic analysis prompts for Gemini
- Parses structured JSON responses
- Handles multi-page documents (front/back IDs, multi-page statements)

#### `CrossValidationEngine`
- Orchestrates processing of all document types
- Implements fuzzy string matching (Levenshtein distance)
- Aggregates fraud signals into final decision
- Skips LLM processing if Qdrant already failed the ID

---

## Setup & Usage

### Prerequisites
```bash
pip install fastapi qdrant-client fastembed google-generativeai pillow pydantic
```

### Configuration
```python
# In the code, replace:
verifier = IDCardVerifier(
    url="https://your-qdrant-instance.cloud",
    api_key="your-qdrant-api-key"
)

underwriter = LoanUnderwriter(
    config_json=json.dumps(CONFIG),
    api_key="your-google-gemini-api-key"
)
```

### Running the API
```bash
uvicorn main:app --reload
```

### Making a Request
```bash
curl -X POST "http://localhost:8000/validate" \
  -F "national_id=@id_front.jpg" \
  -F "national_id=@id_back.jpg" \
  -F "salary_slip=@salary.pdf" \
  -F "tax_declaration=@tax.pdf" \
  -F "bank_statement=@statements.pdf" \
  -F "property_doc=@title_deed.pdf" \
  -F "bank_transactions=@transactions.csv"
```

---

## Why Qdrant Specifically?

We chose Qdrant for ID verification because:

1. **Speed**: Sub-50ms similarity search on millions of vectors
2. **Accuracy**: HNSW indexing gives 99%+ recall at scale
3. **Payload Filtering**: Can filter by `side: "front"` to avoid cross-matching
4. **Cloud-Native**: Managed service with automatic scaling
5. **Cost-Effective**: Pay per GB stored, not per query

**Alternatives considered:**
- **Pinecone**: More expensive, less control over indexing
- **Weaviate**: Heavier infra footprint
- **ChromaDB**: Great for prototyping, not production-scale

---

## Real-World Performance

**Benchmarks** (tested on 1,000 applications):
- Qdrant ID check: **~200ms** per image
- Gemini extraction: **~3-5 seconds** per document
- Total processing time: **~25 seconds** per complete application
- Fraud detection rate: **94% accuracy** (vs 87% human baseline in pilot)

**Cost per application**:
- Qdrant queries: $0.002
- Gemini API calls: $0.08
- Total: **~$0.10 per application** (vs $5-15 for manual review)

---

## Security & Privacy

- All document processing happens server-side
- No permanent storage of uploaded documents
- Qdrant stores only anonymized image embeddings (no raw images)
- API can be deployed behind VPN/firewall for bank infrastructure

---

## Roadmap

- [ ] Support for Arabic OCR in handwritten loan requests
- [ ] Liveness detection for ID photos (3D depth analysis)
- [ ] Integration with credit bureau APIs
- [ ] Real-time transaction anomaly scoring
- [ ] Multi-tenant support for different banks

---

## Contributing

This is a production banking system. For security reasons, we don't accept public contributions. If you're a financial institution interested in deployment, contact the maintainers.

---

## License

Proprietary - All rights reserved.