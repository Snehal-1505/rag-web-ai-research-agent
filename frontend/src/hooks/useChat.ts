import { useState, useEffect, useRef, useCallback } from 'react';
import { Message, ResearchStage, DocSource, WebSource } from '../types/chat';
import { fetchSession } from '../services/api';

export function useChat(activeSessionId: string | null, onSessionUpdated?: () => void) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoadingSession, setIsLoadingSession] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [researchStage, setResearchStage] = useState<ResearchStage>('idle');
  const [researchStrategy, setResearchStrategy] = useState<string | null>(null);
  const [activeSources, setActiveSources] = useState<{
    documents: DocSource[];
    web: WebSource[];
  } | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  // Load messages when activeSessionId changes
  useEffect(() => {
    if (!activeSessionId) {
      setMessages([]);
      return;
    }

    let isMounted = true;
    setIsLoadingSession(true);

    fetchSession(activeSessionId)
      .then((detail) => {
        if (isMounted) {
          setMessages(detail.messages || []);
        }
      })
      .catch((err) => {
        console.error('Error loading session messages:', err);
      })
      .finally(() => {
        if (isMounted) {
          setIsLoadingSession(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [activeSessionId]);

  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsGenerating(false);
    setResearchStage('idle');
  }, []);

  const sendMessage = useCallback(
    async (question: string, topKDocs: number = 5, maxWebResults: number = 5) => {
      if (!question.trim() || isGenerating) return;

      const userMsgId = `temp-user-${Date.now()}`;
      const assistantMsgId = `temp-asst-${Date.now()}`;

      const userMsg: Message = {
        id: userMsgId,
        role: 'user',
        content: question,
        timestamp: new Date().toISOString(),
      };

      const pendingAsstMsg: Message = {
        id: assistantMsgId,
        role: 'assistant',
        content: '',
        timestamp: new Date().toISOString(),
        metadata: {},
      };

      setMessages((prev) => [...prev, userMsg, pendingAsstMsg]);
      setIsGenerating(true);
      setResearchStage('searching');
      setResearchStrategy(null);
      setActiveSources(null);

      const abortController = new AbortController();
      abortControllerRef.current = abortController;

      let accumulatedText = '';
      let currentStrategy = 'hybrid';
      let docResults: DocSource[] = [];
      let webResults: WebSource[] = [];

      try {
        const response = await fetch('/api/chat/stream', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: activeSessionId,
            question,
            top_k_docs: topKDocs,
            max_web_results: maxWebResults,
          }),
          signal: abortController.signal,
        });

        if (!response.ok || !response.body) {
          throw new Error(`Streaming failed with status ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n\n');
          buffer = lines.pop() || '';

          for (const block of lines) {
            if (!block.trim()) continue;
            const eventMatch = block.match(/^event:\s*(.+)$/m);
            const dataMatch = block.match(/^data:\s*(.+)$/m);

            if (eventMatch && dataMatch) {
              const eventType = eventMatch[1].trim();
              const eventData = JSON.parse(dataMatch[1].trim());

              if (eventType === 'status') {
                if (eventData.stage === 'generating') {
                  setResearchStage('generating');
                } else if (eventData.stage === 'searching') {
                  setResearchStage('searching');
                }
                if (eventData.strategy) {
                  currentStrategy = eventData.strategy;
                  setResearchStrategy(eventData.strategy);
                }
              } else if (eventType === 'sources') {
                docResults = eventData.doc_results || [];
                webResults = eventData.web_results || [];
                currentStrategy = eventData.strategy || currentStrategy;
                setActiveSources({ documents: docResults, web: webResults });
              } else if (eventType === 'delta') {
                const chunk = eventData.text || '';
                accumulatedText += chunk;

                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMsgId
                      ? {
                          ...msg,
                          content: accumulatedText,
                          metadata: {
                            strategy: currentStrategy,
                            doc_results: docResults,
                            web_results: webResults,
                          },
                        }
                      : msg
                  )
                );
              } else if (eventType === 'done') {
                setResearchStage('done');
                if (onSessionUpdated) onSessionUpdated();
              }
            }
          }
        }
      } catch (err: any) {
        if (err.name === 'AbortError') {
          console.log('Stream generation aborted by user.');
        } else {
          console.warn('Streaming error, falling back to standard chat:', err);
          // Fallback to standard chat endpoint if streaming fails
          try {
            const fallbackRes = await fetch('/api/chat', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                session_id: activeSessionId,
                question,
                top_k_docs: topKDocs,
                max_web_results: maxWebResults,
              }),
            });
            if (fallbackRes.ok) {
              const fbData = await fallbackRes.json();
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.id === assistantMsgId
                    ? {
                        ...msg,
                        content: fbData.answer,
                        metadata: {
                          strategy: fbData.strategy,
                          doc_results: fbData.sources?.documents || [],
                          web_results: fbData.sources?.web || [],
                        },
                      }
                    : msg
                )
              );
            }
          } catch (fbErr) {
            setMessages((prev) =>
              prev.map((msg) =>
                msg.id === assistantMsgId
                  ? {
                      ...msg,
                      content: 'Something went wrong while generating the answer. Please try again.',
                    }
                  : msg
              )
            );
          }
        }
      } finally {
        setIsGenerating(false);
        abortControllerRef.current = null;
        setTimeout(() => {
          setResearchStage('idle');
        }, 3000);
      }
    },
    [activeSessionId, isGenerating, onSessionUpdated]
  );

  return {
    messages,
    isLoadingSession,
    isGenerating,
    researchStage,
    researchStrategy,
    activeSources,
    sendMessage,
    stopGeneration,
  };
}
