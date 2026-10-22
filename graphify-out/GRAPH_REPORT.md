# Graph Report - VibeBreaker  (2026-10-22)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 223 nodes · 369 edges · 13 communities (7 shown, 6 thin omitted)
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 7 edges (avg confidence: 0.85)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `083fb8fb`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- routes.py
- AgentLoop
- api.ts
- package.json
- compilerOptions
- react
- devDependencies
- guardrails.py
- next.config.js

## God Nodes (most connected - your core abstractions)
1. `AgentLoop` - 23 edges
2. `compilerOptions` - 16 edges
3. `get_db_conn()` - 10 edges
4. `Home()` - 9 edges
5. `submit_attempt()` - 8 edges
6. `apiFetch()` - 8 edges
7. `create_session()` - 7 edges
8. `get_hint()` - 7 edges
9. `row_to_dict()` - 7 edges
10. `handle_code_analyze()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `create_session()` --calls--> `handle_learn_plan()`  [EXTRACTED]
  api/app/routes.py → api/app/services/agent_loop.py
- `finish_session()` --calls--> `handle_reflect()`  [EXTRACTED]
  api/app/routes.py → api/app/services/agent_loop.py
- `generate_session_from_prompt()` --calls--> `handle_generate_from_prompt()`  [EXTRACTED]
  api/app/routes.py → api/app/services/agent_loop.py
- `submit_attempt()` --calls--> `handle_evaluate()`  [EXTRACTED]
  api/app/routes.py → api/app/services/agent_loop.py
- `LearningWorkspaceProps` --references--> `SessionState`  [EXTRACTED]
  web/components/LearningWorkspace.tsx → web/lib/api.ts

## Import Cycles
- None detected.

## Communities (13 total, 6 thin omitted)

### Community 0 - "routes.py"
Cohesion: 0.07
Nodes (16): get_db(), init_db(), health_check(), create_session(), finish_session(), generate_session_from_prompt(), get_db_conn(), get_hint() (+8 more)

### Community 1 - "AgentLoop"
Cohesion: 0.09
Nodes (7): AgentLoop, _clean_json_str(), handle_evaluate(), handle_generate_from_prompt(), handle_learn_plan(), handle_reflect(), handle_tutor()

### Community 2 - "api.ts"
Cohesion: 0.12
Nodes (30): AppScreen, Home(), Header(), HeaderProps, HintEntry, LearningWorkspace(), LearningWorkspaceProps, Editor (+22 more)

### Community 3 - "package.json"
Cohesion: 0.07
Nodes (26): autoprefixer, axios, eslint, eslint-config-next, @monaco-editor/react, postcss, react-dom, tailwindcss (+18 more)

### Community 4 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowJs, esModuleInterop, incremental, isolatedModules, jsx, lib, module (+10 more)

### Community 5 - "react"
Cohesion: 0.15
Nodes (5): next, react, metadata, PasteCodeScreenProps, QUICK_PROMPTS

### Community 6 - "devDependencies"
Cohesion: 0.20
Nodes (10): devDependencies, autoprefixer, eslint, eslint-config-next, postcss, tailwindcss, @types/node, @types/react (+2 more)

## Knowledge Gaps
- **11 isolated node(s):** `autoprefixer`, `axios`, `eslint`, `eslint-config-next`, `postcss` (+6 more)
  These have ≤1 connection - possible missing edges. (Counts symbols only; 124 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **6 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `react` connect `react` to `api.ts`, `package.json`?**
  _High betweenness centrality (0.070) - this node is a cross-community bridge._
- **What connects `autoprefixer`, `axios`, `eslint` to the rest of the system?**
  _11 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `routes.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06936026936026936 - nodes in this community are weakly interconnected._
- **Why does `AgentLoop` connect `AgentLoop` to `routes.py`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Should `AgentLoop` be split into smaller, more focused modules?**
  _Cohesion score 0.09446693657219973 - nodes in this community are weakly interconnected._
- **Why does `devDependencies` connect `devDependencies` to `package.json`?**
  _High betweenness centrality (0.030) - this node is a cross-community bridge._
- **Should `api.ts` be split into smaller, more focused modules?**
  _Cohesion score 0.11561561561561562 - nodes in this community are weakly interconnected._