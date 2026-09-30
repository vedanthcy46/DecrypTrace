'use client';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Key, Unlock, Shield, FileText, Check, RefreshCw } from 'lucide-react';

export default function RecipientPage() {
  const [documents, setDocuments] = useState<any[]>([]);
  const [recipients, setRecipients] = useState<any[]>([]);
  const [selectedDoc, setSelectedDoc] = useState<any>(null);

  const [decrypting, setDecrypting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [decryptedFile, setDecryptedFile] = useState<string | null>(null);

  // Identity: callsign typed in UI, keyInfo = local key info from agent, recipientInfo = backend DB record
  const [callsign, setCallsign] = useState('');
  const [generating, setGenerating] = useState(false);
  const [keyInfo, setKeyInfo] = useState<any>(null);       // Local agent keys (has callsign)
  const [recipientInfo, setRecipientInfo] = useState<any>(null); // Backend DB record (has .id)

  useEffect(() => {
    loadDocuments();
    loadRecipients();
    // Auto-load saved identity from agent keystore
    loadSavedIdentity();
  }, []);

  const loadDocuments = async (recipientId?: string) => {
    try {
      const { api } = await import('@/lib/api');
      const docs = recipientId
        ? await api.listDocumentsForRecipient(recipientId)
        : await api.listDocuments();
      setDocuments(docs || []);
    } catch (err) {
      console.error(err);
    }
  };

  const loadRecipients = async () => {
    try {
      const { api } = await import('@/lib/api');
      const recs = await api.listRecipients();
      setRecipients(recs || []);
    } catch (err) {
      console.error(err);
    }
  };

  const loadSavedIdentity = async () => {
    try {
      // Ask agent for list of stored keypairs
      const res = await fetch('http://localhost:8010/api/keys/list');
      if (!res.ok) return;
      const data = await res.json();
      if (data?.keypairs?.length > 0) {
        const saved = data.keypairs[0]; // Use most recent
        setKeyInfo(saved);
        setCallsign(saved.callsign);
      }
    } catch (err) {
      // Agent not running or no saved keys - ok
    }
  };

  // After keyInfo is set, find the corresponding backend recipient record
  useEffect(() => {
    if (!keyInfo || recipients.length === 0) return;
    const match = recipients.find(
      (r: any) => r.callsign === keyInfo.callsign || r.callsign === callsign
    );
    if (match) {
      setRecipientInfo(match);
      loadDocuments(match.id); // Reload inbox filtered to this recipient
    }
  }, [keyInfo, recipients, callsign]);

  const handleGenerateKeys = async () => {
    if (!callsign) return;
    setGenerating(true);
    try {
      const { api } = await import('@/lib/api');
      // 1. Generate keys locally in agent
      const localKeys = await api.generateKeys({ callsign, name: callsign });
      setKeyInfo(localKeys);

      // 2. Register public keys with backend
      const regResponse = await api.registerRecipient({
        name: callsign,
        callsign: callsign,
        email: `${callsign.toLowerCase()}@decryptrace.local`,
        ml_kem_public_key: localKeys.kem_public_key,
        ml_dsa_public_key: localKeys.dsa_public_key
      });
      setRecipientInfo(regResponse);
      setDocuments([]); // Clear while reloading
      await loadRecipients();
      await loadDocuments(regResponse.id); // Load only docs for this recipient
    } catch (err: any) {
      console.error(err);
      alert(`Failed to generate keys: ${err.message}\n\nMake sure the Recipient Agent (port 8010) is running.`);
    }
    setGenerating(false);
  };

  const handleDecrypt = async () => {
    if (!selectedDoc) {
      alert("Please select a document from your inbox.");
      return;
    }
    if (!keyInfo || !recipientInfo) {
      alert("Please generate your identity keys first. The system needs to find your callsign in the backend registry.");
      return;
    }

    setDecrypting(true);
    setProgress(0);

    try {
      const { api } = await import('@/lib/api');

      // 1. Prepare Decryption (Backend creates session, returns envelope)
      setProgress(1);
      const prepRes = await api.prepareDecryption(selectedDoc.id, recipientInfo.id);

      // 2. Decrypt locally via Agent (uses stored private key)
      setProgress(2);
      const agentRes = await api.decryptDocument({
        session_id: prepRes.session_id,
        document_id: prepRes.document_id,
        encrypted_document_b64: prepRes.encrypted_document_b64,
        kem_ciphertext_b64: prepRes.kem_ciphertext_b64,
        wrapped_dek_b64: prepRes.wrapped_dek_b64,
        kek_nonce_b64: prepRes.kek_nonce_b64,
        nonce_b64: prepRes.nonce_b64,
        document_hash: prepRes.document_hash,
        watermark_id: prepRes.watermark_id,
        callsign: keyInfo.callsign
      });

      // 3. Submit signed evidence to Backend
      setProgress(3);
      await api.submitEvidence(prepRes.session_id, {
        client_instance_id: agentRes.canonical_record?.clientInstanceId || keyInfo.callsign,
        canonical_record: agentRes.canonical_record,
        recipient_signature: agentRes.recipient_signature
      });

      // 4. Commit to Ledger (2-of-3 quorum)
      setProgress(4);
      await api.commitSession(prepRes.session_id);

      setProgress(5);
      setDecryptedFile(agentRes.decrypted_document_b64);

    } catch (err: any) {
      console.error(err);
      alert(`Decryption failed: ${err.message}`);
      setDecrypting(false);
      setProgress(0);
    }
  };

  const handleDownload = () => {
    if (!decryptedFile || !selectedDoc) return;
    const binaryStr = window.atob(decryptedFile);
    const len = binaryStr.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) bytes[i] = binaryStr.charCodeAt(i);
    const blob = new Blob([bytes], { type: 'application/pdf' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `Decrypted_${selectedDoc.title}.pdf`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const steps = [
    'Initializing Session & ML-KEM Decapsulation',
    'Decrypting Content (AES-GCM)',
    'Embedding Unique Watermark & Signing Session (ML-DSA)',
    'Submitting Signed Evidence to DecrypTrace Backend',
    'Committing to Distributed Ledger (2-of-3 Quorum)'
  ];

  const isReady = !!keyInfo && !!recipientInfo;

  return (
    <div className="space-y-8 max-w-5xl mx-auto">
      <div className="flex items-center space-x-4 border-b border-[#1E293B] pb-6">
        <div className="p-3 bg-[#10B981]/20 rounded-xl">
          <Key className="w-8 h-8 text-[#10B981]" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-white">Recipient Portal</h1>
          <p className="text-[#94A3B8]">Access encrypted documents safely</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Identity Setup</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {!isReady ? (
                <>
                  <div className="space-y-2">
                    <label className="text-sm text-[#94A3B8]">Agent Callsign</label>
                    <Input
                      placeholder="e.g., Agent_Alpha"
                      value={callsign}
                      onChange={(e) => setCallsign(e.target.value)}
                    />
                  </div>
                  <Button
                    variant="recipient"
                    className="w-full"
                    onClick={handleGenerateKeys}
                    disabled={generating || !callsign}
                  >
                    {generating ? 'Generating...' : 'Generate Keys'}
                  </Button>
                  {keyInfo && !recipientInfo && (
                    <p className="text-xs text-yellow-400">Keys found locally but not in backend registry. Click Generate to re-register.</p>
                  )}
                </>
              ) : (
                <div className="space-y-3">
                  <div className="flex items-center space-x-2 text-[#10B981]">
                    <Check className="w-5 h-5" />
                    <span className="font-medium">Identity Active</span>
                  </div>
                  <div className="p-3 bg-[#1E293B] rounded-lg">
                    <p className="text-sm text-[#94A3B8] mb-1">Callsign</p>
                    <p className="font-medium text-white">{keyInfo.callsign}</p>
                    <p className="text-sm text-[#94A3B8] mt-2 mb-1">Fingerprint</p>
                    <p className="font-mono text-xs text-[#10B981] truncate">{keyInfo.key_fingerprint || recipientInfo.key_fingerprint}</p>
                  </div>
                  <Button variant="outline" className="w-full text-xs" onClick={() => { setKeyInfo(null); setRecipientInfo(null); }}>
                    <RefreshCw className="w-3 h-3 mr-1" /> Switch Identity
                  </Button>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Inbox</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {documents.length === 0 && <p className="text-[#94A3B8] text-sm">No encrypted documents found.</p>}
              {documents.map(doc => (
                <div
                  key={doc.id}
                  onClick={() => !decrypting && setSelectedDoc(doc)}
                  className={`p-3 rounded-lg border cursor-pointer transition-colors ${selectedDoc?.id === doc.id ? 'bg-[#1E293B] border-[#10B981]' : 'border-[#1E293B] hover:border-[#10B981]/50'}`}
                >
                  <div className="flex items-center space-x-2">
                    <FileText className={`w-4 h-4 ${selectedDoc?.id === doc.id ? 'text-[#10B981]' : 'text-[#94A3B8]'}`} />
                    <span className="text-sm font-medium truncate">{doc.title}</span>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2">
          <Card className="h-full">
            <CardHeader>
              <CardTitle>Decryption Workspace</CardTitle>
            </CardHeader>
            <CardContent>
              {!decrypting ? (
                <div className="text-center py-12 space-y-6">
                  <Shield className="w-16 h-16 text-[#1E293B] mx-auto" />
                  <p className="text-[#94A3B8]">
                    {!isReady
                      ? 'Generate your identity keys to access encrypted documents.'
                      : selectedDoc
                      ? `Selected: ${selectedDoc.title}`
                      : 'Select a document from your inbox to decrypt.'}
                  </p>
                  <Button variant="recipient" size="lg" onClick={handleDecrypt} disabled={!selectedDoc || !isReady}>
                    <Unlock className="w-4 h-4 mr-2" /> Decrypt Document
                  </Button>
                </div>
              ) : (
                <div className="space-y-6 py-6">
                  {steps.map((label, idx) => (
                    <div key={idx} className="flex items-center space-x-4">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center border-2 shrink-0
                        ${progress > idx ? 'bg-[#10B981] border-[#10B981]' :
                          progress === idx ? 'border-[#10B981] animate-pulse' : 'border-[#1E293B]'}`}>
                        {progress > idx && <Check className="w-4 h-4 text-white" />}
                      </div>
                      <span className={`text-sm font-medium ${progress >= idx ? 'text-white' : 'text-[#94A3B8]'}`}>
                        {label}
                      </span>
                    </div>
                  ))}

                  {progress >= 5 && (
                    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="mt-8 p-6 bg-[#10B981]/10 border border-[#10B981]/30 rounded-xl text-center">
                      <h3 className="text-xl font-bold text-[#10B981] mb-4">Document Ready</h3>
                      <Button variant="recipient" onClick={handleDownload}>Download Plaintext Document</Button>
                      <Button variant="outline" className="ml-4" onClick={() => { setDecrypting(false); setDecryptedFile(null); setSelectedDoc(null); }}>Close</Button>
                    </motion.div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
