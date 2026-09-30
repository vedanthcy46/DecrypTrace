export const API_URL = 'http://localhost:8000/api';
export const RECIPIENT_API_URL = 'http://localhost:8010/api';

const handleResponse = async (r: Response) => {
  if (!r.ok) {
    const err = await r.json().catch(() => ({}));
    throw new Error(err.detail || `Request failed with status ${r.status}`);
  }
  return r.json();
};

export const api = {
  // Documents
  uploadDocument: async (data: FormData) => fetch(`${API_URL}/documents/`, { method: 'POST', body: data }).then(handleResponse),
  encryptDocument: async (docId: string, policies: any) => fetch(`${API_URL}/documents/${docId}/encrypt`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(policies) }).then(handleResponse),
  listDocuments: async () => fetch(`${API_URL}/documents/`).then(handleResponse),
  listDocumentsForRecipient: async (recipientId: string) => fetch(`${API_URL}/documents/?recipient_id=${recipientId}`).then(handleResponse),
  
  // Recipients
  registerRecipient: async (data: any) => fetch(`${API_URL}/recipients/`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) }).then(handleResponse),
  listRecipients: async () => fetch(`${API_URL}/recipients/`).then(handleResponse),
  
  // Decryption Flow
  prepareDecryption: async (docId: string, recipientId: string) => fetch(`${API_URL}/decryption/prepare/${docId}?recipient_id=${recipientId}`, { method: 'POST' }).then(handleResponse),
  submitEvidence: async (sessionId: string, data: any) => fetch(`${API_URL}/decryption/${sessionId}/submit-evidence`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) }).then(handleResponse),
  commitSession: async (sessionId: string) => fetch(`${API_URL}/decryption/${sessionId}/commit`, { method: 'POST' }).then(handleResponse),
  listSessions: async () => fetch(`${API_URL}/decryption/sessions`).then(handleResponse),
  
  // Forensics
  analyzeLeakedDoc: async (data: FormData) => fetch(`${API_URL}/forensics/analyze`, { method: 'POST', body: data }).then(handleResponse),
  listReports: async () => fetch(`${API_URL}/forensics/reports`).then(handleResponse),
  getReport: async (id: string) => fetch(`${API_URL}/forensics/reports/${id}`).then(handleResponse),
  
  // Ledger
  getLedgerBlocks: async () => fetch(`${API_URL}/ledger/blocks`).then(handleResponse),
  verifyLedger: async () => fetch(`${API_URL}/ledger/verify`).then(handleResponse),
  tamperTest: async () => fetch(`${API_URL}/ledger/tamper-test`, { method: 'POST' }).then(handleResponse),
  nodesHealth: async () => fetch(`${API_URL}/ledger/nodes/health`).then(handleResponse),
  
  // Recipient Agent (Local)
  generateKeys: async (data: any) => fetch(`${RECIPIENT_API_URL}/keys/generate`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) }).then(handleResponse),
  rotateKeys: async (data: any) => fetch(`${RECIPIENT_API_URL}/keys/rotate`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) }).then(handleResponse),
  decryptDocument: async (data: any) => fetch(`${RECIPIENT_API_URL}/decrypt`, { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(data) }).then(handleResponse),
};
