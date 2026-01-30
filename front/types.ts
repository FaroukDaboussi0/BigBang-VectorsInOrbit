
export enum LoanStep {
  INTAKE = 1,
  ANALYSIS = 2,
  DECISION = 3
}

export enum DecisionResult {
  PENDING = 'PENDING',
  APPROVED = 'APPROVED',
  REJECTED = 'REJECTED',
  FRAUD = 'FRAUD'
}

export interface LoanApplication {
  id: string;
  applicant: {
    fullName: string;
    cinId: string;
    monthlyIncome: number;
    hasProperty: boolean;
  };
  loan: {
    purpose: string;
    amount: number;
    durationMonths: number;
  };
  documents: {
    cin: string | null;
    payslip: string | null;
    incomeTax: string | null;
    bankStatements: string | null;
    propertyTitle: string | null;
  };
  analysis: {
    riskScore: number;
    fraudProbability: number;
    similarityScore: number;
    aiExplanation: string;
    possibleImprovements?: string[];
    status: DecisionResult;
  };
  createdAt: string;
}

export const LOAN_PURPOSES = [
  'Personal Loan (قرض شخصي)',
  'Home Mortgage (قرض عقاري)',
  'Vehicle Purchase (قرض سيارة)',
  'Business Expansion (توسيع الأعمال)',
  'Education (قرض تعليمي)',
  'Refinancing (إعادة تمويل)'
];
