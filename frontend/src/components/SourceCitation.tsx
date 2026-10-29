import React, { useState } from 'react';
import { FileText, Globe, ExternalLink, ChevronDown, ChevronUp } from 'lucide-react';
import { DocSource, WebSource } from '../types/chat';

interface SourceCitationProps {
  docResults?: DocSource[];
  webResults?: WebSource[];
}

export const SourceCitation: React.FC<SourceCitationProps> = ({
  docResults = [],
  webResults = [],
}) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const totalSources = docResults.length + webResults.length;

  if (totalSources === 0) return null;

  return (
    <div className="mt-3 pt-3 border-t border-loomi-border/60 dark:border-loomi-dark-border/60 text-xs">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="flex items-center gap-1.5 text-loomi-secondary dark:text-loomi-dark-muted hover:text-loomi-ink dark:hover:text-loomi-dark-text transition-colors font-medium group"
      >
        <span className="flex items-center gap-1">
          {docResults.length > 0 && <FileText className="w-3.5 h-3.5 text-loomi-coral" />}
          {webResults.length > 0 && <Globe className="w-3.5 h-3.5 text-blue-500" />}
          <span>
            {totalSources} source{totalSources > 1 ? 's' : ''} consulted
          </span>
        </span>
        {isExpanded ? (
          <ChevronUp className="w-3.5 h-3.5 text-loomi-secondary" />
        ) : (
          <ChevronDown className="w-3.5 h-3.5 text-loomi-secondary" />
        )}
      </button>

      {isExpanded && (
        <div className="mt-2.5 grid grid-cols-1 sm:grid-cols-2 gap-2 animate-fadeIn">
          {/* Document Sources */}
          {docResults.map((doc, idx) => (
            <div
              key={`doc-${idx}`}
              className="p-2.5 rounded-xl bg-loomi-sand/40 dark:bg-loomi-dark-elevated/40 border border-loomi-border/70 dark:border-loomi-dark-border/70 flex flex-col justify-between"
            >
              <div className="flex items-start gap-1.5">
                <FileText className="w-3.5 h-3.5 text-loomi-coral flex-shrink-0 mt-0.5" />
                <div className="min-w-0">
                  <div className="font-semibold text-loomi-ink dark:text-loomi-dark-text truncate">
                    {doc.filename}
                  </div>
                  <div className="text-[11px] text-loomi-secondary dark:text-loomi-dark-muted">
                    Page {doc.page || 1}
                  </div>
                </div>
              </div>
              {doc.content && (
                <p className="mt-1.5 text-[11px] text-loomi-secondary dark:text-loomi-dark-muted line-clamp-2 leading-relaxed italic bg-white/40 dark:bg-black/20 p-1.5 rounded-lg">
                  "{doc.content.trim()}"
                </p>
              )}
            </div>
          ))}

          {/* Web Sources */}
          {webResults.map((web, idx) => {
            let domain = '';
            try {
              if (web.url) domain = new URL(web.url).hostname.replace('www.', '');
            } catch (_) {
              domain = 'web';
            }

            return (
              <div
                key={`web-${idx}`}
                className="p-2.5 rounded-xl bg-loomi-sand/40 dark:bg-loomi-dark-elevated/40 border border-loomi-border/70 dark:border-loomi-dark-border/70 flex flex-col justify-between"
              >
                <div className="flex items-start justify-between gap-1.5">
                  <div className="flex items-start gap-1.5 min-w-0">
                    <Globe className="w-3.5 h-3.5 text-blue-500 flex-shrink-0 mt-0.5" />
                    <div className="min-w-0">
                      <div className="font-semibold text-loomi-ink dark:text-loomi-dark-text truncate">
                        {web.title || domain}
                      </div>
                      <div className="text-[11px] text-loomi-secondary dark:text-loomi-dark-muted truncate">
                        {domain}
                      </div>
                    </div>
                  </div>
                  {web.url && (
                    <a
                      href={web.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-loomi-secondary hover:text-loomi-coral transition-colors p-0.5"
                      title="Open source link"
                    >
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </div>
                {web.content && (
                  <p className="mt-1.5 text-[11px] text-loomi-secondary dark:text-loomi-dark-muted line-clamp-2 leading-relaxed italic bg-white/40 dark:bg-black/20 p-1.5 rounded-lg">
                    "{web.content.trim()}"
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};
