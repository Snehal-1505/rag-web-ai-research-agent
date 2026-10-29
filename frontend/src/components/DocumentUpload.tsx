import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, CheckCircle2, AlertCircle, RefreshCw, X, Loader2 } from 'lucide-react';
import { uploadDocument } from '../services/api';
import { DocumentUploadResult } from '../types/chat';

interface DocumentUploadProps {
  sessionId?: string | null;
  onUploadSuccess?: (result: DocumentUploadResult) => void;
  onClose?: () => void;
}

export const DocumentUpload: React.FC<DocumentUploadProps> = ({
  sessionId,
  onUploadSuccess,
  onClose,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadStatus, setUploadStatus] = useState<{
    type: 'idle' | 'success' | 'duplicate' | 'error';
    message: string;
    filename?: string;
  }>({ type: 'idle', message: '' });

  const fileInputRef = useRef<HTMLInputElement>(null);

  const processFile = async (file: File) => {
    const validExtensions = ['.pdf', '.txt', '.docx'];
    const fileName = file.name.toLowerCase();
    const isValid = validExtensions.some((ext) => fileName.endsWith(ext));

    if (!isValid) {
      setUploadStatus({
        type: 'error',
        message: 'Unsupported format. Please upload a .pdf, .txt, or .docx file.',
      });
      return;
    }

    if (file.size > 50 * 1024 * 1024) {
      setUploadStatus({
        type: 'error',
        message: 'File size exceeds maximum 50 MB limit.',
      });
      return;
    }

    setIsUploading(true);
    setUploadStatus({ type: 'idle', message: '' });

    try {
      const res = await uploadDocument(file, sessionId || undefined);

      if (res.status === 'duplicate') {
        setUploadStatus({
          type: 'duplicate',
          message: res.message,
          filename: res.filename,
        });
      } else {
        setUploadStatus({
          type: 'success',
          message: res.message,
          filename: res.filename,
        });
      }

      if (onUploadSuccess) {
        onUploadSuccess(res);
      }
    } catch (err: any) {
      setUploadStatus({
        type: 'error',
        message: err.message || 'Failed to index document.',
        filename: file.name,
      });
    } finally {
      setIsUploading(false);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      processFile(e.target.files[0]);
    }
  };

  return (
    <div className="p-4 rounded-2xl bg-white dark:bg-loomi-dark-surface border border-loomi-border dark:border-loomi-dark-border shadow-warm">
      <div className="flex items-center justify-between pb-3 mb-3 border-b border-loomi-border/60 dark:border-loomi-dark-border/60">
        <div className="flex items-center gap-2">
          <div className="p-1.5 rounded-lg bg-loomi-coral/10 text-loomi-coral">
            <UploadCloud className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-semibold text-loomi-ink dark:text-loomi-dark-text">
              Knowledge Base Ingestion
            </h3>
            <p className="text-xs text-loomi-secondary dark:text-loomi-dark-muted">
              PDF, TXT, or DOCX (max 50 MB)
            </p>
          </div>
        </div>
        {onClose && (
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-loomi-secondary hover:text-loomi-ink dark:hover:text-loomi-dark-text hover:bg-loomi-sand/50 dark:hover:bg-loomi-dark-elevated transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !isUploading && fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-5 text-center cursor-pointer transition-all duration-200 ${
          isDragging
            ? 'border-loomi-coral bg-loomi-coral-light/40 dark:bg-loomi-coral/10'
            : 'border-loomi-border dark:border-loomi-dark-border bg-loomi-sand/30 dark:bg-loomi-dark-elevated/30 hover:border-loomi-coral/60 hover:bg-loomi-sand/50 dark:hover:bg-loomi-dark-elevated/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.docx"
          onChange={handleFileChange}
          className="hidden"
          disabled={isUploading}
        />

        {isUploading ? (
          <div className="flex flex-col items-center justify-center py-2">
            <Loader2 className="w-7 h-7 text-loomi-coral animate-spin mb-2" />
            <p className="text-xs font-medium text-loomi-ink dark:text-loomi-dark-text">
              Extracting text, chunking & generating embeddings…
            </p>
            <p className="text-[11px] text-loomi-secondary dark:text-loomi-dark-muted mt-0.5">
              Indexing to ChromaDB vector store
            </p>
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center py-2">
            <div className="w-10 h-10 rounded-full bg-loomi-sand dark:bg-loomi-dark-elevated flex items-center justify-center text-loomi-coral mb-2">
              <FileText className="w-5 h-5" />
            </div>
            <p className="text-xs font-semibold text-loomi-ink dark:text-loomi-dark-text">
              Click to choose a file <span className="font-normal text-loomi-secondary">or drag and drop</span>
            </p>
            <p className="text-[11px] text-loomi-secondary dark:text-loomi-dark-muted mt-1">
              Supports .pdf, .txt, .docx
            </p>
          </div>
        )}
      </div>

      {/* Status Messages */}
      {uploadStatus.type !== 'idle' && (
        <div
          className={`mt-3 p-2.5 rounded-xl text-xs flex items-start gap-2 ${
            uploadStatus.type === 'success'
              ? 'bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 dark:text-emerald-300 border border-emerald-200 dark:border-emerald-800/60'
              : uploadStatus.type === 'duplicate'
              ? 'bg-amber-50 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 border border-amber-200 dark:border-amber-800/60'
              : 'bg-rose-50 dark:bg-rose-950/40 text-rose-800 dark:text-rose-300 border border-rose-200 dark:border-rose-800/60'
          }`}
        >
          {uploadStatus.type === 'success' && <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />}
          {uploadStatus.type === 'duplicate' && <RefreshCw className="w-4 h-4 flex-shrink-0 mt-0.5" />}
          {uploadStatus.type === 'error' && <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />}
          <div className="leading-relaxed">
            {uploadStatus.filename && <span className="font-semibold block">{uploadStatus.filename}</span>}
            {uploadStatus.message}
          </div>
        </div>
      )}
    </div>
  );
};
