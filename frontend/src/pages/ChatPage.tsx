import React, { useState, useEffect } from 'react';
import { Sidebar } from '../components/Sidebar';
import { ChatHeader } from '../components/ChatHeader';
import { MessageList } from '../components/MessageList';
import { ChatInput } from '../components/ChatInput';
import { DocumentUpload } from '../components/DocumentUpload';
import { useSessions } from '../hooks/useSessions';
import { useChat } from '../hooks/useChat';
import { fetchHealth } from '../services/api';
import { HealthInfo } from '../types/chat';

export const ChatPage: React.FC = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [uploadOpen, setUploadOpen] = useState(false);
  const [healthInfo, setHealthInfo] = useState<HealthInfo | null>(null);

  const {
    sessions,
    activeSessionId,
    loadSessions,
    createSession,
    renameSession,
    deleteSession,
    selectSession,
  } = useSessions();

  const {
    messages,
    isGenerating,
    researchStage,
    researchStrategy,
    sendMessage,
    stopGeneration,
  } = useChat(activeSessionId, loadSessions);

  // Load real backend health & indexed documents stats
  const refreshHealth = () => {
    fetchHealth()
      .then(setHealthInfo)
      .catch((err) => console.warn('Could not fetch health stats:', err));
  };

  useEffect(() => {
    refreshHealth();
  }, []);

  const activeSession = sessions.find((s) => s.id === activeSessionId);

  const handleNewChat = async () => {
    try {
      await createSession();
    } catch (err) {
      console.error(err);
    }
  };

  const handleSendMessage = async (text: string) => {
    // If no session exists yet, create one first
    if (!activeSessionId) {
      try {
        const newId = await createSession();
        selectSession(newId);
        // Next tick after session is created
        setTimeout(() => {
          sendMessage(text);
        }, 50);
      } catch (err) {
        console.error(err);
      }
    } else {
      sendMessage(text);
    }
  };

  return (
    <div className="flex h-screen w-full bg-loomi-ivory dark:bg-loomi-dark-bg text-loomi-ink dark:text-loomi-dark-text overflow-hidden">
      {/* Collapsible Left Sidebar */}
      <Sidebar
        sessions={sessions}
        activeSessionId={activeSessionId}
        onSelectSession={selectSession}
        onNewChat={handleNewChat}
        onRenameSession={renameSession}
        onDeleteSession={deleteSession}
        indexedCount={healthInfo?.indexed_documents || 0}
        indexedFiles={healthInfo?.indexed_files || []}
        isOpen={sidebarOpen}
        onCloseMobile={() => setSidebarOpen(false)}
      />

      {/* Main Chat Workspace */}
      <div className="flex-1 flex flex-col h-full min-w-0 relative">
        <ChatHeader
          activeSession={activeSession}
          onRenameSession={renameSession}
          onOpenUpload={() => setUploadOpen(true)}
          onToggleSidebar={() => setSidebarOpen(!sidebarOpen)}
          isOnline={healthInfo?.status === 'ok'}
        />

        {/* Upload Modal / Backdrop */}
        {uploadOpen && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-xs">
            <div className="w-full max-w-md animate-scaleUp">
              <DocumentUpload
                sessionId={activeSessionId}
                onUploadSuccess={() => {
                  refreshHealth();
                  setTimeout(() => setUploadOpen(false), 2000);
                }}
                onClose={() => setUploadOpen(false)}
              />
            </div>
          </div>
        )}

        {/* Message Stream Area */}
        <main className="flex-1 overflow-hidden flex flex-col">
          <MessageList
            messages={messages}
            researchStage={researchStage}
            researchStrategy={researchStrategy}
            onSelectPrompt={handleSendMessage}
            indexedCount={healthInfo?.indexed_documents || 0}
          />

          {/* Floating Composer */}
          <ChatInput
            onSendMessage={handleSendMessage}
            onOpenUpload={() => setUploadOpen(true)}
            onStopGeneration={stopGeneration}
            isGenerating={isGenerating}
          />
        </main>
      </div>
    </div>
  );
};
