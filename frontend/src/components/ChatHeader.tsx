import React, { useState } from 'react';
import { Menu, UploadCloud, Edit2, Check, X } from 'lucide-react';
import { ThemeToggle } from './ThemeToggle';
import { Session } from '../types/chat';

interface ChatHeaderProps {
  activeSession?: Session;
  onRenameSession?: (id: string, newTitle: string) => void;
  onOpenUpload: () => void;
  onToggleSidebar: () => void;
  isOnline?: boolean;
}

export const ChatHeader: React.FC<ChatHeaderProps> = ({
  activeSession,
  onRenameSession,
  onOpenUpload,
  onToggleSidebar,
  isOnline = true,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [title, setTitle] = useState('');

  const handleStartEdit = () => {
    if (activeSession) {
      setTitle(activeSession.title);
      setIsEditing(true);
    }
  };

  const handleSave = () => {
    if (activeSession && title.trim() && onRenameSession) {
      onRenameSession(activeSession.id, title.trim());
    }
    setIsEditing(false);
  };

  return (
    <header className="sticky top-0 z-20 flex items-center justify-between px-4 py-3 bg-loomi-ivory/80 dark:bg-loomi-dark-bg/80 backdrop-blur-md border-b border-loomi-border/60 dark:border-loomi-dark-border/60">
      <div className="flex items-center gap-3 min-w-0">
        {/* Mobile menu button */}
        <button
          onClick={onToggleSidebar}
          aria-label="Toggle menu"
          className="p-1.5 rounded-xl text-loomi-secondary hover:text-loomi-ink dark:hover:text-loomi-dark-text md:hidden hover:bg-loomi-sand/40"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Brand or Active Session Title */}
        <div className="flex items-center gap-2 min-w-0">
          <div
            className={`w-2.5 h-2.5 rounded-full ${
              isOnline ? 'bg-emerald-500 ring-4 ring-emerald-500/20' : 'bg-amber-500 ring-4 ring-amber-500/20'
            } flex-shrink-0`}
            title={isOnline ? 'RAG system active' : 'Offline'}
          />

          {isEditing ? (
            <div className="flex items-center gap-1.5">
              <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleSave();
                  if (e.key === 'Escape') setIsEditing(false);
                }}
                autoFocus
                className="px-2 py-0.5 rounded-lg border border-loomi-coral bg-white dark:bg-loomi-dark-surface text-sm font-semibold text-loomi-ink dark:text-loomi-dark-text focus:outline-none"
              />
              <button onClick={handleSave} className="text-emerald-600 hover:bg-white dark:hover:bg-black p-1 rounded">
                <Check className="w-4 h-4" />
              </button>
              <button onClick={() => setIsEditing(false)} className="text-rose-500 hover:bg-white dark:hover:bg-black p-1 rounded">
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 truncate group cursor-pointer" onClick={handleStartEdit}>
              <h1 className="text-sm font-semibold text-loomi-ink dark:text-loomi-dark-text truncate">
                {activeSession ? activeSession.title : 'Research Workspace'}
              </h1>
              {activeSession && (
                <Edit2 className="w-3 h-3 text-loomi-secondary opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
              )}
            </div>
          )}
        </div>
      </div>

      {/* Right Controls */}
      <div className="flex items-center gap-2">
        <button
          onClick={onOpenUpload}
          className="hidden sm:flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium border border-loomi-border dark:border-loomi-dark-border bg-white dark:bg-loomi-dark-surface hover:border-loomi-coral/60 hover:text-loomi-coral text-loomi-ink dark:text-loomi-dark-text shadow-xs transition-colors"
        >
          <UploadCloud className="w-3.5 h-3.5 text-loomi-coral" />
          <span>Attach PDF/Doc</span>
        </button>

        <ThemeToggle />
      </div>
    </header>
  );
};
