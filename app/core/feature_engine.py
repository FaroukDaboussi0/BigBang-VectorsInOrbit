import pandas as pd
import numpy as np
from typing import List, Dict, Any
from app.models.pydantic_models import PipelineRequest, TransactionInput
from app.models.domain_models import ExtractedFeatureSet
import joblib # To load our pre-fitted scalers
from app.core.config import SETTINGS

class FeatureEngine:
    def __init__(self, risk_scaler_path: str, fraud_scaler_path: str):
        # Load the scalers we saved during the training phase
        self.risk_scaler = joblib.load(risk_scaler_path)
        self.fraud_scaler = joblib.load(fraud_scaler_path)
        
        # Define the strict order of features for the vectors
        # (Must match the order used during Qdrant collection setup)
        self.risk_feature_order = SETTINGS.RISK_VECTOR_FEATURES

        self.fraud_feature_order = SETTINGS.FRAUD_VECTOR_FEATURES

    def create_feature_set(self, request: PipelineRequest, ip_density_map: Dict, device_density_map: Dict) -> ExtractedFeatureSet:
        """
        Main entry point: PipelineRequest -> ExtractedFeatureSet
        """
        # 1. Convert to DataFrames
        loan_data = request.application.dict()
        tx_list = [tx.dict() for tx in request.transactions]
        tx_df = pd.DataFrame(tx_list)
        
        # 2. Extract Features
        all_features = self._run_engineering(loan_data, tx_df, ip_density_map, device_density_map)
        
        # 3. Generate Scaled Vectors
        risk_vec = self._generate_vector(all_features, self.risk_feature_order, self.risk_scaler)
        fraud_vec = self._generate_vector(all_features, self.fraud_feature_order, self.fraud_scaler)
        
        return ExtractedFeatureSet(
            application_id=request.application.application_id,
            customer_id=request.application.customer_id,
            all_features=all_features,
            risk_vector=risk_vec,
            fraud_vector=fraud_vec
        )

    def _run_engineering(self, loan: Dict, tx_df: pd.DataFrame, ip_map: Dict, dev_map: Dict) -> Dict[str, Any]:
        """The actual logic for all 50+ features"""
        d = loan.copy()
        
        # --- Transactional Aggregates ---
        if not tx_df.empty:
            tx_df['transaction_date'] = pd.to_datetime(tx_df['transaction_date'])
            total_spent = tx_df['transaction_amount'].sum()
            avg_tx = tx_df['transaction_amount'].mean()
            total_months = max(tx_df['transaction_date'].dt.to_period('M').nunique(), 1)

            # Category Logic
            essential_cats = ['Utilities', 'Healthcare', 'Groceries', 'Education', 'Fuel']
            lifestyle_cats = ['Dining', 'Travel', 'Entertainment', 'Online Shopping', 'Electronics']
            
            essential_val = tx_df[tx_df['merchant_category'].isin(essential_cats)]['transaction_amount'].sum()
            lifestyle_val = tx_df[tx_df['merchant_category'].isin(lifestyle_cats)]['transaction_amount'].sum()
            debt_val = tx_df[tx_df['merchant_category'] == 'Financial Services']['transaction_amount'].sum()
            cash_val = tx_df[tx_df['merchant_category'] == 'Cash Withdrawal']['transaction_amount'].sum()

            # Risk Engineered
            d['avg_monthly_balance'] = tx_df['account_balance_after_transaction'].mean()
            d['balance_volatility'] = tx_df['account_balance_after_transaction'].std()
            d['total_monthly_burn_rate'] = total_spent / total_months
            d['essential_spending_ratio'] = essential_val / (total_spent + 1)
            d['lifestyle_spending_ratio'] = lifestyle_val / (total_spent + 1)
            d['transaction_frequency'] = len(tx_df) / total_months
            d['international_tx_indicator'] = tx_df['is_international_transaction'].sum()
            d['device_diversity_score'] = tx_df['device_used'].nunique()
            d['ip_stability_ratio'] = (tx_df['ip_address'].nunique()) / (d['transaction_frequency'] + 0.0001)
            d['debt_indicator_ratio'] = debt_val / (total_spent + 1)
            d['cash_dependence_ratio'] = cash_val / (total_spent + 1)
            d['min_balance_reached'] = tx_df['account_balance_after_transaction'].min()
            d['max_transaction_value'] = tx_df['transaction_amount'].max()
            d['avg_transaction_value'] = tx_df['transaction_amount'].mean()
            
            # Fraud Engineered
            d['avg_tx_amount'] = avg_tx
            d['max_tx_amount'] = tx_df['transaction_amount'].max()
            d['intl_tx_count'] = tx_df['is_international_transaction'].sum()
            d['unique_locations'] = tx_df['transaction_location'].nunique()
            d['unique_ips'] = tx_df['ip_address'].nunique()
            d['unique_devices'] = tx_df['device_used'].nunique()
            d['unique_destinations'] = tx_df['transaction_source_destination'].nunique()
            d['financial_service_spend'] = debt_val
            d['max_ip_sharing_score'] = tx_df['ip_address'].map(ip_map).max() if ip_map else 1
            d['max_device_sharing_score'] = tx_df['device_used'].map(dev_map).max() if dev_map else 1
            d['suspicious_notes_count'] = tx_df['transaction_notes'].str.contains('Test|Refund|Verify|Cash', case=False).sum()
            d['failed_ratio'] = (tx_df['transaction_status'] == 'Failed').sum() / (len(tx_df) + 1)
            d['mule_indicator_ratio'] = d['unique_destinations'] / (len(tx_df) + 1)
            d['intl_tx_ratio'] = d['intl_tx_count'] / (len(tx_df) + 1)
            d['avg_tx_velocity'] = len(tx_df) / 30
            d['income_validation_ratio'] = d['monthly_income'] / (avg_tx + 1)
            d['loan_to_spend_ratio'] = d['loan_amount_requested'] / (total_spent + 1)
        else:
            d['min_balance_reached'] = 0
            d['max_transaction_value'] = 0
            d['avg_transaction_value'] = 0
            # Fallback for 0 transactions
            for feat in ['avg_monthly_balance', 'balance_volatility', 'total_monthly_burn_rate', 'essential_spending_ratio']:
                d[feat] = 0

        # --- Loan Engineering (Static) ---
        est_emi = (d['loan_amount_requested'] / d['loan_tenure_months']) * 1.1
        d['loan_to_income_ratio'] = d['loan_amount_requested'] / (d['monthly_income'] * 12 + 1)
        d['installment_to_income_ratio'] = (d['existing_emis_monthly'] + est_emi) / (d['monthly_income'] + 1)
        d['disposable_income'] = d['monthly_income'] - d['existing_emis_monthly']
        d['age_at_loan_end'] = d['applicant_age'] + (d['loan_tenure_months'] / 12)
        d['income_per_dependent'] = d['monthly_income'] / (d['number_of_dependents'] + 1)
        d['cash_flow_coverage_ratio'] = d.get('avg_monthly_balance', 0) / (d.get('total_monthly_burn_rate', 0) + 1)
        d['payment_to_income_reality_check'] = (essential_val if 'essential_val' in locals() else 0) / (d['monthly_income'] + 1)
        d['income_stability_proxy'] = d.get('balance_volatility', 0) / (d.get('avg_monthly_balance', 0) + 1)

        # --- Encoding ---
        d['gender_val'] = {'Male': 0, 'Female': 1, 'Other': 0.5}.get(d['gender'], 0)
        d['property_val'] = {'Rented': 0, 'Jointly Owned': 0.5, 'Owned': 1}.get(d['property_ownership_status'], 0)
        d['cibil_category_val'] = 0 if d['cibil_score'] <= 600 else 0.33 if d['cibil_score'] <= 700 else 0.66 if d['cibil_score'] <= 800 else 1.0
        d['employment_risk_val'] = {'Salaried': 0.2, 'Business Owner': 0.4, 'Self-Employed': 0.6, 'Student': 0.8, 'Unemployed': 1.0, 'Retired': 0.1}.get(d['employment_status'], 0.5)
        d['loan_type_risk_val'] = {'Home Loan': 0.1, 'Car Loan': 0.2, 'Education Loan': 0.4, 'Business Loan': 0.7, 'Personal Loan': 0.9}.get(d['loan_type'], 0.5)
        d['midnight_app_flag'] = 1 if 0 <= pd.to_datetime(d['application_date']).hour <= 5 else 0
        d['previous_application_count'] = 1 # Incremented during finalization

        return d

    def _generate_vector(self, feature_dict: Dict, order: List[str], scaler: Any) -> List[float]:
        """Scales and orders features into a flat list of floats"""
        vals = []
        for feat in order:
            val = feature_dict.get(feat, 0)
            if pd.isna(val) or np.isinf(val):
                val = 0
            vals.append(val)
        
        # Reshape for scaler (1, -1) and return as flat list
        scaled_vals = scaler.transform([vals])[0]
        return scaled_vals.tolist()