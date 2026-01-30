
import React from 'react';
import { LoanStep } from '../types';
import { Database, Zap, CheckCircle } from 'lucide-react';

interface PipelineStepperProps {
  currentStep: LoanStep;
}

const PipelineStepper: React.FC<PipelineStepperProps> = ({ currentStep }) => {
  const steps = [
    { id: LoanStep.INTAKE, label: 'Data Intake', sub: 'Multimodal Input', icon: Database },
    { id: LoanStep.ANALYSIS, label: 'AI Analysis', sub: 'Neural Processing', icon: Zap },
    { id: LoanStep.DECISION, label: 'Decision Output', sub: 'Final Verdict', icon: CheckCircle },
  ];

  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between relative max-w-4xl mx-auto">
        <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gray-200 -translate-y-1/2 z-0"></div>
        <div 
          className="absolute top-1/2 left-0 h-0.5 bg-emerald-500 -translate-y-1/2 transition-all duration-500 z-0"
          style={{ width: `${((currentStep - 1) / (steps.length - 1)) * 100}%` }}
        ></div>
        
        {steps.map((step) => {
          const Icon = step.icon;
          const isActive = currentStep === step.id;
          const isCompleted = currentStep > step.id;
          
          return (
            <div key={step.id} className="relative z-10 flex flex-col items-center">
              <div 
                className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 border-2 ${
                  isActive 
                    ? 'bg-emerald-600 border-emerald-600 text-white shadow-lg scale-110' 
                    : isCompleted 
                      ? 'bg-emerald-500 border-emerald-500 text-white' 
                      : 'bg-white border-gray-300 text-gray-400'
                }`}
              >
                <Icon size={24} />
              </div>
              <div className="mt-3 text-center">
                <p className={`text-sm font-bold ${isActive || isCompleted ? 'text-emerald-900' : 'text-gray-500'}`}>
                  {step.label}
                </p>
                <p className="text-xs text-gray-400 hidden md:block">{step.sub}</p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default PipelineStepper;
