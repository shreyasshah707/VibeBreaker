'use client';

import { ReflectionResponse } from '@/lib/api';

interface SummaryScreenProps {
  reflection: ReflectionResponse;
  onNewSession: () => void;
}

export default function SummaryScreen({ reflection, onNewSession }: SummaryScreenProps) {
  return (
    <div className="min-h-[calc(100vh-56px)] flex items-center justify-center p-6">
      <div className="w-full max-w-2xl space-y-6 animate-fadeIn">
        {/* Header */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-vibe-success to-emerald-600 mb-4">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
              <path d="M20 6L9 17L4 12" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-vibe-text mb-1">Session Complete!</h2>
          <p className="text-vibe-textMuted">
            You completed {reflection.completed_steps} of {reflection.total_steps} steps
          </p>
        </div>

        {/* Patterns Practiced */}
        <div className="card">
          <h3 className="text-sm font-semibold text-vibe-text mb-3 flex items-center gap-2">
            <span className="text-lg">🧩</span> Patterns Practiced
          </h3>
          <div className="flex flex-wrap gap-2">
            {(reflection.patterns_practiced || []).map((pattern, i) => (
              <span
                key={i}
                className="px-3 py-1 text-xs font-medium rounded-full bg-vibe-accent/15 text-vibe-accent border border-vibe-accent/20"
              >
                {pattern}
              </span>
            ))}
          </div>
        </div>

        {/* Hint Usage */}
        <div className="card">
          <h3 className="text-sm font-semibold text-vibe-text mb-3 flex items-center gap-2">
            <span className="text-lg">💡</span> Hint Usage
          </h3>
          {reflection.hint_usage && Object.keys(reflection.hint_usage).length > 0 ? (
            <div className="grid grid-cols-3 gap-3">
              {Object.entries(reflection.hint_usage).map(([level, count]) => (
                <div key={level} className="bg-vibe-bg rounded-lg p-3 text-center border border-vibe-border">
                  <div className="text-xl font-bold text-vibe-text">{count}</div>
                  <div className="text-xs text-vibe-textMuted capitalize">{level}</div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-vibe-success">
              🏆 No hints used — impressive!
            </p>
          )}
        </div>

        {/* Weak Areas */}
        {reflection.weak_areas && reflection.weak_areas.length > 0 && (
          <div className="card">
            <h3 className="text-sm font-semibold text-vibe-text mb-3 flex items-center gap-2">
              <span className="text-lg">📈</span> Areas for Growth
            </h3>
            <ul className="space-y-2">
              {reflection.weak_areas.map((area, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-vibe-textMuted">
                  <span className="text-vibe-warning mt-0.5">•</span>
                  {area}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Viva Questions */}
        <div className="card">
          <h3 className="text-sm font-semibold text-vibe-text mb-3 flex items-center gap-2">
            <span className="text-lg">🎤</span> Viva Questions
          </h3>
          <p className="text-xs text-vibe-textMuted mb-3">
            Can you answer these without looking at any reference?
          </p>
          <div className="space-y-3">
            {(reflection.viva_questions || []).map((q, i) => (
              <div key={i} className="bg-vibe-bg border border-vibe-border rounded-lg p-4">
                <span className="text-xs font-semibold text-vibe-accent mb-1 block">
                  Question {i + 1}
                </span>
                <p className="text-sm text-vibe-text">{q}</p>
              </div>
            ))}
          </div>
        </div>

        {/* New Session Button */}
        <button
          onClick={onNewSession}
          className="btn-primary w-full py-3 text-base font-semibold"
        >
          Start a New Session
        </button>
      </div>
    </div>
  );
}
