
import React, { useState } from 'react';
import { LoanStep, LoanApplication, DecisionResult } from './types';
import { getLoanDecisionAnalysis } from './services/geminiService';
import PipelineStepper from './components/PipelineStepper';
import DataIntakeForm from './components/DataIntakeForm';
import AIAnalysisView from './components/AIAnalysisView';
import DecisionView from './components/DecisionView';
import { Shield, LayoutDashboard, History, Settings, LogOut, Search } from 'lucide-react';

const App: React.FC = () => {
  const [step, setStep] = useState<LoanStep>(LoanStep.INTAKE);
  const [application, setApplication] = useState<LoanApplication | null>(null);
  const [loading, setLoading] = useState(false);

  const handleIntakeComplete = async (data: any) => {
    setLoading(true);
    const initialApp: LoanApplication = {
      id: Math.random().toString(36).substring(7).toUpperCase(),
      ...data,
      analysis: {
        riskScore: 0,
        fraudProbability: 0,
        similarityScore: 0,
        aiExplanation: '',
        status: DecisionResult.PENDING
      },
      createdAt: new Date().toISOString()
    };
    
    setApplication(initialApp);
    setStep(LoanStep.ANALYSIS);
  };

  const handleAnalysisComplete = async () => {
    if (!application) return;

    try {
      const result = await getLoanDecisionAnalysis(application);
      setApplication({
        ...application,
        analysis: {
          ...application.analysis,
          ...result
        }
      });
      setStep(LoanStep.DECISION);
    } catch (error) {
      console.error(error);
      setStep(LoanStep.DECISION);
    } finally {
      setLoading(false);
    }
  };

  const resetFlow = () => {
    setStep(LoanStep.INTAKE);
    setApplication(null);
  };

  return (
    <div className="min-h-screen flex flex-col md:flex-row bg-slate-50">
      {/* Sidebar - Desktop Only */}
      <aside className="hidden md:flex flex-col w-64 bg-emerald-900 text-white h-screen sticky top-0">
        <div className="p-8 flex items-center gap-3">
          <div className="bg-emerald-500 p-2 rounded-xl">
            <Shield size={28} />
          </div>
          <span className="text-xl font-bold tracking-tight">TrustLend</span>
        </div>

        <nav className="flex-1 px-4 space-y-2">
          <button className="w-full flex items-center gap-3 px-4 py-3 bg-emerald-800 rounded-xl text-emerald-100 font-medium">
            <LayoutDashboard size={20} /> Dashboard
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 hover:bg-emerald-800/50 rounded-xl text-emerald-100/70 font-medium transition-colors">
            <History size={20} /> History
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 hover:bg-emerald-800/50 rounded-xl text-emerald-100/70 font-medium transition-colors">
            <Search size={20} /> Search Cases
          </button>
          <button className="w-full flex items-center gap-3 px-4 py-3 hover:bg-emerald-800/50 rounded-xl text-emerald-100/70 font-medium transition-colors">
            <Settings size={20} /> System Config
          </button>
        </nav>

        <div className="p-6 border-t border-emerald-800">
          <button className="w-full flex items-center gap-3 px-4 py-3 text-emerald-300/60 font-medium hover:text-white transition-colors">
            <LogOut size={20} /> Log Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto">
        {/* Header */}
        <header className="bg-white border-b border-gray-100 px-8 py-4 flex justify-between items-center sticky top-0 z-50">
          <div className="md:hidden flex items-center gap-2">
            <div className="bg-emerald-500 p-1.5 rounded-lg text-white">
              <Shield size={20} />
            </div>
            <span className="font-bold text-emerald-900">TrustLend</span>
          </div>
          <h1 className="text-lg font-bold text-gray-800 hidden md:block">Agent Workspace: Loan Decision Intelligence</h1>
          
          <div className="flex items-center gap-4">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-bold text-gray-900">Amira Mansour</p>
              <p className="text-xs text-emerald-600">Senior Credit Agent</p>
            </div>
            <img 
              src="https://picsum.photos/seed/agent/100/100" 
              alt="Agent" 
              className="w-10 h-10 rounded-full border-2 border-emerald-100"
            />
          </div>
        </header>

        {/* Pipeline Stepper Container */}
        <div className="max-w-6xl mx-auto px-6 py-4">
          <PipelineStepper currentStep={step} />
        </div>

        {/* Content Stages */}
        <div className="max-w-6xl mx-auto px-6 pb-12">
          {step === LoanStep.INTAKE && (
            <DataIntakeForm onComplete={handleIntakeComplete} />
          )}

          {step === LoanStep.ANALYSIS && (
            <AIAnalysisView onAnalysisComplete={handleAnalysisComplete} />
          )}

          {step === LoanStep.DECISION && application && (
            <DecisionView application={application} onReset={resetFlow} />
          )}
        </div>

        {/* Footer/Stats Bar */}
        <footer className="bg-white border-t border-gray-100 px-8 py-4 flex justify-between items-center text-xs text-gray-400 font-medium">
          <p>© 2024 TrustLend Decision Intelligence. All rights reserved.</p>
          <div className="flex gap-4">
            <span>Uptime: 99.9%</span>
            <span className="text-emerald-500">Secure AES-256 Connection</span>
          </div>
        </footer>
      </main>
    </div>
  );
};

export default App;
