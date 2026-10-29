export type Role = 'user' | 'assistant';

export interface DocSource {
  filename: string;
  page?: number;
  content: string;
  score?: number;
}

export interface WebSource {
  title: string;
  url: string;
  content: string;
  provider?: string;
  score?: number;
}

export interface MessageMetadata {
  strategy?: 'documents' | 'web' | 'hybrid' | string;
  doc_results?: DocSource[];
  web_results?: WebSource[];
}

export interface Message {
  id: string;
  role: Role;
  content: string;
  timestamp: string;
  metadata?: MessageMetadata;
}

export interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface SessionDetail {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface HealthInfo {
  status: string;
  version: string;
  indexed_documents: number;
  indexed_files: string[];
  gemini_configured: boolean;
  tavily_configured: boolean;
}

export interface DocumentRecord {
  id: string;
  filename: string;
  stored_path?: string;
  file_hash: string;
  upload_time: string;
  status: 'pending' | 'processing' | 'ready' | 'error' | 'duplicate';
  error_message?: string | null;
  conversation_id?: string | null;
}

export interface DocumentUploadResult {
  document_id: string;
  filename: string;
  status: string;
  message: string;
}

export type ResearchStage = 'idle' | 'searching' | 'generating' | 'done' | 'error';
