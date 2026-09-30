'use client';
import { useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Search, AlertTriangle, Fingerprint, ShieldAlert, CheckCircle2, FileSearch, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export default function InvestigatorPage() {
  const [analyzing, setAnalyzing] = useState(false);
  const [step, setStep] = useState(0);
  const [report, setReport] = useState<any>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const startAnalysis = async (e: any) => {
    const selected = e.target.files?.[0];
    if (!selected) return;

    setAnalyzing(true);
    setStep(1); // Uploading & Scanning
    setReport(null);
    setErrorMsg(null);
    
    try {
      const { api } = await import('@/lib/api');
      const formData = new FormData();
      formData.append('file', selected);
      
      // We simulate the pipeline steps in UI to match the backend process visually
      setTimeout(() => setStep(2), 1500); // Extracting watermark
      setTimeout(() => setStep(3), 3000); // Checking ML-DSA
      setTimeout(() => setStep(4), 4500); // Querying Ledger

      const res = await api.analyzeLeakedDoc(formData);
      
      setTimeout(() => {
        setStep(5);
        setReport(res);
      }, 6000);
      
    } catch (err: any) {
      console.error(err);
      setTimeout(() => {
        setStep(5);
        setErrorMsg("Attribution failed. No valid watermark found or signature verification failed.");
      }, 6000);
    }
  };

  const steps = [
    { label: 'Scanning Document...', icon: FileSearch },
    { label: 'Extracting Watermark Payload...', icon: Fingerprint },
    { label: 'Verifying Integrity (ML-DSA)...', icon: ShieldAlert },
    { label: 'Querying Ledger Blocks...', icon: Search },
    { label: 'Attribution Complete', icon: CheckCircle2 }
  ];

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex items-center space-x-4 border-b border-[#1E293B] pb-6">
        <div className="p-3 bg-[#F59E0B]/20 rounded-xl">
          <Search className="w-8 h-8 text-[#F59E0B]" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-white">Forensic Analysis Console</h1>
          <p className="text-[#94A3B8]">Analyze leaked documents for attribution</p>
        </div>
      </div>

      {!analyzing ? (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <input type="file" ref={fileInputRef} className="hidden" accept=".pdf" onChange={startAnalysis} />
          <Card className="border-red-500/30 shadow-[0_0_15px_rgba(239,68,68,0.15)]">
            <CardContent className="p-12 text-center">
              <AlertTriangle className="w-16 h-16 text-red-500 mx-auto mb-6" />
              <h2 className="text-2xl font-bold text-white mb-2">Upload Suspected Leak</h2>
              <p className="text-[#94A3B8] mb-8">Upload a leaked file to extract watermarks and trace the source.</p>
              
              <div 
                className="border-2 border-dashed border-red-500/50 bg-red-500/5 rounded-xl p-10 mb-6 cursor-pointer hover:bg-red-500/10 transition-colors" 
                onClick={() => fileInputRef.current?.click()}
              >
                <p className="text-red-400 font-medium">Click to Upload Leaked Document</p>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <Card>
            <CardHeader>
              <CardTitle>Analysis Pipeline</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              {steps.map((s, idx) => {
                const isActive = step === (idx + 1);
                const isPast = step > (idx + 1);
                const Icon = s.icon;
                
                return (
                  <motion.div 
                    key={idx}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: isPast || isActive ? 1 : 0.3, x: 0 }}
                    className={`flex items-center space-x-4 p-4 rounded-lg ${isActive ? 'bg-[#F59E0B]/10 border border-[#F59E0B]/30' : 'bg-[#1E293B]/50'}`}
                  >
                    <div className={`p-2 rounded-full ${isPast ? 'bg-[#10B981]/20 text-[#10B981]' : isActive ? 'bg-[#F59E0B]/20 text-[#F59E0B] animate-pulse' : 'bg-[#1E293B] text-[#94A3B8]'}`}>
                      <Icon className="w-5 h-5" />
                    </div>
                    <span className={`font-medium ${isActive ? 'text-[#F59E0B]' : isPast ? 'text-white' : 'text-[#94A3B8]'}`}>
                      {s.label}
                    </span>
                    {isPast && <CheckCircle2 className="w-5 h-5 text-[#10B981] ml-auto" />}
                  </motion.div>
                );
              })}
            </CardContent>
          </Card>

          <AnimatePresence>
            {step >= 5 && (
              <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} className="h-full">
                {report ? (
                  <Card className="border-[#10B981]/50 shadow-[0_0_30px_rgba(16,185,129,0.15)] h-full">
                    <CardHeader className="bg-[#10B981]/10 border-b border-[#10B981]/20">
                      <CardTitle className="text-[#10B981] flex items-center">
                        <ShieldAlert className="w-5 h-5 mr-2" /> Official Forensic Report
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-6 space-y-6">
                      <div className="text-center pb-6 border-b border-[#1E293B]">
                        <p className="text-sm text-[#94A3B8] uppercase tracking-wider mb-1">Attribution Status</p>
                        <h2 className="text-4xl font-black text-[#10B981] tracking-tight">CONFIRMED</h2>
                      </div>
                      
                      <div className="space-y-4">
                        <div className="flex justify-between items-center">
                          <span className="text-[#94A3B8]">Leaker Identity</span>
                          <span className="font-mono font-bold text-white bg-[#1E293B] px-3 py-1 rounded">{report.attributed_recipient_callsign || 'Unknown'}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[#94A3B8]">Session ID</span>
                          <span className="font-mono text-xs text-white truncate max-w-[200px]" title={report.matched_session_id}>{report.matched_session_id || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[#94A3B8]">Ledger Found</span>
                          {report.ledger_match ? <Badge variant="success">Yes</Badge> : <Badge variant="danger">No</Badge>}
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-[#94A3B8]">Signature Valid</span>
                          {report.signature_verified ? <Badge variant="success">Yes (ML-DSA)</Badge> : <Badge variant="danger">No</Badge>}
                        </div>
                      </div>

                      <Button variant="outline" className="w-full" onClick={() => { setAnalyzing(false); setStep(0); setReport(null); }}>
                        Reset Console
                      </Button>
                    </CardContent>
                  </Card>
                ) : (
                  <Card className="border-red-500/50 shadow-[0_0_30px_rgba(239,68,68,0.15)] h-full">
                    <CardHeader className="bg-red-500/10 border-b border-red-500/20">
                      <CardTitle className="text-red-500 flex items-center">
                        <XCircle className="w-5 h-5 mr-2" /> Attribution Failed
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="p-6 space-y-6">
                      <div className="text-center pb-6 border-b border-[#1E293B]">
                        <h2 className="text-xl font-bold text-red-500 mb-2">No Match Found</h2>
                        <p className="text-[#94A3B8]">{errorMsg}</p>
                      </div>
                      <Button variant="outline" className="w-full" onClick={() => { setAnalyzing(false); setStep(0); setErrorMsg(null); }}>
                        Try Another Document
                      </Button>
                    </CardContent>
                  </Card>
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}
