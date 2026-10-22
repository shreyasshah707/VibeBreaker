'use client';

import dynamic from 'next/dynamic';

// Dynamically import Monaco to avoid SSR issues
const Editor = dynamic(() => import('@monaco-editor/react'), { ssr: false });

interface MonacoEditorProps {
  value: string;
  onChange: (value: string) => void;
  readOnly?: boolean;
  height?: string;
  language?: string;
}

export default function MonacoEditor({
  value,
  onChange,
  readOnly = false,
  height = '100%',
  language = 'python',
}: MonacoEditorProps) {
  return (
    <Editor
      height={height}
      language={language}
      value={value}
      onChange={(val) => onChange(val || '')}
      theme="vs-dark"
      options={{
        readOnly,
        minimap: { enabled: false },
        fontSize: 14,
        fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
        automaticLayout: true,
        tabSize: 4,
        wordWrap: 'on',
        padding: { top: 16, bottom: 16 },
        renderLineHighlight: 'gutter',
        scrollbar: {
          verticalScrollbarSize: 8,
          horizontalScrollbarSize: 8,
        },
        suggestOnTriggerCharacters: false,
        quickSuggestions: false,
        parameterHints: { enabled: false },
        wordBasedSuggestions: 'off',
        acceptSuggestionOnCommitCharacter: false,
      }}
    />
  );
}
