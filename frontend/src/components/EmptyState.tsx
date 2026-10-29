import React from 'react';
import { Sparkles, ArrowRight, BookOpen } from 'lucide-react';

interface EmptyStateProps {
  onSelectPrompt: (prompt: string) => void;
  indexedCount?: number;
}

const PROMPT_SUGGESTIONS = [
  {
    title: 'Explore my PDFs',
    desc: 'Synthesize findings and facts from uploaded research docs',
  },
  {
    title: 'Explain RAG simply',
    desc: 'How vector databases and LLMs cooperate to ground answers',
  },
  {
    title: 'Compare vector search vs keyword search',
    desc: 'Trade-offs between dense semantic retrieval and BM25',
  },
  {
    title: 'Research recent breakthroughs in AI agents',
    desc: 'Search the live web for state-of-the-art agent architectures',
  },
];

export const EmptyState: React.FC<EmptyStateProps> = ({ onSelectPrompt, indexedCount = 0 }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4 max-w-2xl mx-auto animate-fadeIn">
      {/* Brand Icon */}
      <div className="relative mb-6">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-loomi-coral to-amber-500 text-white flex items-center justify-center shadow-coral-glow mx-auto transform -rotate-3 transition-transform hover:rotate-0 duration-300">
          <Sparkles className="w-8 h-8" />
        </div>
        <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 border-2 border-loomi-ivory dark:border-loomi-dark-bg" title="Online" />
      </div>

      {/* Heading */}
      <h1 className="font-serif text-3xl sm:text-4xl font-semibold tracking-tight text-loomi-ink dark:text-loomi-dark-text mb-3">
        Curiosity looks good on you.
      </h1>

      {/* Supporting Text */}
      <p className="text-sm sm:text-base text-loomi-secondary dark:text-loomi-dark-muted max-w-lg mb-6 leading-relaxed">
        Loomi weaves your uploaded documents and live web knowledge into grounded, authoritative research answers.
      </p>

      {/* Knowledge Base Status Badge */}
      {indexedCount > 0 && (
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-loomi-coral-light dark:bg-loomi-coral/15 text-loomi-coral border border-loomi-coral/30 mb-8">
          <BookOpen className="w-3.5 h-3.5" />
          <span>{indexedCount} document chunk{indexedCount > 1 ? 's' : ''} indexed in ChromaDB</span>
        </div>
      )}

      {/* Suggested Prompts Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full text-left">
        {PROMPT_SUGGESTIONS.map((sug, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt(sug.title)}
            className="p-3.5 rounded-2xl bg-white dark:bg-loomi-dark-surface border border-loomi-border dark:border-loomi-dark-border hover:border-loomi-coral/60 dark:hover:border-loomi-coral/60 hover:shadow-warm transition-all duration-200 group flex items-start justify-between"
          >
            <div>
              <div className="text-xs font-semibold text-loomi-ink dark:text-loomi-dark-text group-hover:text-loomi-coral transition-colors">
                {sug.title}
              </div>
              <div className="text-[11px] text-loomi-secondary dark:text-loomi-dark-muted mt-0.5 line-clamp-1">
                {sug.desc}
              </div>
            </div>
            <ArrowRight className="w-3.5 h-3.5 text-loomi-secondary dark:text-loomi-dark-muted group-hover:text-loomi-coral group-hover:translate-x-0.5 transition-all mt-0.5 flex-shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
};
