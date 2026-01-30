
import React, { useState, useEffect } from 'react';
import { FileText, User, CreditCard, Home, Landmark, Upload, Info, Loader2, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { LOAN_PURPOSES } from '../types';

interface DataIntakeFormProps {
  onComplete: (data: any) => void;
}

type DocStatus = 'idle' | 'processing' | 'success' | 'rejected';

interface DocItem {
  id: string;
  label: string;
  desc: string;
  status: DocStatus;
  error?: string;
}

const DataIntakeForm: React.FC<DataIntakeFormProps> = ({ onComplete }) => {
  const [formPart, setFormPart] = useState<1 | 2>(1);
  const [showTooltip, setShowTooltip] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    fullName: '',
    cinId: '',
    monthlyIncome: '',
    hasProperty: false,
    loanPurpose: LOAN_PURPOSES[0],
    loanAmount: '',
    repaymentMonths: '12'
  });

  const [docs, setDocs] = useState<Record<string, DocItem>>({
    cin: { id: 'cin', label: 'CIN Scanned Copy', desc: 'بطاقة تعريف وطنية', status: 'idle' },
    payslip: { id: 'payslip', label: 'Recent Payslip', desc: 'قسيمة الراتب', status: 'idle' },
    incomeTax: { id: 'incomeTax', label: 'Tax Declaration', desc: 'تصريح بالدخل', status: 'idle' },
    bankStatements: { id: 'bankStatements', label: '6 Mo Bank Statements', desc: 'كشف بنكي', status: 'idle' },
    propertyTitle: { id: 'propertyTitle', label: 'Property Certificate', desc: 'شهادة ملكية', status: 'idle' }
  });

  const handleFileChange = (id: string) => {
    // Set to processing
    setDocs(prev => ({
      ...prev,
      [id]: { ...prev[id], status: 'processing' }
    }));

    // Simulate verification and extraction
    setTimeout(() => {
      setDocs(prev => {
        const isTax = id === 'incomeTax';
        return {
          ...prev,
          [id]: { 
            ...prev[id], 
            status: isTax ? 'rejected' : 'success',
            error: isTax ? 'Document illegible or stamp missing. Please provide a certified copy with visible fiscal stamps.' : undefined
          }
        };
      });
    }, 2500);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formPart === 1) {
      setFormPart(2);
    } else {
      onComplete({
        applicant: {
          fullName: formData.fullName,
          cinId: formData.cinId,
          monthlyIncome: parseFloat(formData.monthlyIncome),
          hasProperty: formData.hasProperty
        },
        loan: {
          purpose: formData.loanPurpose,
          amount: parseFloat(formData.loanAmount),
          durationMonths: parseInt(formData.repaymentMonths)
        },
        documents: Object.keys(docs).reduce((acc, key) => ({...acc, [key]: docs[key].status === 'success'}), {})
      });
    }
  };

  const renderDocStatus = (doc: DocItem) => {
    switch (doc.status) {
      case 'idle':
        return (
          <label className="cursor-pointer px-3 py-1.5 rounded-md text-xs font-bold transition-all bg-gray-100 text-gray-600 hover:bg-emerald-50">
            <input type="file" className="hidden" onChange={() => handleFileChange(doc.id)} />
            UPLOAD
          </label>
        );
      case 'processing':
        return (
          <div className="flex items-center gap-2 text-emerald-600 font-bold text-xs">
            <Loader2 size={16} className="animate-spin" />
            VERIFYING...
          </div>
        );
      case 'success':
        return (
          <div className="flex items-center gap-1 text-emerald-600 font-bold text-xs bg-emerald-50 px-2 py-1 rounded">
            <CheckCircle2 size={14} />
            EXTRACTED
          </div>
        );
      case 'rejected':
        return (
          <div className="flex items-center gap-2 relative">
            <div className="flex items-center gap-1 text-red-600 font-bold text-xs bg-red-50 px-2 py-1 rounded">
              <XCircle size={14} />
              REJECTED
            </div>
            <button 
              type="button"
              onMouseEnter={() => setShowTooltip(doc.id)}
              onMouseLeave={() => setShowTooltip(null)}
              onClick={() => setShowTooltip(showTooltip === doc.id ? null : doc.id)}
              className="text-gray-400 hover:text-red-500 transition-colors"
            >
              <Info size={16} />
            </button>
            {showTooltip === doc.id && (
              <div className="absolute right-0 top-8 z-50 w-64 bg-white shadow-xl border border-red-100 rounded-lg p-3 text-xs text-red-800 animate-in fade-in zoom-in duration-200">
                <p className="font-bold mb-1">OCR Analysis Failed</p>
                <p className="leading-relaxed">{doc.error}</p>
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className="max-w-4xl mx-auto bg-white rounded-2xl shadow-xl overflow-hidden border border-gray-100">
      <div className="bg-emerald-600 px-8 py-6 text-white flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Layer 1 – Data Intake</h2>
          <p className="text-emerald-100 opacity-90">
            {formPart === 1 ? 'Form 1: Personal Information (Informations Personnelles)' : 'Form 2: Loan Information (Informations sur le Crédit)'}
          </p>
        </div>
        <div className="bg-emerald-700/50 px-3 py-1 rounded-full text-xs font-medium uppercase tracking-wider">
          Step {formPart} of 2
        </div>
      </div>

      <form onSubmit={handleSubmit} className="p-8">
        {formPart === 1 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <User size={20} className="text-emerald-600" />
                Applicant Identity
              </h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                <input 
                  required
                  type="text" 
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="Mohamed Ben Ali"
                  value={formData.fullName}
                  onChange={e => setFormData({...formData, fullName: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  CIN / National ID <span className="text-xs text-gray-400 font-arabic">(بطاقة تعريف وطنية)</span>
                </label>
                <input 
                  required
                  type="text" 
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="00000000"
                  value={formData.cinId}
                  onChange={e => setFormData({...formData, cinId: e.target.value})}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Monthly Net Income (TND)</label>
                <input 
                  required
                  type="number" 
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                  placeholder="2500"
                  value={formData.monthlyIncome}
                  onChange={e => setFormData({...formData, monthlyIncome: e.target.value})}
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <input 
                  type="checkbox" 
                  id="property"
                  className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  checked={formData.hasProperty}
                  onChange={e => setFormData({...formData, hasProperty: e.target.checked})}
                />
                <label htmlFor="property" className="text-sm text-gray-700 font-medium cursor-pointer">
                  Owns Property <span className="text-xs text-gray-400 font-arabic">(شهادة ملكية)</span>
                </label>
              </div>
            </div>

            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <Upload size={20} className="text-emerald-600" />
                Multimodal Document Intake
              </h3>
              
              <div className="space-y-3">
                {/* FIX: Explicitly cast Object.values(docs) to DocItem[] to avoid TS unknown type error */}
                {(Object.values(docs) as DocItem[]).map((doc) => (
                  <div key={doc.id} className="flex items-center justify-between p-3 border border-dashed border-gray-300 rounded-lg hover:bg-gray-50 transition-colors">
                    <div>
                      <p className="text-sm font-medium text-gray-800">{doc.label}</p>
                      <p className="text-xs text-gray-400 font-arabic">{doc.desc}</p>
                    </div>
                    {/* FIX: doc is now correctly typed as DocItem */}
                    {renderDocStatus(doc)}
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="max-w-xl mx-auto space-y-6 py-4">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <CreditCard size={20} className="text-emerald-600" />
              Loan Specifications
            </h3>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Loan Purpose</label>
              <select 
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none"
                value={formData.loanPurpose}
                onChange={e => setFormData({...formData, loanPurpose: e.target.value})}
              >
                {LOAN_PURPOSES.map(p => <option key={p} value={p}>{p}</option>)}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Requested Amount (Tunisian Dinars - TND)</label>
              <div className="relative">
                <input 
                  required
                  type="number" 
                  className="w-full pl-12 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 outline-none text-xl font-bold"
                  placeholder="50000"
                  value={formData.loanAmount}
                  onChange={e => setFormData({...formData, loanAmount: e.target.value})}
                />
                <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 font-bold border-r pr-3">DT</div>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Repayment Duration (Months)</label>
              <div className="flex gap-4">
                {[12, 24, 36, 48, 60, 72].map(m => (
                  <button
                    key={m}
                    type="button"
                    onClick={() => setFormData({...formData, repaymentMonths: m.toString()})}
                    className={`flex-1 py-2 rounded-lg border font-medium transition-all ${
                      formData.repaymentMonths === m.toString()
                        ? 'bg-emerald-600 border-emerald-600 text-white shadow-md'
                        : 'bg-white border-gray-200 text-gray-600 hover:border-emerald-300'
                    }`}
                  >
                    {m}m
                  </button>
                ))}
              </div>
            </div>

            <div className="bg-emerald-50 rounded-xl p-4 flex gap-4 border border-emerald-100">
              <Info className="text-emerald-600 shrink-0" size={24} />
              <div className="text-sm text-emerald-800">
                <p className="font-bold">Estimated Monthly Installment</p>
                <p className="text-lg">
                  {formData.loanAmount && formData.repaymentMonths 
                    ? (parseFloat(formData.loanAmount) / parseInt(formData.repaymentMonths) * 1.08).toFixed(2) 
                    : '0.00'} TND
                </p>
                <p className="text-xs opacity-75 mt-1">*Incl. approx 8% TMM+ margin</p>
              </div>
            </div>
          </div>
        )}

        <div className="mt-10 flex gap-4">
          {formPart === 2 && (
            <button 
              type="button"
              onClick={() => setFormPart(1)}
              className="px-8 py-3 bg-gray-100 text-gray-700 font-bold rounded-xl hover:bg-gray-200 transition-colors"
            >
              Back
            </button>
          )}
          <button 
            type="submit"
            className="flex-1 py-3 bg-emerald-600 text-white font-bold rounded-xl hover:bg-emerald-700 transition-all shadow-lg hover:shadow-xl active:scale-95"
          >
            {formPart === 1 ? 'Continue to Loan Info' : 'Initiate AI Analysis Pipeline'}
          </button>
        </div>
      </form>
    </div>
  );
};

export default DataIntakeForm;
