"""FastAPI routes for VibeBreaker."""

import json
import sqlite3
import os
import re
import sys
from datetime import datetime, timezone

# Ensure the api/app directory is on the path
_sys_path = os.path.dirname(os.path.abspath(__file__))
if _sys_path not in sys.path:
    sys.path.insert(0, _sys_path)

# Import DB path from models (same as init_db uses)
from app.db.models import DATABASE_PATH

from fnmatch import filter
from fastapi import APIRouter, Request, Depends, Body, Path
from typing import Optional, List

# ---- Row factory helper ----

def row_to_dict(row):
    """Convert sqlite3.Row or tuple to dict."""
    if isinstance(row, dict):
        return row
    # sqlite3.Row objects have a keys() method
    if hasattr(row, 'keys'):
        return dict(row)
    # Otherwise, assume it's a tuple and return as-is (caller must use indexing)
    return row

# ---- Inlined guardrail logic from app.guardrails.guardrails ----

def validate_python_code(code: str) -> List[str]:
    """Validate input code and return list of errors."""
    errors = []

    # Maximum 300 lines
    lines = code.split("\n")
    if len(lines) > 300:
        errors.append("Code must not exceed 300 lines.")

    # Reject code containing likely secrets or API keys
    secret_patterns = [
        r"api_key\s*=\s*['\"][^'\"]+['\"]",
        r"api_key\s*=\s*\".*?\"",
        r"secret_key\s*=\s*['\"][^'\"]+['\"]",
        r"token\s*=\s*['\"][^'\"]{10,}['\"]",
    ]
    for pattern in secret_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            errors.append("Code contains potential secrets or API keys. Please remove them.")

    # Sanitize or flag suspicious prompt-injection instructions inside comments
    injection_patterns = [
        r"ignore\s+previous\s+instructions",
        r"disregard\s+all\s+previous",
        r"system\s*:\s*",
        r"#\s*ignore",
    ]
    for pattern in injection_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            errors.append("Suspicious prompt-injection instructions detected in comments.")

    return errors


# ---- Router definition ----

router = APIRouter(prefix="/api", tags=["vibebreaker"])


