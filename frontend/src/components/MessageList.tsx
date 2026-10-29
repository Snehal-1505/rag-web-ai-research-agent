import React, { useEffect, useRef } from 'react';
import { Message, ResearchStage } from '../types/chat';
import { MessageBubble } from './MessageBubble';
import { EmptyState } from './EmptyState';
import { ResearchStatus } from './ResearchStatus';

interface MessageListProps {
  messages: Message[];
  researchStage: ResearchStage;
  researchStrategy?: string | null;
  onSelectPrompt: (prompt: string) => void;
  indexedCount?: number;
}

export const MessageList: React.FC<MessageListProps> = ({
  messages,
  researchStage,
  researchStrategy,
  onSelectPrompt,
  indexedCount = 0,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, researchStage]);

  if (messages.length === 0) {
    return <EmptyState onSelectPrompt={onSelectPrompt} indexedCount={indexedCount} />;
  }

  return (
    <div className="flex-1 overflow-y-auto px-4 py-6 max-w-3xl w-full mx-auto">
      {messages.map((msg) => (
        <MessageBubble key={msg.id} message={msg} />
      ))}

      {/* Real-time Research Stage Indicator */}
      {researchStage !== 'idle' && (
        <div className="my-3 flex justify-start pl-11">
          <ResearchStatus stage={researchStage} strategy={researchStrategy} />
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
};
