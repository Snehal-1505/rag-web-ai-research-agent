import React, { useState } from 'react';
import {
  Sparkles,
  Plus,
  MessageSquare,
  Search,
  MoreVertical,
  Edit2,
  Trash2,
  Check,
  X,
  FileText,
  ChevronRight,
  Database,
} from 'lucide-react';
import { Session } from '../types/chat';

interface SidebarProps {
  sessions: Session[];
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
  onRenameSession: (id: string, title: string) => void;
  onDeleteSession: (id: string) => void;
  indexedCount?: number;
  indexedFiles?: string[];
  isOpen: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  sessions,
  activeSessionId,
  onSelectSession,
  onNewChat,
  onRenameSession,
  onDeleteSession,
  indexedCount = 0,
  indexedFiles = [],
  isOpen,
  onCloseMobile,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null);
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);
  const [showDocLibrary, setShowDocLibrary] = useState(false);

  const filteredSessions = sessions.filter((s) =>
    s.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const startRename = (s: Session) => {
    setEditingId(s.id);
    setEditTitle(s.title);
    setActiveMenuId(null);
  };

  const saveRename = (id: string) => {
    if (editTitle.trim()) {
      onRenameSession(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const confirmDelete = (id: string) => {
    onDeleteSession(id);
    setConfirmDeleteId(null);
    setActiveMenuId(null);
  };

  return (
    <>
      {/* Mobile Backdrop */}
      {isOpen && (
        <div
          onClick={onCloseMobile}
          className="fixed inset-0 bg-black/40 backdrop-blur-xs z-40 md:hidden"
        />
      )}

      {/* Sidebar Container */}
      <aside
        className={`fixed md:static inset-y-0 left-0 z-50 w-72 bg-white dark:bg-loomi-dark-surface border-r border-loomi-border dark:border-loomi-dark-border flex flex-col justify-between transform transition-transform duration-300 ease-in-out md:translate-x-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        {/* Top: Brand & New Chat */}
        <div className="p-4 border-b border-loomi-border/60 dark:border-loomi-dark-border/60">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-loomi-coral to-amber-500 text-white flex items-center justify-center shadow-sm">
                <Sparkles className="w-4 h-4" />
              </div>
              <div>
                <h2 className="font-serif font-bold text-lg leading-tight text-loomi-ink dark:text-loomi-dark-text tracking-tight">
                  Loomi AI
                </h2>
                <p className="text-[10px] text-loomi-secondary dark:text-loomi-dark-muted font-medium">
                  Weaving knowledge into answers
                </p>
              </div>
            </div>
            <button
              onClick={onCloseMobile}
              className="p-1 rounded-lg text-loomi-secondary md:hidden hover:bg-loomi-sand/40"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* New Chat Button */}
          <button
            onClick={() => {
              onNewChat();
              onCloseMobile();
            }}
            className="w-full py-2.5 px-3.5 rounded-xl bg-loomi-coral text-white font-medium text-xs flex items-center justify-center gap-2 hover:bg-loomi-coral-hover shadow-sm transition-all duration-200"
          >
            <Plus className="w-4 h-4" />
            <span>New Research Chat</span>
          </button>

          {/* Search sessions */}
          {sessions.length > 3 && (
            <div className="mt-3 relative">
              <Search className="w-3.5 h-3.5 text-loomi-secondary absolute left-2.5 top-2.5" />
              <input
                type="text"
                placeholder="Search conversations…"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 rounded-lg bg-loomi-sand/40 dark:bg-loomi-dark-elevated text-xs text-loomi-ink dark:text-loomi-dark-text placeholder:text-loomi-secondary/70 focus:outline-none focus:ring-1 focus:ring-loomi-coral"
              />
            </div>
          )}
        </div>

        {/* Middle: Conversation List */}
        <div className="flex-1 overflow-y-auto p-2 space-y-1">
          <div className="px-2 py-1 text-[10px] font-semibold tracking-wider text-loomi-secondary/80 dark:text-loomi-dark-muted/80 uppercase">
            Conversations
          </div>

          {filteredSessions.length === 0 ? (
            <div className="text-center py-8 text-xs text-loomi-secondary dark:text-loomi-dark-muted">
              {searchQuery ? 'No chats match your search.' : 'No conversations yet.'}
            </div>
          ) : (
            filteredSessions.map((session) => {
              const isActive = session.id === activeSessionId;
              const isEditing = editingId === session.id;
              const isConfirmingDelete = confirmDeleteId === session.id;

              if (isEditing) {
                return (
                  <div
                    key={session.id}
                    className="flex items-center gap-1 p-1.5 rounded-xl bg-loomi-sand/60 dark:bg-loomi-dark-elevated"
                  >
                    <input
                      type="text"
                      value={editTitle}
                      onChange={(e) => setEditTitle(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') saveRename(session.id);
                        if (e.key === 'Escape') setEditingId(null);
                      }}
                      autoFocus
                      className="flex-1 px-2 py-1 rounded bg-white dark:bg-black text-xs text-loomi-ink dark:text-loomi-dark-text focus:outline-none focus:ring-1 focus:ring-loomi-coral"
                    />
                    <button
                      onClick={() => saveRename(session.id)}
                      className="p-1 text-emerald-600 hover:bg-white dark:hover:bg-black rounded"
                    >
                      <Check className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => setEditingId(null)}
                      className="p-1 text-rose-500 hover:bg-white dark:hover:bg-black rounded"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                );
              }

              if (isConfirmingDelete) {
                return (
                  <div
                    key={session.id}
                    className="p-2 rounded-xl bg-rose-50 dark:bg-rose-950/40 border border-rose-200 dark:border-rose-900 text-xs"
                  >
                    <p className="text-rose-800 dark:text-rose-300 font-medium mb-1.5 text-[11px]">
                      Delete this conversation?
                    </p>
                    <div className="flex gap-2">
                      <button
                        onClick={() => confirmDelete(session.id)}
                        className="px-2 py-1 bg-rose-600 text-white rounded text-[10px] font-medium hover:bg-rose-700"
                      >
                        Delete
                      </button>
                      <button
                        onClick={() => setConfirmDeleteId(null)}
                        className="px-2 py-1 bg-stone-200 dark:bg-stone-800 text-stone-700 dark:text-stone-300 rounded text-[10px]"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                );
              }

              return (
                <div
                  key={session.id}
                  className={`group relative flex items-center justify-between p-2 rounded-xl text-xs cursor-pointer transition-colors ${
                    isActive
                      ? 'bg-loomi-sand/70 dark:bg-loomi-dark-elevated text-loomi-ink dark:text-loomi-dark-text font-semibold shadow-xs'
                      : 'text-loomi-secondary dark:text-loomi-dark-muted hover:bg-loomi-sand/30 dark:hover:bg-loomi-dark-elevated/40 hover:text-loomi-ink dark:hover:text-loomi-dark-text'
                  }`}
                  onClick={() => {
                    onSelectSession(session.id);
                    onCloseMobile();
                  }}
                >
                  <div className="flex items-center gap-2 truncate mr-2">
                    <MessageSquare
                      className={`w-3.5 h-3.5 flex-shrink-0 ${
                        isActive ? 'text-loomi-coral' : 'text-loomi-secondary'
                      }`}
                    />
                    <span className="truncate">{session.title}</span>
                  </div>

                  {/* Actions Dropdown Toggle */}
                  <div className="relative">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setActiveMenuId(activeMenuId === session.id ? null : session.id);
                      }}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded-md hover:bg-loomi-sand dark:hover:bg-loomi-dark-surface text-loomi-secondary hover:text-loomi-ink transition-opacity"
                    >
                      <MoreVertical className="w-3.5 h-3.5" />
                    </button>

                    {activeMenuId === session.id && (
                      <div
                        onClick={(e) => e.stopPropagation()}
                        className="absolute right-0 top-6 z-30 w-28 py-1 rounded-xl bg-white dark:bg-loomi-dark-surface border border-loomi-border dark:border-loomi-dark-border shadow-warm-lg text-xs"
                      >
                        <button
                          onClick={() => startRename(session)}
                          className="w-full px-2.5 py-1.5 text-left flex items-center gap-1.5 hover:bg-loomi-sand/40 dark:hover:bg-loomi-dark-elevated text-loomi-ink dark:text-loomi-dark-text"
                        >
                          <Edit2 className="w-3 h-3 text-loomi-secondary" />
                          <span>Rename</span>
                        </button>
                        <button
                          onClick={() => {
                            setConfirmDeleteId(session.id);
                            setActiveMenuId(null);
                          }}
                          className="w-full px-2.5 py-1.5 text-left flex items-center gap-1.5 hover:bg-rose-50 dark:hover:bg-rose-950/30 text-rose-600"
                        >
                          <Trash2 className="w-3 h-3" />
                          <span>Delete</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* Bottom: Knowledge Base Library Section */}
        <div className="p-3 border-t border-loomi-border/60 dark:border-loomi-dark-border/60 bg-loomi-ivory/40 dark:bg-loomi-dark-bg/40">
          <button
            onClick={() => setShowDocLibrary(!showDocLibrary)}
            className="w-full flex items-center justify-between text-xs p-2 rounded-xl hover:bg-loomi-sand/50 dark:hover:bg-loomi-dark-elevated text-loomi-secondary dark:text-loomi-dark-muted transition-colors"
          >
            <div className="flex items-center gap-2">
              <Database className="w-3.5 h-3.5 text-loomi-coral" />
              <span className="font-semibold text-loomi-ink dark:text-loomi-dark-text">
                Knowledge Base
              </span>
            </div>
            <div className="flex items-center gap-1 text-[11px]">
              <span className="px-1.5 py-0.5 rounded-full bg-loomi-sand dark:bg-loomi-dark-elevated font-mono">
                {indexedFiles.length} file{indexedFiles.length === 1 ? '' : 's'} {indexedCount > 0 ? `(${indexedCount})` : ''}
              </span>
              <ChevronRight
                className={`w-3.5 h-3.5 transition-transform ${
                  showDocLibrary ? 'rotate-90' : ''
                }`}
              />
            </div>
          </button>

          {showDocLibrary && (
            <div className="mt-2 max-h-36 overflow-y-auto space-y-1 pl-2">
              {indexedFiles.length === 0 ? (
                <p className="text-[11px] text-loomi-secondary/70 italic py-1">
                  No documents indexed yet.
                </p>
              ) : (
                indexedFiles.map((file, idx) => (
                  <div
                    key={idx}
                    className="flex items-center gap-1.5 text-[11px] text-loomi-ink dark:text-loomi-dark-text truncate py-0.5"
                    title={file}
                  >
                    <FileText className="w-3 h-3 text-loomi-coral flex-shrink-0" />
                    <span className="truncate">{file}</span>
                  </div>
                ))
              )}
            </div>
          )}
        </div>
      </aside>
    </>
  );
};
