import os
from pydantic_settings import BaseSettings
from typing import List, Dict

class Settings(BaseSettings):
    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    QDRANT_URL: str = os.getenv("QDRANT_URL")
    QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY")
    
    # Model Paths
    RISK_SCALER_PATH: str = "models/risk_scaler.joblib"
    FRAUD_SCALER_PATH: str = "models/fraud_scaler.joblib"
    
    # Vector Configuration
    VECTOR_DISTANCE_METRIC: str = "Cosine"
    
    # Feature Engineering Constants
    ESSENTIAL_CATEGORIES: List[str] = ['Utilities', 'Healthcare', 'Groceries', 'Education', 'Fuel']
    LIFESTYLE_CATEGORIES: List[str] = ['Dining', 'Travel', 'Entertainment', 'Online Shopping', 'Electronics']
    
    # Mapping Definitions
    EMPLOYMENT_RISK_MAP: Dict[str, float] = {
        'Salaried': 0.2, 'Business Owner': 0.4, 'Self-Employed': 0.6, 
        'Student': 0.8, 'Unemployed': 1.0, 'Retired': 0.1
    }
    LOAN_TYPE_RISK_MAP: Dict[str, float] = {
        'Home Loan': 0.1, 'Car Loan': 0.2, 'Education Loan': 0.4, 
        'Business Loan': 0.7, 'Personal Loan': 0.9
    }

    # THE MASTER LISTS (Ensures vector order never breaks)
    RISK_VECTOR_FEATURES: List[str] = [
        'applicant_age', 'number_of_dependents', 'monthly_income', 'cibil_score', 
        'existing_emis_monthly', 'debt_to_income_ratio', 'loan_amount_requested', 
        'loan_tenure_months', 'interest_rate_offered', 'loan_to_income_ratio', 
        'installment_to_income_ratio', 'disposable_income', 'age_at_loan_end', 
        'income_per_dependent', 'gender_val', 'property_val', 'cibil_category_val',
        'avg_monthly_balance', 'balance_volatility', 'min_balance_reached',
        'max_transaction_value', 'avg_transaction_value', 'total_monthly_burn_rate', 
        'essential_spending_ratio', 'lifestyle_spending_ratio', 'transaction_frequency', 
        'international_tx_indicator', 'device_diversity_score', 'ip_stability_ratio',
        'debt_indicator_ratio', 'cash_dependence_ratio', 'cash_flow_coverage_ratio', 
        'payment_to_income_reality_check', 'income_stability_proxy', 'previous_application_count'
    ]

    FRAUD_VECTOR_FEATURES: List[str] = [
        'applicant_age', 'monthly_income', 'cibil_score', 'loan_amount_requested',
        'employment_risk_val', 'loan_type_risk_val', 'number_of_dependents',
        'avg_tx_amount', 'max_tx_amount', 'intl_tx_count', 'unique_locations', 
        'unique_ips', 'unique_devices', 'unique_destinations', 'financial_service_spend',
        'max_ip_sharing_score', 'max_device_sharing_score', 'suspicious_notes_count',
        'failed_ratio', 'mule_indicator_ratio', 'intl_tx_ratio', 'avg_tx_velocity',
        'income_validation_ratio', 'loan_to_spend_ratio', 'midnight_app_flag'
    ]

    class Config:
        env_file = ".env"

SETTINGS = Settings()