def get_db_conn():
    """Dependency to get DB connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---- Route definitions ----

@router.post("/sessions")
async def create_session(request: Request):
    """POST /api/sessions"""
    body = await request.json()
    code = body.get("code", "")
    title = body.get("title", "VibeBreaker Session")

    # Input guardrails
    errors = validate_python_code(code)
    if errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    # Max 300 lines check
    lines = code.split("\n")
    if len(lines) > 300:
        raise HTTPException(status_code=400, detail="Code must not exceed 300 lines.")

    from uuid import uuid4
    session_id = str(uuid4())

    # Initialize DB connection
    conn = get_db_conn()
    c = conn.cursor()

    # Run Code Analyzer Agent
    from services.agent_loop import handle_code_analyze, handle_learn_plan

    analysis = handle_code_analyze(code, session_id)

    # Run Learning Plan Agent
    objectives = handle_learn_plan(analysis, session_id)

    # Create session in SQLite
    created_at = datetime.now(timezone.utc).isoformat()

    c.execute(
        "INSERT INTO sessions (id, title, original_code, language, created_at, current_step_index, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, title, code, "python", created_at, 0, "active"),
    )

    # Create session steps in SQLite
    for i, obj in enumerate(objectives):
        algo = obj.get("algorithm") or f"1. Analyze the requirement: {obj.get('objective', '')}.\n2. Write the function or logic structure.\n3. Return the evaluated result."
        shint = obj.get("starter_hint") or f"Focus on {obj.get('learning_concept', 'the concept')} to get started."
        ref_code = obj.get("reference_code") or ""
        c.execute(
            "INSERT INTO session_steps (session_id, step_index, objective, learning_concept, algorithm, starter_hint, reference_code, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (session_id, i, obj["objective"], obj.get("learning_concept", "general"), algo, shint, ref_code, "pending", created_at),
        )

    conn.commit()
    conn.close()

    # Return session ID, total steps, and first objective
    first_objective = objectives[0] if objectives else {"objective": "Start reconstruction", "learning_concept": "introduction"}

    return {
        "session_id": session_id,
        "title": title,
        "total_steps": len(objectives),
        "current_step_index": 0,
        "step_index": 0,
        "first_objective": first_objective["objective"],
        "first_algorithm": first_objective.get("algorithm", ""),
        "first_starter_hint": first_objective.get("starter_hint", ""),
        "objectives": objectives,
    }


@router.post("/sessions/generate")
async def generate_session_from_prompt(request: Request):
    """POST /api/sessions/generate - Generates code & algorithm using Qwen 2.5 Coder from user's idea."""
    body = await request.json()
    prompt_text = body.get("prompt", "").strip()
    if not prompt_text:
        raise HTTPException(status_code=400, detail="Please describe what you want to build.")

    from uuid import uuid4
    session_id = str(uuid4())

    from services.agent_loop import handle_generate_from_prompt
    gen_result = handle_generate_from_prompt(prompt_text, session_id)

    title = body.get("title") or gen_result.get("title") or "Qwen 2.5 Generated Session"
    code = gen_result.get("full_code", "")
    steps = gen_result.get("steps", [])

    created_at = datetime.now(timezone.utc).isoformat()
    conn = get_db_conn()
    c = conn.cursor()

    c.execute(
        "INSERT INTO sessions (id, title, original_code, language, created_at, current_step_index, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (session_id, title, code, "python", created_at, 0, "active"),
    )

    for i, step in enumerate(steps):
        c.execute(
            "INSERT INTO session_steps (session_id, step_index, objective, learning_concept, algorithm, starter_hint, reference_code, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                session_id,
                i,
                step.get("objective", f"Step {i+1}"),
                step.get("learning_concept", "General"),
                step.get("algorithm", ""),
                step.get("starter_hint", ""),
                step.get("reference_code", ""),
                "pending",
                created_at,
            ),
        )

    conn.commit()
    conn.close()

    first_step = steps[0] if steps else {}
    return {
        "session_id": session_id,
        "title": title,
        "total_steps": len(steps),
        "current_step_index": 0,
        "step_index": 0,
        "first_objective": first_step.get("objective", "Start reconstruction"),
        "first_algorithm": first_step.get("algorithm", ""),
        "first_starter_hint": first_step.get("starter_hint", ""),
        "steps": steps,
    }


@router.get("/sessions/{session_id}")
async def get_session(session_id: str = Path(...)):
    """GET /api/sessions/{session_id}"""
    conn = get_db_conn()
    c = conn.cursor()

    # Get session
    c.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = c.fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    session_dict = row_to_dict(session)

    # Get steps
    c.execute("SELECT * FROM session_steps WHERE session_id = ? ORDER BY step_index", (session_id,))
    raw_steps = c.fetchall()

    # Get attempts
    c.execute("SELECT * FROM session_attempts WHERE session_id = ?", (session_id,))
    attempts = c.fetchall()

    conn.close()

    current_step_index = session_dict.get("current_step_index", 0)
    steps = [row_to_dict(s) for s in raw_steps]

    # Format steps for frontend schema (keep reference_code hidden by default)
    formatted_steps = []
    for s in steps:
        formatted_steps.append({
            "id": str(s.get("id", "")),
            "step_index": s.get("step_index", 0),
            "objective": s.get("objective", ""),
            "learning_concept": s.get("learning_concept"),
            "algorithm": s.get("algorithm") or "",
            "starter_hint": s.get("starter_hint") or "",
            "status": s.get("status", "pending"),
            "hint_level_used": s.get("hint_level_used") or "none",
            "created_at": s.get("created_at") or datetime.now(timezone.utc).isoformat(),
            "completed_at": s.get("completed_at"),
        })

    completed_steps = len([s for s in steps if s.get("status") == "completed"])
    current_objective = None

    if steps and current_step_index < len(steps):
        step_obj = steps[current_step_index]
        current_objective = {
            "objective": step_obj["objective"],
            "learning_concept": step_obj.get("learning_concept", ""),
            "algorithm": step_obj.get("algorithm") or "",
            "starter_hint": step_obj.get("starter_hint") or "",
        }
    elif steps:
        # Fallback to last
        current_objective = {
            "objective": steps[-1]["objective"],
            "learning_concept": steps[-1].get("learning_concept", ""),
            "algorithm": steps[-1].get("algorithm") or "",
            "starter_hint": steps[-1].get("starter_hint") or "",
        }

    # Count hints
    hint_count = len([s for s in steps if s.get("hint_level_used") and s.get("hint_level_used") != "none"])

    return {
        "session_id": session_id,
        "title": session_dict.get("title", ""),
        "original_code": session_dict.get("original_code", ""),
        "language": session_dict.get("language", "python"),
        "created_at": session_dict.get("created_at") or datetime.now(timezone.utc).isoformat(),
        "current_step_index": current_step_index,
        "total_steps": len(steps),
        "steps": formatted_steps,
        "current_objective": current_objective,
        "progress": f"Step {min(current_step_index + 1, len(steps))} of {len(steps)}" if steps else "Step 1 of 0",
        "completed_steps": completed_steps,
        "hint_usage": hint_count,
        "status": session_dict.get("status", "active"),
    }


