
import React, { useEffect, useState } from 'react';
import { ShieldCheck, Search, Activity, Database, AlertTriangle, Zap } from 'lucide-react';

interface AIAnalysisViewProps {
  onAnalysisComplete: () => void;
}

const AIAnalysisView: React.FC<AIAnalysisViewProps> = ({ onAnalysisComplete }) => {
  const [activeStep, setActiveStep] = useState(0);

  const steps = [
    { label: "Document Verification", icon: ShieldCheck, detail: "Validating CIN and Tunisian Tax ID format..." },
    { label: "Fraud Pattern Detection", icon: Search, detail: "Checking for anomalies in bank statement history..." },
    { label: "Historical Case Matching", icon: Database, detail: "Querying vector database for similar profiles (N-Case Similarity)..." },
    { label: "Predictive Risk Scoring", icon: Activity, detail: "Calculating debt-to-income and solvency probability..." },
    { label: "LLM Explanation Logic", icon: Zap, detail: "Synthesizing natural language reasoning for decision transparency..." }
  ];

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep(prev => {
        if (prev < steps.length - 1) return prev + 1;
        clearInterval(timer);
        // Add a small delay for final satisfaction
        setTimeout(onAnalysisComplete, 1500);
        return prev;
      });
    }, 2000);

    return () => clearInterval(timer);
  }, []);

  return (
    <div className="max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-emerald-900 mb-2">Layer 2 – AI Analysis & Validation</h2>
        <p className="text-gray-500">Processing multimodal data through TrustLend Intelligence Core</p>
      </div>

      <div className="bg-gray-900 rounded-3xl p-8 shadow-2xl relative overflow-hidden border-4 border-emerald-900/30">
        {/* Background circuit-like patterns */}
        <div className="absolute inset-0 opacity-10 pointer-events-none">
          <svg className="w-full h-full" viewBox="0 0 100 100">
            <path d="M 0 10 L 20 10 L 25 20 L 50 20 L 55 30 L 80 30" fill="none" stroke="white" strokeWidth="0.5" />
            <path d="M 100 90 L 80 90 L 75 80 L 50 80 L 45 70 L 20 70" fill="none" stroke="white" strokeWidth="0.5" />
            <circle cx="50" cy="50" r="10" fill="none" stroke="white" strokeWidth="0.5" />
          </svg>
        </div>

        <div className="relative z-10 space-y-6">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            const isCompleted = activeStep > idx;
            const isActive = activeStep === idx;
            const isWaiting = activeStep < idx;

            return (
              <div 
                key={idx}
                className={`flex items-start gap-6 p-5 rounded-2xl transition-all duration-700 transform ${
                  isActive ? 'bg-emerald-600/20 scale-[1.02] border border-emerald-500/50' : isCompleted ? 'opacity-60' : 'opacity-20 translate-y-4'
                }`}
              >
                <div className={`shrink-0 w-12 h-12 rounded-xl flex items-center justify-center ${
                  isActive ? 'bg-emerald-500 text-white animate-pulse shadow-lg shadow-emerald-500/50' : isCompleted ? 'bg-emerald-900 text-emerald-400' : 'bg-gray-800 text-gray-600'
                }`}>
                  <Icon size={24} />
                </div>
                
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className={`font-bold text-lg ${isActive ? 'text-emerald-400' : 'text-white'}`}>
                      {step.label}
                    </h3>
                    {isCompleted && (
                      <span className="text-xs font-bold text-emerald-400 bg-emerald-400/10 px-2 py-0.5 rounded border border-emerald-400/20">VERIFIED</span>
                    )}
                    {isActive && (
                      <div className="flex gap-1">
                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '200ms' }}></div>
                        <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-bounce" style={{ animationDelay: '400ms' }}></div>
                      </div>
                    )}
                  </div>
                  <p className={`text-sm ${isActive ? 'text-emerald-200/80' : 'text-gray-400'}`}>
                    {step.detail}
                  </p>
                  
                  {isActive && (
                    <div className="mt-4 w-full bg-gray-800 h-1.5 rounded-full overflow-hidden">
                      <div className="h-full bg-emerald-500 animate-[loading_2s_ease-in-out_infinite]"></div>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <style>{`
        @keyframes loading {
          0% { width: 0; }
          50% { width: 70%; }
          100% { width: 100%; }
        }
      `}</style>
    </div>
  );
};

export default AIAnalysisView;
