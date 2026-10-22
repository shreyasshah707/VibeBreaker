# VibeBreaker Architecture

## Overview

VibeBreaker is an anti–vibe-coding learning tool that helps students reconstruct and understand Python code by converting it into a sequence of natural-language reconstruction objectives.

## Agent Loop

The backend uses a **Hermes-inspired single-agent loop** that owns the workflow state. The LLM never decides to advance the student to the next step — the backend controls this.

### Hermes-Inspired Loop

1. **Receive user action** — Student submits code, requests a hint, or finishes the session
2. **Load session state** — Read current step from SQLite
3. **Select the appropriate agent** — Based on the action, choose Code Analyzer, Learning Plan, Tutor, Evaluator, Hint, or Reflection agent
4. **Construct a focused prompt** — Send only the necessary context to the LLM
5. **Call DigitalOcean Inference** — OpenAI-compatible API with configured model
6. **Parse structured output** — Validate and parse the LLM's JSON response
7. **Apply backend guardrails** — Enforce input/output constraints, never reveal solution
8. **Update SQLite session state** — Save attempts, hints, step progress
9. **Return only the permitted student-facing response** — Never reveal full solution or future steps

### Agent Roles

#### 1. Code Analyzer Agent
- **Input**: pasted Python code
- **Output**: structured JSON describing functions, classes, imports, key variables, calls, control flow, and likely learning concepts
- **Not shown to the student**

#### 2. Learning Plan Agent
- **Input**: code analysis
- **Output**: 5–10 ordered reconstruction objectives
- **Each objective**: small, actionable, understandable without seeing the solution
- **Not shown to the student as raw JSON**

#### 3. Tutor Agent
- **Input**: current objective, student attempt if any, hint level
- **Output**: one short student-facing instruction or hint
- **Student-facing**: encouraging and focused on the current objective only

#### 4. Attempt Evaluator Agent
- **Input**: current objective, reference code region, student attempt
- **Output**: pass/partial/fail status + concise feedback
- **Student-facing**: feedback only, never reveals solution
- **Guardrail**: if uncertain, return partial, not pass
- **Backend controls advancement**, not the LLM

#### 5. Hint Agent
- **Three escalating hint levels**:
  - **Conceptual hint**: high-level guidance (first level)
  - **Narrower hint**: more specific guidance
  - **Code hint**: max 3 lines, only on explicit request
- **Student-facing**: only the hint text, no solution reveal

#### 6. Reflection Agent
- **At the end**, generates:
  - Patterns practiced (3-5 concepts)
  - Areas where student needed hints
  - Three viva-style questions based on reconstructed code
- **Student-facing**

## API Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/sessions` | POST | Create new session: validate code, run Code Analyzer, Learning Plan Agent, create session and steps in SQLite |
| `/api/sessions/{session_id}` | GET | Return current session state, current objective, progress, completed steps |
| `/api/sessions/{session_id}/attempt` | POST | Submit student code: evaluate against objective, advance if pass, remain if partial/fail |
| `/api/sessions/{session_id}/hint` | POST | Request hint at specified level: enforce escalation, return hint |
| `/api/sessions/{session_id}/finish` | POST | Run Reflection Agent: return patterns, areas needing hints, viva questions |

## Database Schema

SQLite with three tables:

- **sessions**: id, title, original_code, language, created_at, current_step_index, status
- **session_steps**: id, session_id, step_index, objective, learning_concept, status, hint_level_used, created_at, completed_at
- **session_attempts**: id, session_id, step_id, student_code, evaluation_status, feedback, created_at
- **agent_traces**: id, session_id, agent_name, input_summary, output_summary, model_name, latency_ms, created_at

## Guardrails

### Input Guardrails
- Accept Python only
- Maximum 300 lines
- Reject code containing likely secrets or API keys
- Sanitize/flag suspicious prompt-injection instructions inside comments

### Output Guardrails
- Never reveal the full original solution
- Never reveal code from future steps
- Only discuss the current objective
- Code hints maximum 3 lines
- Tutor responses must be short, actionable, and focused on the current objective
- If evaluator is uncertain, return partial, not pass
- The backend, not the LLM, controls whether the student advances

## DigitalOcean Inference

- **Base URL**: `https://inference.do-ai.run`
- **API Key**: configured via `DIGITALOCEAN_INFERENCE_API_KEY` environment variable
- **Model name**: configurable via `VIBEBREAKER_MODEL_NAME` environment variable (defaults to `qwen-coder`)
- **API**: OpenAI-compatible `/v1/chat/completions` endpoint

## Security

- API keys never exposed in frontend
- All secrets via environment variables
- Input validation and sanitization on backend
- No student code execution
- Prompt-injection protection in comments