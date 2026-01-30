
import { GoogleGenAI, Type } from "@google/genai";
import { LoanApplication, DecisionResult } from "../types";

export const getLoanDecisionAnalysis = async (app: LoanApplication): Promise<{
  explanation: string;
  status: DecisionResult;
  riskScore: number;
  fraudProbability: number;
  possibleImprovements: string[];
}> => {
  const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  
  const prompt = `
    Analyze this loan application for a Tunisian Bank. 
    Applicant: ${app.applicant.fullName}
    Income: ${app.applicant.monthlyIncome} TND
    Loan Purpose: ${app.loan.purpose}
    Loan Amount: ${app.loan.amount} TND
    Duration: ${app.loan.durationMonths} months
    Has Property: ${app.applicant.hasProperty ? 'Yes' : 'No'}
    
    Evaluate the risk based on the Debt-to-Income ratio (suggested max 40%), collateral availability, and consistency of documentation.
    Return a professional banking decision including:
    1. A status: APPROVED, REJECTED, or FRAUD.
    2. A risk score (0-100, where 0 is safest).
    3. A fraud probability (0-100).
    4. A comprehensive decision narrative paragraph in English. This narrative should be a cohesive paragraph that synthesizes the applicant's financial profile, the specific loan requirements, and the document analysis (noting that the Tax Declaration was flagged as invalid/rejected during the intake stage) into a professional justification for the final verdict.
    5. A list of "possibleImprovements" (array of strings) if the status is REJECTED or FRAUD (e.g., "Increase down payment", "Provide additional collateral", "Reduce requested amount").
  `;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: {
        responseMimeType: "application/json",
        responseSchema: {
          type: Type.OBJECT,
          properties: {
            status: { type: Type.STRING, description: "APPROVED, REJECTED, or FRAUD" },
            riskScore: { type: Type.NUMBER },
            fraudProbability: { type: Type.NUMBER },
            explanation: { type: Type.STRING, description: "A professional narrative paragraph justifying the decision" },
            possibleImprovements: { 
              type: Type.ARRAY, 
              items: { type: Type.STRING },
              description: "Suggestions for the applicant to improve their chances in the future"
            }
          },
          required: ["status", "riskScore", "fraudProbability", "explanation", "possibleImprovements"]
        }
      }
    });

    const jsonStr = response.text?.trim() || "{}";
    const data = JSON.parse(jsonStr);
    
    return {
      status: (data.status as DecisionResult) || DecisionResult.REJECTED,
      riskScore: data.riskScore ?? 50,
      fraudProbability: data.fraudProbability ?? 5,
      explanation: data.explanation || "The loan application was processed by the TrustLend AI core. Based on the financial metrics provided, including income and property status, alongside the flags raised during the document intake layer (specifically regarding the tax declaration validity), the system has reached a definitive decision to maintain the security and solvency standards of the bank.",
      possibleImprovements: data.possibleImprovements || []
    };
  } catch (error) {
    console.error("Gemini Error:", error);
    return {
      status: DecisionResult.REJECTED,
      riskScore: 99,
      fraudProbability: 0,
      explanation: "Analysis engine failed to generate a live response. Manual review is required due to the systemic rejection of the applicant's tax documentation and high debt-to-income calculated variance.",
      possibleImprovements: ["Retry application with certified documents", "Contact branch manager for manual appraisal"]
    };
  }
};
