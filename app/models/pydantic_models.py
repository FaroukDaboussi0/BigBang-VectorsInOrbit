from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Literal, Union
from datetime import date, datetime

# --- Categorical Type Definitions (Based on Dataset) ---
LoanType = Literal['Business Loan', 'Car Loan', 'Education Loan', 'Personal Loan', 'Home Loan']
LoanStatus = Literal['Approved', 'Declined', 'Fraudulent - Detected', 'Fraudulent - Undetected']
PurposeOfLoan = Literal['Medical Emergency', 'Education', 'Debt Consolidation', 'Business Expansion', 'Wedding', 'Vehicle Purchase', 'Home Renovation']
EmploymentStatus = Literal['Retired', 'Unemployed', 'Self-Employed', 'Salaried', 'Business Owner', 'Student']
PropertyStatus = Literal['Rented', 'Owned', 'Jointly Owned']
Gender = Literal['Male', 'Female', 'Other']

TransactionType = Literal['Bill Payment', 'UPI', 'Debit Card', 'Credit Card', 'Loan Disbursement', 'ATM Withdrawal', 'Net Banking', 'Fund Transfer', 'Deposit', 'EMI Payment']
MerchantCategory = Literal['Dining', 'Travel', 'Entertainment', 'Utilities', 'Electronics', 'Healthcare', 'Cash Withdrawal', 'Financial Services', 'Groceries', 'Education', 'Online Shopping', 'Fuel']
DeviceUsed = Literal['Web', 'ATM', 'Mobile', 'POS']
TransactionStatus = Literal['Success', 'Failed']
FraudType = Literal['Transaction Laundering', 'Income Misrepresentation', 'Synthetic Identity', 'Loan Stacking']

# --- Input Models ---

class TransactionInput(BaseModel):
    transaction_id: str
    customer_id: str
    transaction_date: str # keeping as str to match your schema
    transaction_type: TransactionType
    transaction_amount: float
    merchant_category: MerchantCategory
    merchant_name: str
    transaction_location: str
    account_balance_after_transaction: float
    is_international_transaction: int = Field(ge=0, le=1)
    device_used: DeviceUsed
    ip_address: str
    transaction_status: TransactionStatus
    transaction_source_destination: str
    transaction_notes: str
    fraud_flag: Optional[int] = 0

class LoanApplicationInput(BaseModel):
    application_id: str
    customer_id: str
    application_date: str
    loan_type: LoanType
    loan_amount_requested: float
    loan_tenure_months: int # [12, 240, 60, 120, 36, 24, 360]
    interest_rate_offered: float
    purpose_of_loan: PurposeOfLoan
    employment_status: EmploymentStatus
    monthly_income: float
    cibil_score: int
    existing_emis_monthly: float
    debt_to_income_ratio: float
    property_ownership_status: PropertyStatus
    residential_address: str
    applicant_age: int
    gender: Gender
    number_of_dependents: int # [0, 1, 2, 3, 4]

class PipelineRequest(BaseModel):
    application: LoanApplicationInput
    transactions: List[TransactionInput]

# --- Output Models ---

class TwinPayload(BaseModel):
    # Core Fields (Present in both)
    customer_id: str
    loan_status: str
    similarity_score: float
    
    # Risk Collection Metadata
    loan_type: Optional[str] = None
    purpose_of_loan: Optional[str] = None
    monthly_income: Optional[float] = None
    cibil_score: Optional[int] = None
    loan_amount_requested: Optional[float] = None
    essential_spending_ratio: Optional[float] = None
    lifestyle_spending_ratio: Optional[float] = None
    cash_flow_coverage_ratio: Optional[float] = None
    income_stability_proxy: Optional[float] = None

    # Fraud Collection Metadata
    fraud_flag: Optional[int] = None
    fraud_type: Optional[Union[str, int, float]] = None
    avg_tx_amount: Optional[float] = None
    sum_tx_amount: Optional[float] = None
    total_tx_count: Optional[int] = None
    employment_status: Optional[str] = None
    unique_ips: Optional[int] = None
    unique_devices: Optional[int] = None
    max_ip_sharing_score: Optional[int] = None
    max_device_sharing_score: Optional[int] = None
    income_validation_ratio: Optional[float] = None
    failed_ratio: Optional[float] = None
    midnight_app_flag: Optional[int] = None
    suspicious_notes_count: Optional[int] = None
    mule_indicator_ratio: Optional[float] = None

    @validator('fraud_type')
    def clean_fraud_type(cls, v):
        """Prevents crash if fraud_type is 0 or NaN"""
        if v is None or v == 0 or v == "0" or str(v).lower() == "nan":
            return "N/A"
        return str(v)

class PipelineResponse(BaseModel):
    application_id: str
    decision_status: Literal['APPROVED', 'REJECTED', 'REFER_TO_FRAUD']
    confidence_score: int = Field(ge=0, le=100)
    explanation: str
    suggestions: List[str]
    risk_twins: List[TwinPayload]
    fraud_matches: List[TwinPayload]

class ManualReviewAction(BaseModel):
    """The model for Human-in-the-loop feedback"""
    application_id: str
    reviewer_id: str
    final_status: Literal['Approved', 'Declined', 'Fraudulent - Detected']
    notes: str