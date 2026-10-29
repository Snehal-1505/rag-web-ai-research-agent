import { useState, useEffect, useCallback } from 'react';
import { Session } from '../types/chat';
import { fetchSessions, createSession, renameSession, deleteSession } from '../services/api';

export function useSessions() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(() => {
    return localStorage.getItem('loomi-active-session') || null;
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSessions = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await fetchSessions();
      setSessions(data);
      if (data.length > 0 && !activeSessionId) {
        // default to newest session if none selected
        setActiveSessionId(data[0].id);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load conversations.');
    } finally {
      setIsLoading(false);
    }
  }, [activeSessionId]);

  useEffect(() => {
    loadSessions();
  }, []);

  useEffect(() => {
    if (activeSessionId) {
      localStorage.setItem('loomi-active-session', activeSessionId);
    } else {
      localStorage.removeItem('loomi-active-session');
    }
  }, [activeSessionId]);

  const handleCreateSession = async (title?: string): Promise<string> => {
    try {
      const newSession = await createSession(title);
      setSessions((prev) => [newSession, ...prev]);
      setActiveSessionId(newSession.id);
      return newSession.id;
    } catch (err: any) {
      setError(err.message || 'Could not create new chat.');
      throw err;
    }
  };

  const handleRenameSession = async (sessionId: string, newTitle: string) => {
    try {
      const updated = await renameSession(sessionId, newTitle);
      setSessions((prev) =>
        prev.map((s) => (s.id === sessionId ? { ...s, title: updated.title } : s))
      );
    } catch (err: any) {
      setError(err.message || 'Failed to rename conversation.');
    }
  };

  const handleDeleteSession = async (sessionId: string) => {
    try {
      await deleteSession(sessionId);
      const remaining = sessions.filter((s) => s.id !== sessionId);
      setSessions(remaining);
      if (activeSessionId === sessionId) {
        setActiveSessionId(remaining.length > 0 ? remaining[0].id : null);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to delete conversation.');
    }
  };

  const selectSession = (id: string | null) => {
    setActiveSessionId(id);
  };

  return {
    sessions,
    activeSessionId,
    isLoading,
    error,
    loadSessions,
    createSession: handleCreateSession,
    renameSession: handleRenameSession,
    deleteSession: handleDeleteSession,
    selectSession,
  };
}
