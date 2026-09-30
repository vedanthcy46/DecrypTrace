'use client';
import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Upload, Lock, FileText, CheckCircle2 } from 'lucide-react';

export default function SenderPage() {
  const [step, setStep] = useState(1);
  const [file, setFile] = useState<File | null>(null);
  const [docId, setDocId] = useState<string | null>(null);
  const [recipients, setRecipients] = useState<any[]>([]);
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (step === 2) {
      loadRecipients();
    }
  }, [step]);

  const loadRecipients = async () => {
    try {
      const { api } = await import('@/lib/api');
      const data = await api.listRecipients();
      setRecipients(data || []);
    } catch (err) {
      console.error('Failed to load recipients', err);
    }
  };

  const handleFileSelect = async (e: any) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      setLoading(true);
      try {
        const { api } = await import('@/lib/api');
        const formData = new FormData();
        formData.append('file', selected);
        const res = await api.uploadDocument(formData);
        setDocId(res.id);
        setStep(2);
      } catch (err) {
        console.error(err);
        alert('Upload failed');
      }
      setLoading(false);
    }
  };

  const toggleRecipient = (id: string) => {
    setSelectedRecipients(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const handleEncrypt = async () => {
    if (!docId || selectedRecipients.length === 0) return;
    setLoading(true);
    try {
      const { api } = await import('@/lib/api');
      await api.encryptDocument(docId, {
        recipient_ids: selectedRecipients,
        require_watermark: true
      });
      setStep(3);
    } catch (err) {
      console.error(err);
      alert('Encryption failed');
    }
    setLoading(false);
  };

  return (
    <div className="space-y-8 max-w-4xl mx-auto">
      <div className="flex items-center space-x-4 border-b border-[#1E293B] pb-6">
        <div className="p-3 bg-[#8B5CF6]/20 rounded-xl">
          <Lock className="w-8 h-8 text-[#8B5CF6]" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-white">Sender Console</h1>
          <p className="text-[#94A3B8]">Upload and encrypt documents securely</p>
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Document Encryption Pipeline</CardTitle>
        </CardHeader>
        <CardContent>
          {step === 1 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <input type="file" ref={fileInputRef} className="hidden" accept=".pdf" onChange={handleFileSelect} />
              <div 
                className={`border-2 border-dashed border-[#8B5CF6]/30 bg-[#8B5CF6]/5 rounded-xl p-12 text-center transition-colors cursor-pointer ${loading ? 'opacity-50' : 'hover:bg-[#8B5CF6]/10'}`} 
                onClick={() => !loading && fileInputRef.current?.click()}
              >
                <Upload className="w-12 h-12 text-[#8B5CF6] mx-auto mb-4" />
                <h3 className="text-lg font-medium text-white">{loading ? 'Uploading...' : 'Click to Upload Document'}</h3>
                <p className="text-sm text-[#94A3B8] mt-2">Support for PDF only in this prototype</p>
                <Button variant="sender" className="mt-6" disabled={loading}>{loading ? 'Uploading...' : 'Select File'}</Button>
              </div>
            </motion.div>
          )}

          {step === 2 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-6">
              <div className="flex items-center p-4 bg-[#1E293B] rounded-lg">
                <FileText className="w-6 h-6 text-[#3B82F6] mr-4" />
                <div className="flex-1">
                  <p className="font-medium">{file?.name}</p>
                  <p className="text-sm text-[#94A3B8]">{(file?.size! / 1024 / 1024).toFixed(2)} MB</p>
                </div>
                <Badge variant="success">Uploaded</Badge>
              </div>

              <div>
                <h3 className="text-sm font-medium text-[#94A3B8] mb-3">Select Authorized Recipients</h3>
                <div className="grid grid-cols-2 gap-4">
                  {recipients.length === 0 && <p className="text-sm text-yellow-500">No recipients registered. Go to Recipient tab to generate keys first.</p>}
                  {recipients.map(agent => (
                    <div 
                      key={agent.id} 
                      onClick={() => toggleRecipient(agent.id)}
                      className={`flex items-center space-x-3 p-3 border rounded-lg cursor-pointer transition-colors ${selectedRecipients.includes(agent.id) ? 'border-[#8B5CF6] bg-[#8B5CF6]/10' : 'border-[#1E293B] hover:border-[#8B5CF6]/50'}`}
                    >
                      <input type="checkbox" checked={selectedRecipients.includes(agent.id)} readOnly className="accent-[#8B5CF6]" />
                      <span>{agent.callsign}</span>
                    </div>
                  ))}
                </div>
              </div>

              <Button variant="sender" className="w-full" onClick={handleEncrypt} disabled={loading || selectedRecipients.length === 0}>
                <Lock className="w-4 h-4 mr-2" /> {loading ? 'Encrypting...' : 'Encrypt & Store'}
              </Button>
            </motion.div>
          )}

          {step === 3 && (
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="text-center py-12">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#10B981]/20 mb-6">
                <CheckCircle2 className="w-8 h-8 text-[#10B981]" />
              </div>
              <h3 className="text-2xl font-bold text-white mb-2">Encryption Complete</h3>
              <p className="text-[#94A3B8] mb-6">Document has been encrypted and secured via ML-KEM.</p>
              <Button variant="outline" onClick={() => { setStep(1); setFile(null); setDocId(null); setSelectedRecipients([]); }}>Encrypt Another Document</Button>
            </motion.div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
