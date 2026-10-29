import {
  HealthInfo,
  Session,
  SessionDetail,
  DocumentRecord,
  DocumentUploadResult,
} from '../types/chat';

const API_BASE = '/api';

export async function fetchHealth(): Promise<HealthInfo> {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSessions(): Promise<Session[]> {
  const res = await fetch(`${API_BASE}/sessions`);
  if (!res.ok) throw new Error(`Failed to fetch sessions: ${res.statusText}`);
  return res.json();
}

export async function createSession(title?: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title: title || 'New Chat' }),
  });
  if (!res.ok) throw new Error(`Failed to create session: ${res.statusText}`);
  return res.json();
}

export async function fetchSession(sessionId: string): Promise<SessionDetail> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`);
  if (!res.ok) throw new Error(`Failed to fetch session: ${res.statusText}`);
  return res.json();
}

export async function renameSession(sessionId: string, title: string): Promise<Session> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title }),
  });
  if (!res.ok) throw new Error(`Failed to rename session: ${res.statusText}`);
  return res.json();
}

export async function deleteSession(sessionId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error(`Failed to delete session: ${res.statusText}`);
}

export async function uploadDocument(file: File, sessionId?: string): Promise<DocumentUploadResult> {
  const formData = new FormData();
  formData.append('file', file);
  if (sessionId) {
    formData.append('session_id', sessionId);
  }

  const res = await fetch(`${API_BASE}/documents/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Upload failed with status ${res.status}`);
  }

  return res.json();
}

export async function fetchDocuments(): Promise<{
  documents: DocumentRecord[];
  indexed_filenames: string[];
  total_chunks: number;
}> {
  const res = await fetch(`${API_BASE}/documents`);
  if (!res.ok) throw new Error(`Failed to fetch documents: ${res.statusText}`);
  return res.json();
}

export async function fetchDocumentStatus(docId: string): Promise<{
  id: string;
  filename: string;
  status: string;
  error_message?: string;
  upload_time: string;
}> {
  const res = await fetch(`${API_BASE}/documents/${docId}/status`);
  if (!res.ok) throw new Error(`Failed to fetch status: ${res.statusText}`);
  return res.json();
}
