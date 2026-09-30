import { create } from 'zustand';
import { api } from './api';

type Role = 'sender' | 'recipient' | 'investigator' | 'ledger';

interface AppState {
  activeRole: Role;
  setActiveRole: (role: Role) => void;
  documents: any[];
  recipients: any[];
  sessions: any[];
  reports: any[];
  blocks: any[];
  loading: boolean;
  fetchDocuments: () => Promise<void>;
  fetchRecipients: () => Promise<void>;
  fetchSessions: () => Promise<void>;
  fetchReports: () => Promise<void>;
  fetchBlocks: () => Promise<void>;
}

export const useStore = create<AppState>((set) => ({
  activeRole: 'sender',
  setActiveRole: (role) => set({ activeRole: role }),
  documents: [],
  recipients: [],
  sessions: [],
  reports: [],
  blocks: [],
  loading: false,
  fetchDocuments: async () => {
    set({ loading: true });
    try { const docs = await api.listDocuments(); set({ documents: docs }); } catch (e) { console.error(e); } finally { set({ loading: false }); }
  },
  fetchRecipients: async () => {
    set({ loading: true });
    try { const recs = await api.listRecipients(); set({ recipients: recs }); } catch (e) { console.error(e); } finally { set({ loading: false }); }
  },
  fetchSessions: async () => {
    set({ loading: true });
    try { const sess = await api.listSessions(); set({ sessions: sess }); } catch (e) { console.error(e); } finally { set({ loading: false }); }
  },
  fetchReports: async () => {
    set({ loading: true });
    try { const reps = await api.listReports(); set({ reports: reps }); } catch (e) { console.error(e); } finally { set({ loading: false }); }
  },
  fetchBlocks: async () => {
    set({ loading: true });
    try { const blks = await api.getLedgerBlocks(); set({ blocks: blks }); } catch (e) { console.error(e); } finally { set({ loading: false }); }
  }
}));
