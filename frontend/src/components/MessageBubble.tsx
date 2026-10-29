import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check, Sparkles, User } from 'lucide-react';
import { Message } from '../types/chat';
import { SourceCitation } from './SourceCitation';

interface MessageBubbleProps {
  message: Message;
}

export const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === 'user';

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex gap-3 my-4 ${isUser ? 'justify-end' : 'justify-start'}`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-xl bg-gradient-to-br from-loomi-coral to-amber-500 text-white flex items-center justify-center flex-shrink-0 shadow-sm mt-0.5">
          <Sparkles className="w-4 h-4" />
        </div>
      )}

      <div className={`max-w-[85%] md:max-w-[75%] flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div
          className={`p-4 rounded-2xl shadow-sm text-sm ${
            isUser
              ? 'bg-loomi-sand/90 dark:bg-loomi-dark-elevated text-loomi-ink dark:text-loomi-dark-text border border-loomi-border dark:border-loomi-dark-border rounded-br-xs'
              : 'bg-white dark:bg-loomi-dark-surface text-loomi-ink dark:text-loomi-dark-text border border-loomi-border dark:border-loomi-dark-border rounded-bl-xs'
          }`}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap leading-relaxed">{message.content}</p>
          ) : (
            <div className="prose-loomi overflow-hidden">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || '');
                    const codeString = String(children).replace(/\n$/, '');

                    if (!inline && match) {
                      return (
                        <div className="relative my-3 rounded-xl overflow-hidden border border-loomi-border/70 dark:border-loomi-dark-border/70 bg-stone-900 text-stone-100 dark:bg-black/80 font-mono text-xs">
                          <div className="flex items-center justify-between px-3.5 py-1.5 bg-stone-800 dark:bg-stone-900 border-b border-stone-700/60 text-stone-300 text-[11px]">
                            <span className="font-semibold uppercase tracking-wider">{match[1]}</span>
                            <button
                              onClick={() => copyToClipboard(codeString)}
                              className="flex items-center gap-1 hover:text-white transition-colors"
                              title="Copy code"
                            >
                              <Copy className="w-3 h-3" />
                              <span>Copy</span>
                            </button>
                          </div>
                          <pre className="p-3.5 overflow-x-auto leading-relaxed">
                            <code>{children}</code>
                          </pre>
                        </div>
                      );
                    }

                    return (
                      <code
                        className="bg-loomi-sand/60 dark:bg-loomi-dark-elevated px-1.5 py-0.5 rounded text-loomi-coral dark:text-loomi-dark-coral font-mono text-[0.85em]"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  },
                  a({ href, children }) {
                    return (
                      <a
                        href={href}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-loomi-coral hover:underline font-medium break-all"
                      >
                        {children}
                      </a>
                    );
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>

              {/* Citations & Sources */}
              {message.metadata && (
                <SourceCitation
                  docResults={message.metadata.doc_results}
                  webResults={message.metadata.web_results}
                />
              )}
            </div>
          )}
        </div>

        {/* Message Actions */}
        {!isUser && message.content && (
          <div className="flex items-center gap-2 mt-1 px-1">
            <button
              onClick={() => copyToClipboard(message.content)}
              className="flex items-center gap-1 text-[11px] text-loomi-secondary dark:text-loomi-dark-muted hover:text-loomi-ink dark:hover:text-loomi-dark-text transition-colors"
              title="Copy answer"
            >
              {copied ? (
                <>
                  <Check className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                  <span className="text-emerald-600 dark:text-emerald-400 font-medium">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
        )}
      </div>

      {isUser && (
        <div className="w-8 h-8 rounded-xl bg-loomi-sand dark:bg-loomi-dark-elevated text-loomi-secondary dark:text-loomi-dark-muted border border-loomi-border dark:border-loomi-dark-border flex items-center justify-center flex-shrink-0 shadow-sm mt-0.5">
          <User className="w-4 h-4" />
        </div>
      )}
    </div>
  );
};
