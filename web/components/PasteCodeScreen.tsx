'use client';

import { useState } from 'react';

const DEMO_CODE = `def calculate_statistics(scores):
    """Calculate basic statistics for a list of scores."""
    if not scores:
        return None

    total = sum(scores)
    count = len(scores)
    average = total / count

    sorted_scores = sorted(scores)
    mid = count // 2
    if count % 2 == 0:
        median = (sorted_scores[mid - 1] + sorted_scores[mid]) / 2
    else:
        median = sorted_scores[mid]

    highest = max(scores)
    lowest = min(scores)

    return {
        "average": round(average, 2),
        "median": median,
        "highest": highest,
        "lowest": lowest,
        "count": count
    }


def get_letter_grade(score):
    """Convert numeric score to letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"


def generate_report(student_name, scores):
    """Generate a formatted report for a student."""
    stats = calculate_statistics(scores)
    if stats is None:
        return f"No scores available for {student_name}."

    grades = [get_letter_grade(s) for s in scores]
    grade_counts = {}
    for g in grades:
        grade_counts[g] = grade_counts.get(g, 0) + 1

    report = f"Report for {student_name}\\n"
    report += f"{'=' * 30}\\n"
    report += f"Scores: {scores}\\n"
    report += f"Average: {stats['average']}\\n"
    report += f"Median: {stats['median']}\\n"
    report += f"Highest: {stats['highest']}\\n"
    report += f"Lowest: {stats['lowest']}\\n"
    report += f"Grade Distribution: {grade_counts}\\n"

    return report


if __name__ == "__main__":
    student_scores = [85, 92, 78, 95, 88, 76, 90, 82]
    print(generate_report("Alice", student_scores))`;

const QUICK_PROMPTS = [
  { label: 'Prime Number Sieve', prompt: 'Build a prime number generator and sieve up to a given limit' },
  { label: 'Binary Search Tree', prompt: 'Implement a Binary Search Tree with insert and search operations' },
  { label: 'Student Grade Analyzer', prompt: 'Build a student grade statistics calculator with letter grade conversions' },
  { label: 'LRU Cache', prompt: 'Implement a Least Recently Used (LRU) Cache data structure in Python' },
];

interface PasteCodeScreenProps {
  onSubmit: (code: string, title: string) => void;
  onGenerate: (prompt: string, title: string) => void;
  isLoading: boolean;
}

