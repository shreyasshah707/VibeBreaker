'use client';

interface HeaderProps {
  sessionTitle?: string | null;
  showBack?: boolean;
  onBack?: () => void;
}

export default function Header({ sessionTitle, showBack, onBack }: HeaderProps) {
  return (
    <header className="border-b border-vibe-border bg-vibe-surface/80 backdrop-blur-sm sticky top-0 z-50">
      <div className="max-w-[1600px] mx-auto px-6 h-14 flex items-center gap-4">
        {showBack && (
          <button
            onClick={onBack}
            className="text-vibe-textMuted hover:text-vibe-text transition-colors text-sm flex items-center gap-1"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M10 12L6 8L10 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
            Back
          </button>
        )}

        <div className="flex items-center gap-3">
          {/* Logo */}
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-vibe-accent to-purple-500 flex items-center justify-center">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M13 2L3 14H12L11 22L21 10H12L13 2Z" fill="white" />
            </svg>
          </div>
          <div>
            <h1 className="text-base font-semibold text-vibe-text tracking-tight">
              VibeBreaker
            </h1>
          </div>
        </div>

        {sessionTitle && (
          <>
            <span className="text-vibe-border">/</span>
            <span className="text-sm text-vibe-textMuted truncate max-w-[300px]">
              {sessionTitle}
            </span>
          </>
        )}

        <div className="ml-auto text-xs text-vibe-textMuted">
          Learn by rebuilding
        </div>
      </div>
    </header>
  );
}
