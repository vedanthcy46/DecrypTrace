'use client';
import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Database, Link as LinkIcon, ShieldCheck, Activity, AlertTriangle } from 'lucide-react';

export default function LedgerPage() {
  const [blocks, setBlocks] = useState<any[]>([]);
  const [nodes, setNodes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [verifyResult, setVerifyResult] = useState<any>(null);

  const loadData = async () => {
    try {
      const { api } = await import('@/lib/api');
      const [fetchedBlocks, health] = await Promise.all([
        api.getLedgerBlocks(),
        api.nodesHealth()
      ]);
      setBlocks(fetchedBlocks || []);
      setNodes(health.nodes || []);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleVerify = async () => {
    try {
      const { api } = await import('@/lib/api');
      const res = await api.verifyLedger();
      setVerifyResult(res);
      setTimeout(() => setVerifyResult(null), 5000);
    } catch (err) {
      console.error(err);
    }
  };

  const handleTamper = async () => {
    try {
      const { api } = await import('@/lib/api');
      const res = await api.tamperTest();
      alert(`Tamper Test: ${res.divergence_detected ? 'Divergence Detected! Network caught the tamper attempt.' : 'No blocks to tamper with.'}\n\nDetails: ${res.details}`);
      handleVerify(); // Run verify after tamper to show it
    } catch (err) {
      console.error(err);
      alert('Tamper test failed. Ensure DLT nodes are running.');
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="flex items-center justify-between border-b border-[#1E293B] pb-6">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-[#3B82F6]/20 rounded-xl">
            <Database className="w-8 h-8 text-[#3B82F6]" />
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">Immutable Ledger</h1>
            <p className="text-[#94A3B8]">Decentralized record of all access events</p>
          </div>
        </div>
        <div className="flex space-x-4">
          <Button variant="outline" onClick={handleTamper}><Activity className="w-4 h-4 mr-2"/> Tamper Test</Button>
          <Button variant="default" onClick={handleVerify}><ShieldCheck className="w-4 h-4 mr-2"/> Verify Chain</Button>
        </div>
      </div>

      {verifyResult && (
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}>
          <div className={`p-4 rounded-lg border ${verifyResult.verified ? 'bg-[#10B981]/10 border-[#10B981]/30 text-[#10B981]' : 'bg-red-500/10 border-red-500/30 text-red-500'} flex items-center space-x-3`}>
            {verifyResult.verified ? <ShieldCheck className="w-6 h-6" /> : <AlertTriangle className="w-6 h-6" />}
            <div>
              <p className="font-bold">{verifyResult.verified ? 'Ledger Integrity Verified' : 'DIVERGENCE DETECTED'}</p>
              <p className="text-sm opacity-80">{verifyResult.divergence ? verifyResult.divergence.join(', ') : 'All nodes in consensus.'}</p>
            </div>
          </div>
        </motion.div>
      )}

      <div className="relative py-12 overflow-x-auto">
        {blocks.length === 0 && !loading ? (
          <div className="text-center text-[#94A3B8] py-12">No blocks in ledger yet. Process a decryption to mine blocks.</div>
        ) : (
          <div className="flex items-center space-x-4 min-w-max px-4">
            {blocks.map((block, i) => (
              <div key={block.index} className="flex items-center">
                <motion.div 
                  initial={{ opacity: 0, y: 20 }} 
                  animate={{ opacity: 1, y: 0 }} 
                  transition={{ delay: i * 0.1 }}
                >
                  <Card className="w-64 border-[#3B82F6]/30 hover:border-[#3B82F6] transition-colors cursor-pointer bg-[#0A0F1C]">
                    <CardHeader className="pb-2">
                      <div className="flex justify-between items-center">
                        <span className="text-xs font-bold text-[#3B82F6]">BLOCK #{block.index}</span>
                        <div className="w-2 h-2 rounded-full bg-[#10B981]" />
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-3">
                      <div>
                        <p className="text-xs text-[#94A3B8]">Hash</p>
                        <p className="font-mono text-xs text-white truncate" title={block.hash}>{block.hash}</p>
                      </div>
                      <div>
                        <p className="text-xs text-[#94A3B8]">Transactions</p>
                        <p className="font-medium text-white">{block.transactions?.length || 0} Events</p>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
                
                {i < blocks.length - 1 && (
                  <div className="px-4 text-[#3B82F6]/50">
                    <LinkIcon className="w-6 h-6" />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {nodes.map((node, idx) => (
          <Card key={idx}>
            <CardContent className="p-6 flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <Database className="w-5 h-5 text-[#94A3B8]" />
                <span className="font-medium text-white text-sm">{node.url.split('//')[1]}</span>
              </div>
              <div className={`flex items-center space-x-2 px-3 py-1 rounded-full ${node.status === 'up' ? 'bg-[#10B981]/10' : 'bg-red-500/10'}`}>
                <div className={`w-2 h-2 rounded-full ${node.status === 'up' ? 'bg-[#10B981] animate-pulse' : 'bg-red-500'}`} />
                <span className={`text-xs font-medium ${node.status === 'up' ? 'text-[#10B981]' : 'text-red-500'}`}>
                  {node.status === 'up' ? 'SYNCED' : 'OFFLINE'}
                </span>
              </div>
            </CardContent>
          </Card>
        ))}
        {nodes.length === 0 && !loading && [1,2,3].map(i => (
          <Card key={i}>
             <CardContent className="p-6 flex items-center justify-between opacity-50">
                <span className="text-[#94A3B8]">Node {i} Offline</span>
             </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}