export default function PasteCodeScreen({ onSubmit, onGenerate, isLoading }: PasteCodeScreenProps) {
  const [mode, setMode] = useState<'prompt' | 'paste'>('prompt');
  const [promptText, setPromptText] = useState('');
  const [code, setCode] = useState('');
  const [title, setTitle] = useState('');

  const handleSubmit = () => {
    if (mode === 'prompt') {
      if (!promptText.trim()) return;
      onGenerate(promptText, title || promptText.slice(0, 30));
    } else {
      if (!code.trim()) return;
      onSubmit(code, title || 'Untitled Session');
    }
  };

  const handleLoadDemo = () => {
    setCode(DEMO_CODE);
    setTitle('Student Grade Analyzer');
    setMode('paste');
  };

  return (
    <div className="min-h-[calc(100vh-56px)] flex items-center justify-center p-6">
      <div className="w-full max-w-3xl">
        {/* Hero */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-vibe-accent/10 border border-vibe-accent/20 text-vibe-accent text-xs font-medium mb-4">
            <span className="w-1.5 h-1.5 rounded-full bg-vibe-accent animate-pulse"></span>
            Anti-vibe-coding tool · Powered by Qwen 2.5 Coder
          </div>
          <h2 className="text-3xl font-bold text-vibe-text mb-3 tracking-tight">
            Break the Vibe
          </h2>
          <p className="text-vibe-textMuted text-base max-w-lg mx-auto">
            Instead of copying ready-made AI code, read the <strong>Algorithm</strong> and reconstruct every line yourself.
          </p>
        </div>

        {/* Mode Selector Tabs */}
        <div className="flex bg-vibe-surface/80 p-1.5 rounded-xl border border-vibe-border mb-6 max-w-md mx-auto">
          <button
            onClick={() => setMode('prompt')}
            type="button"
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all flex items-center justify-center gap-2 ${
              mode === 'prompt'
                ? 'bg-vibe-accent text-white shadow-md shadow-vibe-accent/20'
                : 'text-vibe-textMuted hover:text-vibe-text'
            }`}
          >
            <span>💡</span> Describe What to Build
          </button>
          <button
            onClick={() => setMode('paste')}
            type="button"
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition-all flex items-center justify-center gap-2 ${
              mode === 'paste'
                ? 'bg-vibe-accent text-white shadow-md shadow-vibe-accent/20'
                : 'text-vibe-textMuted hover:text-vibe-text'
            }`}
          >
            <span>📋</span> Paste Existing Code
          </button>
        </div>

        {/* Form Container */}
        <div className="card space-y-5">
          {mode === 'prompt' ? (
            /* --- Mode 1: Prompt-to-Algorithm --- */
            <div className="space-y-4">
              <div>
                <label htmlFor="prompt-input" className="block text-sm font-medium text-vibe-text mb-1">
                  What do you want to build?
                </label>
                <p className="text-xs text-vibe-textMuted mb-2">
                  Qwen 2.5 Coder generates the code, but reveals <strong>ONLY the step-by-step algorithm</strong> for you to write. The reference code stays secret until you ask to see it.
                </p>
                <textarea
                  id="prompt-input"
                  className="input text-sm min-h-[140px] resize-y leading-relaxed"
                  placeholder="e.g., Build a Binary Search Tree with insert and search methods, or a prime number sieve..."
                  value={promptText}
                  onChange={(e) => setPromptText(e.target.value)}
                  disabled={isLoading}
                />
              </div>

              {/* Quick suggestion chips */}
              <div>
                <span className="text-[11px] font-medium text-vibe-textMuted block mb-2 uppercase tracking-wider">
                  Quick Ideas:
                </span>
                <div className="flex flex-wrap gap-2">
                  {QUICK_PROMPTS.map((item, idx) => (
                    <button
                      key={idx}
                      type="button"
                      onClick={() => {
                        setPromptText(item.prompt);
                        setTitle(item.label);
                      }}
                      className="px-2.5 py-1 text-xs rounded-lg bg-vibe-bg border border-vibe-border text-vibe-text hover:border-vibe-accent/50 hover:text-vibe-accent transition-colors"
                      disabled={isLoading}
                    >
                      + {item.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label htmlFor="session-title-prompt" className="block text-xs font-medium text-vibe-textMuted mb-1">
                  Session Title (Optional)
                </label>
                <input
                  id="session-title-prompt"
                  type="text"
                  className="input text-sm"
                  placeholder="e.g., Prime Sieve Practice"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={isLoading}
                />
              </div>
            </div>
          ) : (
            /* --- Mode 2: Paste Code --- */
            <div className="space-y-4">
              <div>
                <label htmlFor="session-title" className="block text-sm font-medium text-vibe-text mb-1">
                  Session Title
                </label>
                <input
                  id="session-title"
                  type="text"
                  className="input text-sm"
                  placeholder="e.g., Student Grade Analyzer"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  disabled={isLoading}
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label htmlFor="code-input" className="block text-sm font-medium text-vibe-text">
                    Python Code
                  </label>
                  <button
                    onClick={handleLoadDemo}
                    type="button"
                    className="text-xs text-vibe-accent hover:text-vibe-accentHover transition-colors"
                    disabled={isLoading}
                  >
                    Load demo snippet
                  </button>
                </div>
                <textarea
                  id="code-input"
                  className="input mono text-sm min-h-[220px] resize-y leading-relaxed"
                  placeholder="Paste your Python reference code here..."
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  disabled={isLoading}
                  spellCheck={false}
                />
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-vibe-textMuted">
                    {code ? code.split('\n').length : 0} lines · Python only · Max 300 lines
                  </span>
                </div>
              </div>
            </div>
          )}

          {/* Submit Action */}
          <button
            onClick={handleSubmit}
            disabled={(mode === 'prompt' ? !promptText.trim() : !code.trim()) || isLoading}
            className="btn-primary w-full py-3 text-base font-semibold flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                {mode === 'prompt' ? 'Generating Algorithm with Qwen 2.5 Coder…' : 'Breaking the vibe…'}
              </>
            ) : (
              <>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" fill="currentColor" />
                </svg>
                {mode === 'prompt' ? 'Generate Algorithm & Reconstruct' : 'Break the Vibe'}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
