'use client';

import { useState, useCallback } from 'react';
import MonacoEditor from './MonacoEditor';
import {
  submitAttempt,
  requestHint,
  revealReferenceCode,
  AttemptResponse,
  HintResponse,
  SessionState,
} from '@/lib/api';

interface LearningWorkspaceProps {
  session: SessionState;
  onSessionUpdate: (session: SessionState) => void;
  onComplete: () => void;
}

interface HintEntry {
  level: string;
  text: string;
}

export default function LearningWorkspace({ session, onSessionUpdate, onComplete }: LearningWorkspaceProps) {
  const [code, setCode] = useState('');
  const [feedback, setFeedback] = useState<{ status: string; text: string } | null>(null);
  const [hints, setHints] = useState<HintEntry[]>([]);
  const [isChecking, setIsChecking] = useState(false);
  const [isHinting, setIsHinting] = useState(false);
  const [currentHintLevel, setCurrentHintLevel] = useState<number>(0); // 0=none, 1=conceptual, 2=narrower, 3=code

  // Reveal Reference Code State
  const [revealedCode, setRevealedCode] = useState<string | null>(null);
  const [showRevealConfirm, setShowRevealConfirm] = useState(false);
  const [isRevealing, setIsRevealing] = useState(false);

  const currentStep = session.steps && session.steps.length > session.current_step_index
    ? session.steps[session.current_step_index]
    : null;
  const completedSteps = session.steps ? session.steps.filter(s => s.status === 'completed').length : 0;

  // Active step algorithm & starter hint
  const currentAlgorithm = currentStep?.algorithm || session.current_objective?.algorithm || '';
  const currentStarterHint = currentStep?.starter_hint || session.current_objective?.starter_hint || '';

  const handleCheck = useCallback(async () => {
    if (!code.trim() || isChecking) return;
    setIsChecking(true);
    setFeedback(null);

    try {
      const result: AttemptResponse = await submitAttempt(session.session_id, code);

      setFeedback({
        status: result.evaluation_status,
        text: result.feedback,
      });

      if (result.evaluation_status === 'pass') {
        if (result.is_complete) {
          onComplete();
        } else {
          // Advance to next step - refresh session state
          const nextIdx = result.next_step_index ?? session.current_step_index + 1;
          const updatedSteps = (session.steps || []).map((step, i) => {
            if (i === session.current_step_index) {
              return { ...step, status: 'completed' as const };
            }
            if (i === nextIdx) {
              return {
                ...step,
                status: 'in_progress' as const,
                algorithm: result.next_algorithm || step.algorithm,
                starter_hint: result.next_starter_hint || step.starter_hint,
              };
            }
            return step;
          });

          onSessionUpdate({
            ...session,
            current_step_index: nextIdx,
            steps: updatedSteps,
            current_objective: {
              objective: result.next_objective || (updatedSteps[nextIdx]?.objective || ''),
              algorithm: result.next_algorithm || updatedSteps[nextIdx]?.algorithm || '',
              starter_hint: result.next_starter_hint || updatedSteps[nextIdx]?.starter_hint || '',
            },
          });

          // Reset step-specific hints (DO NOT clear code terminal: keep progressive code!)
          setHints([]);
          setCurrentHintLevel(0);
          setRevealedCode(null);

          // Keep the pass feedback visible briefly, then clear
          setTimeout(() => setFeedback(null), 3000);
        }
      }
    } catch (err) {
      setFeedback({
        status: 'fail',
        text: err instanceof Error ? err.message : 'Something went wrong.',
      });
    } finally {
      setIsChecking(false);
    }
  }, [code, isChecking, session, onSessionUpdate, onComplete]);

  const handleHint = useCallback(async (level: 'conceptual' | 'narrower' | 'code') => {
    setIsHinting(true);
    try {
      const result: HintResponse = await requestHint(session.session_id, level);
      setHints(prev => [...prev, { level: result.level, text: result.hint }]);

      const levelMap: Record<string, number> = { conceptual: 1, narrower: 2, code: 3 };
      setCurrentHintLevel(levelMap[level] || 0);
    } catch (err) {
      setFeedback({
        status: 'fail',
        text: err instanceof Error ? err.message : 'Could not get hint.',
      });
    } finally {
      setIsHinting(false);
    }
  }, [session.session_id]);

  const handleConfirmReveal = async () => {
    setShowRevealConfirm(false);
    setIsRevealing(true);
    try {
      const res = await revealReferenceCode(session.session_id, session.current_step_index);
      setRevealedCode(res.reference_code || res.full_code || '# No reference code available.');
    } catch (err) {
      setFeedback({
        status: 'fail',
        text: err instanceof Error ? err.message : 'Could not retrieve reference code.',
      });
    } finally {
      setIsRevealing(false);
    }
  };

  // Helper to safely format hints if backend accidentally sent JSON string
  const formatHintText = (text: string) => {
    if (text.startsWith('[') || text.startsWith('{')) {
      try {
        const parsed = JSON.parse(text);
        if (Array.isArray(parsed)) {
          return parsed.map((item, idx) => (
            <div key={idx} className="mb-1">
              • {item.objective || item.learning_concept || JSON.stringify(item)}
            </div>
          ));
        }
        return JSON.stringify(parsed, null, 2);
      } catch {
        return text;
      }
    }
    return text;
  };

  const feedbackColor = feedback?.status === 'pass'
    ? 'border-vibe-success bg-vibe-success/10 text-vibe-success'
    : feedback?.status === 'partial'
      ? 'border-vibe-warning bg-vibe-warning/10 text-vibe-warning'
      : 'border-vibe-error bg-vibe-error/10 text-vibe-error';

  return (
    <div className="h-[calc(100vh-56px)] flex">
      {/* Left: Code Editor */}
      <div className="flex-1 flex flex-col border-r border-vibe-border min-w-0">
        <div className="px-4 py-3 border-b border-vibe-border bg-vibe-surface/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-sm text-vibe-textMuted mono">student_code.py</span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-vibe-accent/10 text-vibe-accent border border-vibe-accent/20">
              Type code matching the algorithm
            </span>
          </div>

          <button
            onClick={handleCheck}
            disabled={!code.trim() || isChecking}
            className="btn-primary text-sm py-1.5 px-4 flex items-center gap-2"
          >
            {isChecking ? (
              <>
                <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                Checking…
              </>
            ) : (
              <>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M20 6L9 17L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
                Check my code
              </>
            )}
          </button>
        </div>

        <div className="flex-1 relative">
          <MonacoEditor value={code} onChange={setCode} />
        </div>
      </div>

      {/* Right: Complete Algorithm, Guidance & Feedback Panel */}
      <div className="w-[480px] flex flex-col bg-vibe-surface/30 overflow-y-auto">
        {/* Step Progress */}
        <div className="px-5 py-4 border-b border-vibe-border">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-vibe-textMuted uppercase tracking-wider">
              Progress
            </span>
            <span className="text-sm font-medium text-vibe-accent">
              Step {session.current_step_index + 1} of {session.total_steps}
            </span>
          </div>
          {/* Progress bar */}
          <div className="w-full h-2 bg-vibe-bg rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-vibe-accent to-purple-500 rounded-full transition-all duration-500"
              style={{ width: `${session.total_steps ? (completedSteps / session.total_steps) * 100 : 0}%` }}
            />
          </div>
          {/* Step indicators */}
          <div className="flex gap-1.5 mt-3">
            {(session.steps || []).map((step, i) => (
              <div
                key={step.id || i}
                className={`flex-1 h-1.5 rounded-full transition-colors ${
                  step.status === 'completed'
                    ? 'bg-vibe-success'
                    : i === session.current_step_index
                      ? 'bg-vibe-accent'
                      : 'bg-vibe-border'
                }`}
                title={`Step ${i + 1}: ${(step.objective || '').slice(0, 50)}...`}
              />
            ))}
          </div>
        </div>

        {/* Feedback Area (Shows immediately when evaluated) */}
        {feedback && (
          <div className="px-5 py-3.5 border-b border-vibe-border animate-fadeIn">
            <div className={`border rounded-lg p-3.5 ${feedbackColor}`}>
              <div className="flex items-center gap-2 mb-1">
                {feedback.status === 'pass' && (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M20 6L9 17L4 12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                )}
                {feedback.status === 'partial' && (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/><path d="M12 8V12M12 16H12.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/></svg>
                )}
                {feedback.status === 'fail' && (
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none"><path d="M18 6L6 18M6 6L18 18" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>
                )}
                <span className="text-xs font-semibold uppercase">
                  {feedback.status === 'pass' ? 'Passed!' : feedback.status === 'partial' ? 'Almost there' : 'Check Objective'}
                </span>
              </div>
              <p className="text-xs opacity-90 leading-relaxed">{feedback.text}</p>
            </div>
          </div>
        )}

        {/* --- COMPLETE ALGORITHM SPECIFICATION (Full multi-stage roadmap) --- */}
        <div className="px-5 py-4 border-b border-vibe-border">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-xs font-bold text-vibe-accent uppercase tracking-wider flex items-center gap-1.5">
              <span>🧠</span> Complete Program Algorithm
            </h3>
            <span className="text-[10px] text-vibe-textMuted bg-vibe-surface px-2 py-0.5 rounded border border-vibe-border">
              {session.total_steps || session.steps?.length || 0} Stages
            </span>
          </div>

          <div className="space-y-3">
            {(session.steps && session.steps.length > 0 ? session.steps : [currentStep]).map((step, idx) => {
              if (!step) return null;
              const isCurrent = idx === session.current_step_index;
              const isCompleted = step.status === 'completed' || idx < session.current_step_index;
              const isUpcoming = !isCurrent && !isCompleted;

              return (
                <div
                  key={step.id || idx}
                  className={`rounded-lg transition-all p-3.5 ${
                    isCurrent
                      ? 'border-2 border-vibe-accent bg-vibe-accent/10 shadow-lg shadow-vibe-accent/5 ring-1 ring-vibe-accent/30'
                      : isCompleted
                        ? 'border border-emerald-500/35 bg-emerald-500/5'
                        : 'border border-vibe-border/60 bg-vibe-bg/40 opacity-75 hover:opacity-100'
                  }`}
                >
                  {/* Step Header */}
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className={`text-xs font-bold ${isCurrent ? 'text-vibe-accent' : isCompleted ? 'text-emerald-400' : 'text-vibe-textMuted'}`}>
                        Step {idx + 1}
                      </span>
                      {isCurrent && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider bg-vibe-accent text-white">
                          Current Objective
                        </span>
                      )}
                      {isCompleted && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase tracking-wider bg-emerald-500/20 text-emerald-400 flex items-center gap-1">
                          ✓ Done
                        </span>
                      )}
                      {isUpcoming && (
                        <span className="px-1.5 py-0.5 rounded text-[10px] font-medium uppercase tracking-wider bg-vibe-surface text-vibe-textMuted border border-vibe-border">
                          Upcoming
                        </span>
                      )}
                    </div>
                    {step.learning_concept && (
                      <span className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/15 text-purple-400 border border-purple-500/20 max-w-[140px] truncate">
                        {step.learning_concept}
                      </span>
                    )}
                  </div>

                  {/* Objective Title */}
                  <p className={`text-xs font-medium mb-2 ${isCurrent ? 'text-white font-semibold' : 'text-vibe-text'}`}>
                    {step.objective}
                  </p>

                  {/* Step Algorithm Specification */}
                  <div className={`p-2.5 rounded text-xs font-mono whitespace-pre-wrap leading-relaxed ${
                    isCurrent
                      ? 'bg-vibe-bg border border-vibe-accent/25 text-vibe-text'
                      : isCompleted
                        ? 'bg-vibe-bg/60 border border-emerald-500/20 text-vibe-textMuted'
                        : 'bg-vibe-bg/40 border border-vibe-border/40 text-vibe-textMuted'
                  }`}>
                    {step.algorithm || '1. Review requirement.\n2. Implement logic.\n3. Return result.'}
                  </div>

                  {/* Current Step Starter Guidance */}
                  {isCurrent && (step.starter_hint || currentStarterHint) && (
                    <div className="mt-2.5 p-2 rounded bg-blue-500/10 border border-blue-500/25 flex items-start gap-1.5">
                      <span className="text-xs">💡</span>
                      <div className="text-[11px] text-blue-300 leading-snug">
                        <span className="font-semibold text-blue-400">Starter Guidance: </span>
                        {step.starter_hint || currentStarterHint}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>


        {/* Need Help? Hint Buttons */}
        <div className="px-5 py-4 border-b border-vibe-border">
          <h3 className="text-xs font-medium text-vibe-textMuted uppercase tracking-wider mb-2.5">
            Need more hints?
          </h3>
          <div className="flex gap-2">
            <button
              onClick={() => handleHint('conceptual')}
              disabled={isHinting || currentHintLevel >= 1}
              className={`btn-secondary text-xs flex-1 py-1.5 ${currentHintLevel >= 1 ? 'opacity-50' : ''}`}
            >
              💡 Conceptual
            </button>
            <button
              onClick={() => handleHint('narrower')}
              disabled={isHinting || currentHintLevel < 1 || currentHintLevel >= 2}
              className={`btn-secondary text-xs flex-1 py-1.5 ${currentHintLevel >= 2 || currentHintLevel < 1 ? 'opacity-50' : ''}`}
            >
              🔍 Narrower
            </button>
            <button
              onClick={() => handleHint('code')}
              disabled={isHinting || currentHintLevel < 2 || currentHintLevel >= 3}
              className={`btn-secondary text-xs flex-1 py-1.5 ${currentHintLevel >= 3 || currentHintLevel < 2 ? 'opacity-50' : ''}`}
            >
              {'</>'} Tiny Code
            </button>
          </div>
          {isHinting && (
            <p className="text-xs text-vibe-textMuted mt-2 animate-pulse">
              Generating hint…
            </p>
          )}
        </div>

        {/* Hint History */}
        {hints.length > 0 && (
          <div className="px-5 py-4 border-b border-vibe-border">
            <h3 className="text-xs font-medium text-vibe-textMuted uppercase tracking-wider mb-2.5">
              Escalated Hints
            </h3>
            <div className="space-y-2.5">
              {hints.map((hint, i) => (
                <div
                  key={i}
                  className="bg-vibe-bg border border-vibe-border rounded-lg p-3 animate-fadeIn"
                >
                  <span className={`inline-block text-[10px] font-semibold uppercase px-1.5 py-0.5 rounded mb-1 ${
                    hint.level === 'conceptual' ? 'bg-blue-500/20 text-blue-400'
                    : hint.level === 'narrower' ? 'bg-yellow-500/20 text-yellow-400'
                    : 'bg-red-500/20 text-red-400'
                  }`}>
                    {hint.level}
                  </span>
                  <div className="text-xs text-vibe-text whitespace-pre-wrap leading-relaxed">
                    {formatHintText(hint.text)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* --- REVEAL REFERENCE CODE SECTION (Hidden by default) --- */}
        <div className="px-5 py-4 mt-auto border-t border-vibe-border bg-vibe-surface/40">
          <div className="flex items-center justify-between">
            <span className="text-[11px] text-vibe-textMuted">
              Stuck? Reference code is kept hidden.
            </span>
            {revealedCode ? (
              <button
                onClick={() => setRevealedCode(null)}
                className="text-xs text-vibe-textMuted hover:text-white transition-colors underline"
              >
                Hide Code
              </button>
            ) : (
              <button
                onClick={() => setShowRevealConfirm(true)}
                disabled={isRevealing}
                className="text-xs font-medium px-2.5 py-1 rounded bg-vibe-bg border border-vibe-border hover:border-vibe-accent text-vibe-text hover:text-vibe-accent transition-all flex items-center gap-1.5"
              >
                <span>👁️</span> Reveal Code
              </button>
            )}
          </div>

          {/* Revealed Code Drawer */}
          {revealedCode && (
            <div className="mt-3 bg-vibe-bg border border-vibe-warning/30 rounded-lg p-3 animate-fadeIn">
              <div className="flex items-center justify-between mb-1.5 text-[10px] text-vibe-warning font-semibold uppercase tracking-wider">
                <span>Reference Implementation</span>
                <span className="text-vibe-textMuted font-normal">Step {session.current_step_index + 1}</span>
              </div>
              <pre className="text-xs text-emerald-400 mono whitespace-pre-wrap bg-black/40 p-2.5 rounded border border-white/5 overflow-x-auto">
                {revealedCode}
              </pre>
            </div>
          )}
        </div>
      </div>

      {/* Confirmation Modal to Reveal Code */}
      {showRevealConfirm && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-vibe-surface border border-vibe-border rounded-xl p-6 max-w-md w-full shadow-2xl animate-scaleIn">
            <div className="flex items-center gap-3 text-vibe-warning mb-3">
              <span className="text-2xl">⚠️</span>
              <h4 className="text-base font-bold text-vibe-text">Anti-Vibe-Coding Check</h4>
            </div>
            <p className="text-sm text-vibe-textMuted leading-relaxed mb-5">
              VibeBreaker is designed for you to reconstruct the code yourself using the <strong>Algorithm</strong>.
              <br /><br />
              Are you sure you want to reveal the reference solution for this step?
            </p>
            <div className="flex justify-end gap-3">
              <button
                onClick={() => setShowRevealConfirm(false)}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-vibe-bg border border-vibe-border text-vibe-text hover:bg-vibe-surface"
              >
                No, I will write it myself
              </button>
              <button
                onClick={handleConfirmReveal}
                className="px-4 py-2 text-xs font-semibold rounded-lg bg-vibe-warning text-black hover:bg-yellow-400 transition-colors"
              >
                Yes, reveal code
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
