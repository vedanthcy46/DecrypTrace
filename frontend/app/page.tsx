'use client';
import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileText, Users, LockOpen, Database, ArrowRight } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const [statsData, setStatsData] = useState({
    documents: 0,
    recipients: 0,
    sessions: 0,
    blocks: 0
  });
  const [recentSessions, setRecentSessions] = useState<any[]>([]);

  useEffect(() => {
    async function loadStats() {
      try {
        const { api } = await import('@/lib/api');
        const [docs, recs, sessions, blocks] = await Promise.all([
          api.listDocuments(),
          api.listRecipients(),
          api.listSessions(),
          api.getLedgerBlocks()
        ]);
        
        setStatsData({
          documents: docs?.length || 0,
          recipients: recs?.length || 0,
          sessions: sessions?.length || 0,
          blocks: blocks?.length || 0
        });
        
        if (sessions?.length) {
          // Sort sessions by date (descending) and take top 3
          const sorted = [...sessions].sort((a: any, b: any) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
          ).slice(0, 5);
          
          // Attach recipient callsign
          for (let s of sorted) {
            const rec = recs?.find((r: any) => r.id === s.recipient_id);
            s.recipient_callsign = rec ? rec.callsign : 'Unknown';
          }
          
          setRecentSessions(sorted);
        }
      } catch (err) {
        console.error("Failed to load dashboard stats", err);
      }
    }
    loadStats();
  }, []);

  const stats = [
    { title: 'Total Documents', value: statsData.documents.toString(), icon: FileText, color: 'text-blue-500' },
    { title: 'Recipients', value: statsData.recipients.toString(), icon: Users, color: 'text-green-500' },
    { title: 'Decryption Events', value: statsData.sessions.toString(), icon: LockOpen, color: 'text-purple-500' },
    { title: 'Ledger Blocks', value: statsData.blocks.toString(), icon: Database, color: 'text-amber-500' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-white">System Overview</h1>
        <p className="text-[#94A3B8] mt-2">Post-Quantum Secure Attribution System</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <motion.div key={stat.title} initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.1 }}>
            <Card glow>
              <CardContent className="p-6 flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-[#94A3B8]">{stat.title}</p>
                  <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <div className={`p-3 rounded-xl bg-opacity-10 bg-current ${stat.color}`}>
                  <stat.icon className="w-6 h-6" />
                </div>
              </CardContent>
            </Card>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentSessions.length === 0 ? (
                <p className="text-sm text-[#94A3B8]">No decryption events recorded yet.</p>
              ) : (
                recentSessions.map((session, i) => (
                  <div key={session.session_id} className="flex items-start space-x-4 p-3 rounded-lg bg-[#1E293B]/50">
                    <div className="w-2 h-2 mt-2 rounded-full bg-[#10B981]" />
                    <div>
                      <p className="text-sm font-medium text-white">Document decrypted by {session.recipient_callsign}</p>
                      <p className="text-xs text-[#94A3B8]">
                        Block #{session.ledger_block_index || 'Pending'} • {new Date(session.created_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Link href="/sender" className="block">
              <Button variant="sender" className="w-full justify-between" size="lg">
                Upload & Encrypt Document <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <Link href="/investigator" className="block">
              <Button variant="investigator" className="w-full justify-between" size="lg">
                Investigate Leak <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
