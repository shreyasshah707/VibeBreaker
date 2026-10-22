'use client';

import { useState, useCallback } from 'react';
import Header from '@/components/Header';
import PasteCodeScreen from '@/components/PasteCodeScreen';
import LearningWorkspace from '@/components/LearningWorkspace';
import SummaryScreen from '@/components/SummaryScreen';
import {
  createSession,
  generateSessionFromPrompt,
  getSession,
  finishSession,
  SessionState,
  ReflectionResponse,
} from '@/lib/api';

type AppScreen = 'paste' | 'workspace' | 'summary';

export default function Home() {
  const [screen, setScreen] = useState<AppScreen>('paste');
  const [session, setSession] = useState<SessionState | null>(null);
  const [reflection, setReflection] = useState<ReflectionResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCreateSession = useCallback(async (code: string, title: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const created = await createSession(code, title);
      const state = await getSession(created.session_id);
      setSession(state);
      setScreen('workspace');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create session');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleGenerateFromPrompt = useCallback(async (prompt: string, title: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const created = await generateSessionFromPrompt(prompt, title);
      const state = await getSession(created.session_id);
      setSession(state);
      setScreen('workspace');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate algorithm from prompt');
    } finally {
      setIsLoading(false);
    }
  }, []);

  const handleSessionUpdate = useCallback((updatedSession: SessionState) => {
    setSession(updatedSession);
  }, []);

  const handleComplete = useCallback(async () => {
    if (!session) return;
    setIsLoading(true);
    try {
      const result = await finishSession(session.session_id);
      setReflection(result);
      setScreen('summary');
    } catch (err) {
      // If reflection endpoint fails, still show a clean fallback summary
      setReflection({
        session_id: session.session_id,
        patterns_practiced: ['Code reconstruction', 'Function design'],
        hint_usage: {},
        weak_areas: ['Boundary conditions'],
        viva_questions: ['What key concepts did you reconstruct in this session?'],
        completed_steps: session.steps ? session.steps.filter(s => s.status === 'completed').length : 0,
        total_steps: session.total_steps || (session.steps ? session.steps.length : 1),
      });
      setScreen('summary');
    } finally {
      setIsLoading(false);
    }
  }, [session]);

  const handleNewSession = useCallback(() => {
    setSession(null);
    setReflection(null);
    setError(null);
    setScreen('paste');
  }, []);

  const handleBack = useCallback(() => {
    if (screen === 'workspace') {
      if (window.confirm('Leave this session? Your progress will be saved.')) {
        handleNewSession();
      }
    } else {
      handleNewSession();
    }
  }, [screen, handleNewSession]);

  return (
    <div className="min-h-screen bg-vibe-bg">
      <Header
        sessionTitle={session?.title}
        showBack={screen !== 'paste'}
        onBack={handleBack}
      />

      {error && (
        <div className="max-w-3xl mx-auto mt-4 px-6">
          <div className="bg-vibe-error/10 border border-vibe-error/30 rounded-lg p-4 text-sm text-vibe-error flex items-center gap-3">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            {error}
            <button onClick={() => setError(null)} className="ml-auto text-vibe-error hover:text-white">
              ✕
            </button>
          </div>
        </div>
      )}

      {screen === 'paste' && (
        <PasteCodeScreen
          onSubmit={handleCreateSession}
          onGenerate={handleGenerateFromPrompt}
          isLoading={isLoading}
        />
      )}

      {screen === 'workspace' && session && (
        <LearningWorkspace
          session={session}
          onSessionUpdate={handleSessionUpdate}
          onComplete={handleComplete}
        />
      )}

      {screen === 'summary' && reflection && (
        <SummaryScreen reflection={reflection} onNewSession={handleNewSession} />
      )}

      {/* Loading overlay for session creation */}
      {isLoading && screen === 'paste' && (
        <div className="fixed inset-0 bg-vibe-bg/80 backdrop-blur-sm flex items-center justify-center z-50">
          <div className="text-center">
            <div className="w-12 h-12 border-4 border-vibe-accent/30 border-t-vibe-accent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-vibe-text font-medium">Breaking the vibe…</p>
            <p className="text-vibe-textMuted text-sm mt-1">Analyzing your code and creating objectives</p>
          </div>
        </div>
      )}
    </div>
  );
}