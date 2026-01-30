# 🏦 IntelliCredit: Vectors In Orbit 🚀
**Intelligent Decision Memory Retrieval Pipeline for Credit Risk & Fraud Detection**

Built for the **BigBang-VectorsInOrbit** Repository.

## 🌟 Overview
IntelliCredit is a next-generation "Self-Learning" credit underwriting system. Unlike traditional static models, this pipeline utilizes **Dual-Path Vector Retrieval (RAG)** to compare new loan applicants against a "Historical Decision Memory." 

By combining **Llama 3.3 (Groq)** with **Qdrant Vector Database**, the system doesn't just predict; it reasons based on the bank's past successes and failures.

---

## 🏗️ Architecture
The system follows a standalone, modular architecture:

1. **Input**: Loan Application + Raw Transaction History.
2. **Feature Engine**: Standalone module extracting 50+ forensic and financial ratios.
3. **Similarity Retrieval (Memory)**: 
    *   **Path A (Risk)**: Finds financial "twins" to assess creditworthiness.
    *   **Path B (Fraud)**: Identifies behavioral anomalies and network overlaps (IP/Device).
4. **Brain Orchestrator**: A Forensic LLM (Llama 3.3) + Rule-Based system that synthesizes memory into a final verdict.
5. **Self-Learning Loop**: Human experts finalize decisions, which are "upserted" back into the Vector Store to improve future AI accuracy.

---

## 🚀 Key Features
- **Forensic Reasoning**: Detects "Liar Loans" by analyzing the gap between claimed income and spending behavior.
- **Network Intelligence**: Detects Fraud Hubs using IP and Device sharing density scores.
- **Decision Memory**: Every human manual approval/rejection makes the AI smarter.
- **FastAPI Backend**: Industrial-strength asynchronous API.
- **Streamlit Dashboard**: Beautiful UI for underwriters to visualize "Past Ghosts" (Twins) found in memory.

---

## 🛠️ Tech Stack
- **Language**: Python 3.10+
- **Brain**: Groq API (Llama 3.3 70B)
- **Memory**: Qdrant Vector Database
- **API Framework**: FastAPI + Pydantic v2
- **Dashboard**: Streamlit
- **Math**: Scikit-Learn (Scalers), Pandas, NumPy

---

## 🔧 Installation & Setup

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/FaroukDaboussi0/BigBang-VectorsInOrbit.git
   cd intelli-credit-pipeline
