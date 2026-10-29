import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Paperclip, Square } from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (text: string) => void;
  onOpenUpload: () => void;
  onStopGeneration?: () => void;
  isGenerating?: boolean;
  disabled?: boolean;
}

export const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  onOpenUpload,
  onStopGeneration,
  isGenerating = false,
  disabled = false,
}) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea based on input content
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isGenerating || disabled) return;

    onSendMessage(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto px-4 pb-4 pt-1">
      <form
        onSubmit={handleSubmit}
        className="relative flex items-end gap-2 p-2 rounded-2xl bg-white dark:bg-loomi-dark-surface border border-loomi-border dark:border-loomi-dark-border shadow-warm-lg focus-within:border-loomi-coral focus-within:ring-2 focus-within:ring-loomi-coral/20 transition-all duration-200"
      >
        {/* Document Upload / Attachment Button */}
        <button
          type="button"
          onClick={onOpenUpload}
          disabled={disabled}
          className="p-2.5 rounded-xl text-loomi-secondary dark:text-loomi-dark-muted hover:text-loomi-coral dark:hover:text-loomi-dark-coral hover:bg-loomi-sand/40 dark:hover:bg-loomi-dark-elevated transition-colors flex-shrink-0"
          title="Attach document to knowledge base (.pdf, .txt, .docx)"
        >
          <Paperclip className="w-4 h-4" />
        </button>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask anything or explore uploaded documents…"
          rows={1}
          disabled={disabled}
          className="flex-1 max-h-40 py-2.5 px-1 bg-transparent text-sm text-loomi-ink dark:text-loomi-dark-text placeholder:text-loomi-secondary/70 dark:placeholder:text-loomi-dark-muted/70 focus:outline-none resize-none leading-relaxed"
        />

        {/* Send / Stop Action Button */}
        {isGenerating ? (
          <button
            type="button"
            onClick={onStopGeneration}
            className="p-2.5 rounded-xl bg-loomi-coral text-white hover:bg-loomi-coral-hover transition-colors flex-shrink-0 shadow-sm"
            title="Stop generation"
          >
            <Square className="w-4 h-4 fill-white" />
          </button>
        ) : (
          <button
            type="submit"
            disabled={!input.trim() || disabled}
            className="p-2.5 rounded-xl bg-loomi-ink dark:bg-loomi-coral text-white hover:bg-loomi-coral dark:hover:bg-loomi-coral-hover disabled:opacity-30 disabled:cursor-not-allowed transition-all flex-shrink-0 shadow-sm"
            title="Send question (Enter)"
          >
            <ArrowUp className="w-4 h-4" />
          </button>
        )}
      </form>
      <div className="flex items-center justify-between mt-1.5 px-3 text-[10px] text-loomi-secondary dark:text-loomi-dark-muted">
        <span>Press <kbd className="px-1 py-0.5 rounded bg-loomi-sand/60 dark:bg-loomi-dark-elevated font-mono">Enter</kbd> to send, <kbd className="px-1 py-0.5 rounded bg-loomi-sand/60 dark:bg-loomi-dark-elevated font-mono">Shift+Enter</kbd> for newline</span>
        <span>Loomi AI · Research Agent</span>
      </div>
    </div>
  );
};
