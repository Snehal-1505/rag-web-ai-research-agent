import React from 'react';
import { Loader2, Sparkles, BookOpen, Globe, CheckCircle2 } from 'lucide-react';
import { ResearchStage } from '../types/chat';

interface ResearchStatusProps {
  stage: ResearchStage;
  strategy?: string | null;
}

export const ResearchStatus: React.FC<ResearchStatusProps> = ({ stage, strategy }) => {
  if (stage === 'idle') return null;

  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium bg-loomi-sand/70 dark:bg-loomi-dark-elevated border border-loomi-border dark:border-loomi-dark-border text-loomi-secondary dark:text-loomi-dark-muted shadow-sm animate-pulse">
      {stage === 'searching' && (
        <>
          <Loader2 className="w-3.5 h-3.5 animate-spin text-loomi-coral" />
          {strategy === 'documents' && (
            <span className="flex items-center gap-1">
              <BookOpen className="w-3 h-3 text-loomi-coral" />
              Retrieving document chunks…
            </span>
          )}
          {strategy === 'web' && (
            <span className="flex items-center gap-1">
              <Globe className="w-3 h-3 text-blue-500" />
              Researching live web…
            </span>
          )}
          {(!strategy || strategy === 'hybrid') && (
            <span className="flex items-center gap-1">
              <Sparkles className="w-3 h-3 text-amber-500" />
              Gathering document & web research…
            </span>
          )}
        </>
      )}

      {stage === 'generating' && (
        <>
          <Sparkles className="w-3.5 h-3.5 text-loomi-coral animate-bounce" />
          <span>Synthesizing authoritative answer…</span>
        </>
      )}

      {stage === 'done' && (
        <>
          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
          <span className="text-emerald-700 dark:text-emerald-300">Research synthesized</span>
        </>
      )}
    </div>
  );
};