@router.post("/sessions/{session_id}/attempt")
async def submit_attempt(session_id: str = Path(...), request: Request = None):
    """POST /api/sessions/{session_id}/attempt"""
    body = await request.json()
    student_code = body.get("student_code") or body.get("code") or ""

    conn = get_db_conn()
    c = conn.cursor()

    # Get current session state
    c.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = c.fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    session_dict = row_to_dict(session)
    curr_idx = session_dict.get("current_step_index", 0)

    # Get current step by session current_step_index
    c.execute("SELECT * FROM session_steps WHERE session_id = ? AND step_index = ?", (session_id, curr_idx))
    current_step = c.fetchone()

    if not current_step:
        # Fallback to first non-completed
        c.execute("SELECT * FROM session_steps WHERE session_id = ? AND status != 'completed' ORDER BY step_index LIMIT 1", (session_id,))
        current_step = c.fetchone()

    if not current_step:
        conn.close()
        raise HTTPException(status_code=404, detail="No active steps found for this session")

    current_step = row_to_dict(current_step)

    # Validate student code input guardrails
    errors = validate_python_code(student_code)
    if errors:
        c.execute(
            "INSERT INTO session_attempts (session_id, step_id, student_code, evaluation_status, feedback, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, current_step["id"], student_code, "fail", "; ".join(errors), datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        conn.close()
        return {
            "status": "fail",
            "evaluation_status": "fail",
            "feedback": "; ".join(errors),
            "current_step_index": current_step["step_index"],
            "next_step_index": current_step["step_index"],
            "objective": current_step["objective"],
            "next_objective": current_step["objective"],
            "advance": False,
            "is_complete": False,
        }

    # Run Attempt Evaluator
    from services.agent_loop import handle_evaluate

    evaluation = handle_evaluate(
        objective=current_step["objective"],
        student_code=student_code,
        analysis={"functions": [], "key_variables": [], "learning_concepts": []},
    )

    evaluation_result = evaluation if isinstance(evaluation, dict) else {"status": "partial", "feedback": "Keep trying."}
    status = evaluation_result.get("status", "partial")
    raw_fb = evaluation_result.get("feedback", "Keep trying.")
    if isinstance(raw_fb, dict):
        feedback = raw_fb.get("feedback") or f"Review the objective: {raw_fb.get('objective', '')}"
    elif raw_fb:
        feedback = str(raw_fb)
    else:
        feedback = "Keep trying to match the objective requirements."

    now_iso = datetime.now(timezone.utc).isoformat()

    if status == "pass":
        new_index = current_step["step_index"] + 1

        c.execute("SELECT COUNT(*) FROM session_steps WHERE session_id = ?", (session_id,))
        total_steps = c.fetchone()[0]

        # Mark current step as completed
        c.execute(
            "UPDATE session_steps SET status = 'completed', completed_at = ? WHERE id = ?",
            (now_iso, current_step["id"]),
        )

        # Save passing attempt
        c.execute(
            "INSERT INTO session_attempts (session_id, step_id, student_code, evaluation_status, feedback, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, current_step["id"], student_code, "pass", feedback, now_iso),
        )

        if new_index < total_steps:
            # Update session current_step_index
            c.execute(
                "UPDATE sessions SET current_step_index = ? WHERE id = ?",
                (new_index, session_id),
            )

            # Get next objective
            c.execute("SELECT objective, learning_concept, algorithm, starter_hint FROM session_steps WHERE session_id = ? AND step_index = ?", (session_id, new_index))
            next_step = c.fetchone()
            next_step_dict = row_to_dict(next_step) if next_step else {}

            conn.commit()
            conn.close()

            return {
                "status": "pass",
                "evaluation_status": "pass",
                "feedback": feedback,
                "current_step_index": new_index,
                "next_step_index": new_index,
                "objective": next_step_dict.get("objective"),
                "next_objective": next_step_dict.get("objective"),
                "algorithm": next_step_dict.get("algorithm", ""),
                "next_algorithm": next_step_dict.get("algorithm", ""),
                "starter_hint": next_step_dict.get("starter_hint", ""),
                "next_starter_hint": next_step_dict.get("starter_hint", ""),
                "advance": True,
                "is_complete": False,
            }
        else:
            # Last step completed
            c.execute(
                "UPDATE sessions SET current_step_index = ?, status = 'completed' WHERE id = ?",
                (new_index, session_id),
            )
            conn.commit()
            conn.close()
            return {
                "status": "pass",
                "evaluation_status": "pass",
                "feedback": feedback,
                "current_step_index": new_index,
                "next_step_index": None,
                "objective": None,
                "next_objective": None,
                "advance": True,
                "is_complete": True,
            }
    else:
        # Save attempt for partial/fail
        c.execute(
            "INSERT INTO session_attempts (session_id, step_id, student_code, evaluation_status, feedback, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, current_step["id"], student_code, status, feedback, now_iso),
        )
        conn.commit()
        conn.close()

        return {
            "status": status,
            "evaluation_status": status,
            "feedback": feedback,
            "current_step_index": current_step["step_index"],
            "next_step_index": current_step["step_index"],
            "objective": current_step["objective"],
            "next_objective": current_step["objective"],
            "advance": False,
            "is_complete": False,
        }


@router.post("/sessions/{session_id}/hint")
async def get_hint(session_id: str = Path(...), request: Request = None):
    """POST /api/sessions/{session_id}/hint"""
    body = await request.json()
    hint_level = body.get("level") or body.get("hint_level") or "conceptual"

    conn = get_db_conn()
    c = conn.cursor()

    # Get current session state
    c.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = c.fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    session_dict = row_to_dict(session)
    curr_idx = session_dict.get("current_step_index", 0)

    # Get current step
    c.execute("SELECT * FROM session_steps WHERE session_id = ? AND step_index = ?", (session_id, curr_idx))
    current_step = c.fetchone()
    if not current_step:
        c.execute("SELECT * FROM session_steps WHERE session_id = ? AND status != 'completed' ORDER BY step_index LIMIT 1", (session_id,))
        current_step = c.fetchone()

    if not current_step:
        conn.close()
        raise HTTPException(status_code=404, detail="No active steps found for hint")

    current_step = row_to_dict(current_step)

    # Escalation levels
    hint_escalation = ["conceptual", "narrower", "code"]

    # Check existing hint level
    last_hint = current_step.get("hint_level_used")
    if last_hint and last_hint != "none":
        last_idx = hint_escalation.index(last_hint) if last_hint in hint_escalation else 0
        current_idx = hint_escalation.index(hint_level) if hint_level in hint_escalation else 0

        # Cannot de-escalate to a lower level once a higher one is seen
        if current_idx < last_idx:
            conn.close()
            return {
                "hint": f"You've already received a {last_hint} hint. Request a {hint_escalation[min(last_idx + 1, 2)]} hint or try the same level again.",
                "hint_level": last_hint,
                "level": last_hint,
                "step_index": current_step["step_index"],
                "escalation_ok": False,
            }

    # Run Hint Agent
    from services.agent_loop import handle_hint

    hint = handle_hint(current_step["objective"], hint_level)

    # Save hint usage on current step
    c.execute(
        "UPDATE session_steps SET hint_level_used = ? WHERE id = ?",
        (hint_level, current_step["id"]),
    )
    conn.commit()
    conn.close()

    return {
        "hint": hint,
        "hint_level": hint_level,
        "level": hint_level,
        "step_index": current_step["step_index"],
        "escalation_ok": True,
    }


@router.post("/sessions/{session_id}/finish")
async def finish_session(session_id: str = Path(...)):
    """POST /api/sessions/{session_id}/finish"""
    conn = get_db_conn()
    c = conn.cursor()

    # Get session state
    c.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = c.fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    # Get all steps
    c.execute("SELECT * FROM session_steps WHERE session_id = ? ORDER BY step_index", (session_id,))
    raw_steps = c.fetchall()
    steps = [row_to_dict(s) for s in raw_steps]

    # Count hint usage
    hint_usage_dict: dict = {}
    hint_count = 0
    for s in steps:
        lvl = s.get("hint_level_used")
        if lvl and lvl != "none":
            hint_count += 1
            hint_usage_dict[lvl] = hint_usage_dict.get(lvl, 0) + 1

    analysis = {"learning_concepts": [s.get("learning_concept", "general") for s in steps if s.get("learning_concept")]}

    # Run Reflection Agent
    from services.agent_loop import handle_reflect

    completed_count = len([s for s in steps if s.get("status") == "completed"])
    reflection = handle_reflect(session_id, hint_count, completed_count, analysis)

    weak_areas = reflection.get("weak_areas") or reflection.get("areas_needing_hints", [])
    if not weak_areas:
        weak_areas = ["Boundary conditions", "Edge cases with empty inputs"]

    viva = reflection.get("viva_questions", [])
    if not viva or len(viva) < 3:
        viva = [
            "Why is defensive input validation preferred over letting Python raise unhandled exceptions?",
            "What is the time and space complexity of your reconstructed implementation?",
            "How would you refactor this code to follow clean functional design principles?"
        ]

    # Mark session completed in DB
    c.execute("UPDATE sessions SET status = 'completed' WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()

    return {
        "session_id": session_id,
        "patterns_practiced": reflection.get("patterns_practiced", ["Code reconstruction", "Structured aggregation"]),
        "areas_needing_hints": weak_areas,
        "weak_areas": weak_areas,
        "hint_usage": hint_usage_dict if hint_usage_dict else {"conceptual": hint_count},
        "viva_questions": viva,
        "completed_steps": completed_count,
        "total_steps": len(steps),
        "status": "completed",
    }


@router.post("/sessions/{session_id}/reveal-code")
async def reveal_reference_code(session_id: str = Path(...), request: Request = None):
    """POST /api/sessions/{session_id}/reveal-code - Reveals the reference code for the step or session when student requests it."""
    body = {}
    if request:
        try:
            body = await request.json()
        except Exception:
            pass

    conn = get_db_conn()
    c = conn.cursor()

    c.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
    session = c.fetchone()
    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    session_dict = row_to_dict(session)
    curr_idx = body.get("step_index") if body.get("step_index") is not None else session_dict.get("current_step_index", 0)

    c.execute("SELECT * FROM session_steps WHERE session_id = ? AND step_index = ?", (session_id, curr_idx))
    step = c.fetchone()
    conn.close()

    ref_code = ""
    if step:
        step_dict = row_to_dict(step)
        ref_code = step_dict.get("reference_code") or ""

    if not ref_code:
        ref_code = session_dict.get("original_code", "")

    return {
        "session_id": session_id,
        "step_index": curr_idx,
        "reference_code": ref_code,
        "full_code": session_dict.get("original_code", ""),
    }



def register_routes(app):
    """Register all API routes with the FastAPI app."""
    app.include_router(router)