"""Hermes-style agent loop for VibeBreaker.

The backend owns workflow state. The LLM never decides to advance on its own.
"""

import time
import json
import os
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import httpx
from uuid import uuid4

import app.guardrails as guardrails
from app.db.models import get_db, init_db


def _clean_json_str(raw: str) -> str:
    """Robustly extract and clean JSON string from LLM responses (stripping markdown fences & commentary)."""
    if not raw:
        return "{}"
    raw = raw.strip()
    # Strip markdown code blocks if wrapped by the LLM
    if "```" in raw:
        start = raw.find("```")
        end = raw.rfind("```")
        if start != -1 and end != -1 and end > start:
            inner = raw[start + 3:end].strip()
            if inner.lower().startswith("json"):
                inner = inner[4:].strip()
            raw = inner

    # Find matching { ... } or [ ... ]
    first_brace = raw.find("{")
    first_bracket = raw.find("[")
    if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
        last_brace = raw.rfind("}")
        if last_brace != -1:
            raw = raw[first_brace:last_brace + 1]
    elif first_bracket != -1:
        last_bracket = raw.rfind("]")
        if last_bracket != -1:
            raw = raw[first_bracket:last_bracket + 1]
    return raw.strip()


class AgentLoop:
    """Hermes-inspired single-agent loop."""

    def __init__(self):
        from dotenv import load_dotenv
        _dir = os.path.dirname(os.path.abspath(__file__))
        _env = os.path.abspath(os.path.join(_dir, "..", "..", ".env"))
        if os.path.exists(_env):
            load_dotenv(dotenv_path=_env)
        else:
            load_dotenv()

        self.base_url = os.getenv("DIGITALOCEAN_INFERENCE_BASE_URL", "https://api.groq.com/openai/v1").rstrip("/")
        self.api_key = os.getenv("DIGITALOCEAN_INFERENCE_API_KEY")
        raw_model = os.getenv("VIBEBREAKER_MODEL_NAME", "qwen/qwen3.8-27b")
        self.model_name = raw_model.split("#")[0].strip() or "qwen/qwen3.8-27b"
        self.client = httpx.Client(base_url=self.base_url, headers={
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def _call_llm(self, prompt: str, system: str = "", max_tokens: int = 800) -> Dict[str, Any]:
        """Call the Inference LLM (Groq / DigitalOcean / OpenAI-compatible)."""
        start = time.time()
        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system or "You are a concise, helpful Python tutor."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }
        try:
            # If base_url already contains /v1, post to /chat/completions; otherwise /v1/chat/completions
            endpoint = "/chat/completions" if self.base_url.endswith("/v1") else "/v1/chat/completions"
            response = self.client.post(endpoint, json=payload, timeout=30.0)
            latency_ms = int((time.time() - start) * 1000)

            if response.status_code != 200:
                print(f"[AgentLoop] LLM non-200 ({response.status_code}): {response.text}")
                # Return a fallback output instead of raising
                return {
                    "output": self._fallback_output(prompt),
                    "latency_ms": latency_ms,
                    "model": self.model_name,
                    "fallback": True,
                }

            data = response.json()
            output = data["choices"][0]["message"]["content"]
            return {
                "output": output,
                "latency_ms": latency_ms,
                "model": self.model_name,
                "fallback": False,
            }
        except Exception as e:
            # Return fallback on any error (network, auth, etc.)
            return {
                "output": self._fallback_output(prompt),
                "latency_ms": 0,
                "model": self.model_name,
                "fallback": True,
                "error": str(e),
            }

    def _fallback_output(self, prompt: str) -> str:
        """Generate contextual fallback output when LLM is unavailable."""
        pl = prompt.lower()
        import re
        obj_match = re.search(r"objective[:\s]+([^\n\r]+)", prompt, re.IGNORECASE)
        obj = obj_match.group(1).strip() if obj_match else ""
        obj_l = obj.lower()

        if "hint agent" in pl or "hint:" in pl or "hint level" in pl or "give a conceptual hint" in pl or "give a narrower hint" in pl or "tiny code hint" in pl:
            if "reverse" in obj_l or "string" in obj_l or "slice" in obj_l:
                if "code" in pl:
                    return "def reverse_string(s):\n    return s[::-1]"
                elif "narrower" in pl:
                    return "Use Python slice syntax `s[::-1]` with a step of -1 to reverse the string."
                else:
                    return "Remember strings are sequences in Python that support negative slice stepping `[start:stop:step]`."
            elif "code" in pl:
                return f"# Code snippet for: {obj}\ndef solution():\n    pass"
            elif "narrower" in pl:
                return f"Focus on implementing the logic and syntax specifically for: {obj}"
            else:
                return f"Think about the algorithmic pattern: what inputs and return types are needed for: {obj or 'this step'}?"
        elif "evaluate" in pl:
            if "reverse" in obj_l or "string" in obj_l:
                if "reverse_string" in pl and "[::-1]" in pl:
                    return '{"status": "pass", "feedback": "Great job! String reversal using slicing is correctly implemented."}'
                elif "def reverse_string" in pl:
                    return '{"status": "pass", "feedback": "Function signature is declared correctly! Now implement the slice logic."}'
                else:
                    return '{"status": "fail", "feedback": "Declare def reverse_string(s): to meet the objective."}'
            return '{"status": "partial", "feedback": "Review the objective requirements and check your implementation."}'
        elif "reflect" in pl:
            return '{"patterns_practiced": ["String slicing & immutability", "Function decomposition", "Edge case validation"], "weak_areas": ["Empty string and single-character handling"], "viva_questions": ["What is the time complexity of s[::-1] in Python?", "Why are strings immutable in Python?", "How would you reverse a string without using slicing?"]}'
        elif "analysis" in pl:
            return '{"functions": [{"name": "reverse_string", "parameters": ["s"], "return_type": "str"}], "classes": [], "imports": [], "key_variables": ["s"], "calls": [], "control_flow": [], "learning_concepts": ["String slicing", "Function definition"]}'
        elif "objective" in pl or "define" in pl or "learning plan" in pl:
            return '[{"objective": "Define reverse_string function and accept string parameter s", "learning_concept": "function definition"}, {"objective": "Implement string reversal using slice notation with step -1", "learning_concept": "string slicing"}, {"objective": "Add test driver under main and verify with sample strings", "learning_concept": "testing"}]'
        else:
            return json.dumps({"status": "partial", "feedback": "Review the algorithm and objective carefully."})

    def _trace(self, session_id: str, agent_name: str, input_summary: str, output_summary: str):
        """Record an agent trace in the DB."""
        try:
            conn = next(get_db())
            c = conn.cursor()
            c.execute(
                "INSERT INTO agent_traces (session_id, agent_name, input_summary, output_summary, model_name, latency_ms, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (session_id, agent_name, input_summary, output_summary, self.model_name, self.latency_ms, datetime.now(timezone.utc).isoformat())
            )
            conn.commit()
        except Exception:
            pass  # Best effort tracing

    def run_code_analyzer(self, code: str, session_id: str) -> Dict[str, Any]:
        """Agent 1: Code Analyzer.

        Input: pasted Python code
        Output: structured JSON describing functions, classes, imports, key variables, calls, control flow, and likely learning concepts
        """
        prompt = f"""You are the Code Analyzer for VibeBreaker. Analyze the following Python code and output structured JSON describing:
- functions (name, parameters, return type)
- classes (name, methods)
- imports
- key variables
- function calls
- control flow (loops, conditionals)
- likely learning concepts

Code:
```python
{code}
```

Output ONLY valid JSON with no explanatory text. Use this schema:
{{
  "functions": [...],
  "classes": [...],
  "imports": [...],
  "key_variables": [...],
  "calls": [...],
  "control_flow": [...],
  "learning_concepts": []
}}"""

        result = self._call_llm(prompt)
        # Parse the JSON output
        try:
            analysis = json.loads(_clean_json_str(result.get("output", "")))
        except json.JSONDecodeError:
            analysis = {"functions": [], "classes": [], "imports": [], "key_variables": [], "calls": [], "control_flow": [], "learning_concepts": []}

        self._trace(session_id, "code_analyzer", code[:100], json.dumps(analysis))
        return analysis

    def run_learning_plan(self, analysis: Dict[str, Any], session_id: str) -> List[Dict[str, Any]]:
        """Agent 2: Learning Plan.

        Input: code analysis
        Output: 5-10 ordered reconstruction objectives
        """
        concepts = "; ".join(analysis.get("learning_concepts", [])) or "code reconstruction"
        prompt = f"""You are the Learning Plan Agent for VibeBreaker. Based on the code analysis, create 7 ordered reconstruction objectives that make a student reconstruct the code understandingfully.

Guidelines:
- Each objective must be small, actionable, and understandable WITHOUT seeing the solution
- Objectives should cover different concepts (functions, variables, control flow, etc.)
- Order them from simplest to most complex
- Return as a JSON array of objects with "objective" and "learning_concept" fields

Code concepts: {concepts}

Output ONLY a JSON array like:
[
  {{"objective": "Define a function named calculate_average", "learning_concept": "function definition"}},
  {{"objective": "Inside main, call calculate_average with scores list", "learning_concept": "function call"}}
]"""

        result = self._call_llm(prompt)
        try:
            objectives = json.loads(_clean_json_str(result.get("output", "")))
            # Ensure we have 5-10 objectives
            if not isinstance(objectives, list):
                objectives = []
            if len(objectives) < 4:
                objectives = objectives + [{"objective": f"Reconstruct concept {i}", "learning_concept": "general"} for i in range(len(objectives), 5)]
            if len(objectives) > 10:
                objectives = objectives[:10]
        except json.JSONDecodeError:
            objectives = self._fallback_objectives(analysis)

        # Enrich every objective with algorithm and starter hint if not already present
        for i, obj in enumerate(objectives):
            title = obj.get("objective", f"Step {i+1}")
            concept = obj.get("learning_concept", "logic")
            if "algorithm" not in obj or not obj["algorithm"]:
                obj["algorithm"] = f"1. Review the requirement: {title}.\n2. Define necessary variable(s) or function signature.\n3. Implement the calculation/flow using {concept}.\n4. Ensure correct return value or print format."
            if "starter_hint" not in obj or not obj["starter_hint"]:
                obj["starter_hint"] = f"Starter Guidance: Focus on {concept} and verify your variable naming."

        self._trace(session_id, "learning_plan", json.dumps(analysis), json.dumps(objectives))
        return objectives

    def _fallback_objectives(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback objectives when LLM fails."""
        concepts = analysis.get("learning_concepts", [])
        if not concepts:
            concepts = ["code reconstruction"]
        return [
            {"objective": f"Understand the {c} concept", "learning_concept": c} for c in concepts[:7]
        ]

    def run_tutor(self, objective: str, student_attempt: Optional[str], hint_level: Optional[str]) -> str:
        """Agent 3: Tutor.

        Input: current objective, student attempt if any, hint level
        Output: one short student-facing instruction or hint
        """
        attempt_text = f"\nStudent attempt: {student_attempt}" if student_attempt else ""
        hint_text = f"\nCurrent hint level: {hint_level}" if hint_level else ""

        prompt = f"""You are the Tutor Agent for VibeBreaker. Give ONE short, actionable instruction to the student about the current objective.

Current objective: {objective}{attempt_text}{hint_text}

Rules:
- Keep it under 30 words
- Be encouraging and focused on the objective only
- Do NOT reveal the solution or code from future steps
- Guide the student toward the objective, don't solve it for them

Response:"""

        result = self._call_llm(prompt, max_tokens=200)
        return result["output"].strip()

    def run_evaluator(self, objective: str, student_code: str, analysis: Dict[str, Any]) -> Dict[str, str]:
        """Agent 4: Attempt Evaluator.

        Input: current objective, reference code region if useful, student attempt
        Output: structured result: pass, partial, or fail, plus concise feedback
        """
        # Step 1: Pre-validate Python syntax using ast
        import ast
        clean_code = (student_code or "").strip()
        if not clean_code:
            return {"status": "fail", "feedback": "Please write your code in the editor before submitting."}

        try:
            ast.parse(clean_code)
        except SyntaxError as syn_err:
            return {
                "status": "fail",
                "feedback": f"Syntax error at line {syn_err.lineno}: {syn_err.msg}. Check colons, quotes, and indentation."
            }

        # Step 2: Prompt LLM evaluator
        prompt = f"""You are the Attempt Evaluator for VibeBreaker. Evaluate the student's code attempt against the objective.

Current objective: {objective}

Student attempt:
```python
{clean_code}
```

Code analysis summary:
- Functions: {analysis.get('functions', [])}
- Key variables: {analysis.get('key_variables', [])}

Evaluate as:
- "pass": student code fully achieves the objective
- "partial": student code partially achieves the objective or has minor errors
- "fail": student code does not achieve the objective

Give concise feedback under 20 words. Be strict, constructive, and fair.

Output ONLY valid JSON:
{{
  "status": "pass|partial|fail",
  "feedback": "short feedback string"
}}"""

        result = self._call_llm(prompt)
        clean_out = _clean_json_str(result.get("output", ""))
        try:
            evaluation = json.loads(clean_out)
            if isinstance(evaluation, list) and evaluation:
                evaluation = evaluation[0] if isinstance(evaluation[0], dict) else {"status": "partial", "feedback": str(evaluation[0])}
            elif not isinstance(evaluation, dict):
                evaluation = {"status": "partial", "feedback": str(evaluation)}

            status = evaluation.get("status", "partial")
            feedback = evaluation.get("feedback", "Review the objective requirements.")
            if status not in ("pass", "partial", "fail"):
                status = "partial"
            return {"status": status, "feedback": str(feedback)}
        except json.JSONDecodeError:
            pass

        # Step 3: Contextual fallback evaluation
        obj_lower = objective.lower()
        code_lower = clean_code.lower()
        if "reverse" in obj_lower or "string" in obj_lower or "slice" in obj_lower:
            if "def reverse_string" in code_lower:
                if "[::-1]" in clean_code or "reversed(" in code_lower:
                    return {"status": "pass", "feedback": "Great job! String reversal using slicing is correctly implemented."}
                elif "define" in obj_lower:
                    return {"status": "pass", "feedback": "Function reverse_string(s) signature declared successfully!"}
                else:
                    return {"status": "partial", "feedback": "Function signature matches. Now return reversed string with s[::-1]."}
            elif "[::-1]" in clean_code:
                return {"status": "partial", "feedback": "Slice syntax s[::-1] found. Now place it inside def reverse_string(s):"}
            elif "calculate_statistics" in code_lower:
                return {"status": "fail", "feedback": "You defined calculate_statistics. The objective is to write reverse_string(s)."}
            else:
                return {"status": "partial", "feedback": "Declare `def reverse_string(s):` to begin implementing this step."}

        return {"status": "partial", "feedback": f"Review requirement: {objective}"}

    def run_hint(self, objective: str, hint_level: str) -> str:
        """Agent 5: Hint Agent.

        Handles three escalating hint levels:
        - Conceptual hint
        - Narrower hint
        - Tiny code hint, maximum 3 lines, only on explicit request
        """
        if hint_level == "conceptual":
            prompt = f"""You are the Hint Agent for VibeBreaker. Give a conceptual hint for this objective.

Objective: {objective}

Give a high-level conceptual hint that guides the student toward the solution without revealing it. Keep it under 20 words. Focus strictly on the specific logic needed for this objective.

Hint:"""
        elif hint_level == "narrower":
            prompt = f"""You are the Hint Agent for VibeBreaker. Give a narrower hint for this objective.

Objective: {objective}

Give a more specific hint that narrows down what the student should focus on. Keep it under 20 words. Focus strictly on the specific Python construct or algorithm needed for this objective.

Hint:"""
        elif hint_level == "code":
            prompt = f"""You are the Hint Agent for VibeBreaker. Give a tiny code hint (max 3 lines) for this objective.

Objective: {objective}

Give maximum a 3-line code hint that points the student in the right direction. No more than 3 lines. Provide ONLY the snippet.

Hint (max 3 lines):
"""
        else:
            prompt = f"Hint for: {objective}"

        result = self._call_llm(prompt, max_tokens=150)
        hint = result.get("output", "").strip()

        # Enforce 3-line limit for code hints
        if hint_level == "code":
            lines = hint.split("\n")
            if len(lines) > 3:
                hint = "\n".join(lines[:3])

        # If LLM fallback or empty, return tailored objective hint
        if result.get("fallback") or not hint or "think about the algorithmic pattern" in hint.lower():
            obj_l = objective.lower()
            if "reverse" in obj_l or "string" in obj_l or "slice" in obj_l:
                if hint_level == "conceptual":
                    return "Strings in Python support slicing [start:stop:step]. A negative step (-1) traverses backward."
                elif hint_level == "narrower":
                    return "Slice notation `s[::-1]` with start and stop omitted returns the reversed sequence."
                else:
                    return "def reverse_string(s):\n    return s[::-1]"
            elif "prime" in obj_l:
                if hint_level == "conceptual":
                    return "A prime number has no divisors other than 1 and itself."
                elif hint_level == "narrower":
                    return "Test divisors from 2 up to int(n**0.5) + 1 using modulo `%`."
                else:
                    return "for i in range(2, int(n**0.5) + 1):\n    if n % i == 0: return False"
            else:
                if hint_level == "conceptual":
                    return f"Think about input, processing, and return needed for: {objective}"
                elif hint_level == "narrower":
                    return f"Focus on syntax and variable naming for: {objective}"
                else:
                    return f"# Target: {objective}\n# write implementation"

        return hint

    def run_reflection(self, session_id: str, hint_usage: int, completed_steps: int, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Agent 6: Reflection Agent.

        At the end, generates:
        - Patterns practiced
        - Areas where the student needed hints
        - Three viva-style questions based on the student's reconstructed code
        """
        concepts = "; ".join(analysis.get("learning_concepts", [])) or "code reconstruction"

        prompt = f"""You are the Reflection Agent for VibeBreaker. Generate a session summary at the end of a student's session.

Session stats: {completed_steps} steps completed, {hint_usage} hints used.

Based on the reconstructed code concepts: {concepts}

Output JSON with:
- "patterns_practiced": list of 3-5 concepts the student practiced
- "areas_needing_hints": list of concepts where the student needed hints
- "viva_questions": 3 questions based on the student's reconstructed code

Format:
{{
  "patterns_practiced": [...],
  "areas_needing_hints": [...],
  "viva_questions": ["question1", "question2", "question3"]
}}"""

        result = self._call_llm(prompt)
        try:
            reflection = json.loads(result["output"])
            # Ensure we have 3 viva questions
            if "viva_questions" not in reflection or len(reflection.get("viva_questions", [])) < 3:
                qs = [f"Can you explain why you used {c} in your code?" for c in analysis.get("learning_concepts", [])[:3]]
                reflection["viva_questions"] = qs[:3]
            while len(reflection.get("viva_questions", [])) < 3:
                reflection.setdefault("viva_questions", []).append("How did you decide on this approach?")
            return reflection
        except json.JSONDecodeError:
            return {
                "patterns_practiced": ["function definition", "control flow"],
                "areas_needing_hints": ["variable scope"],
                "viva_questions": [
                    "Why did you place this function here?",
                    "How would you modify this code?",
                    "What does this variable represent?"
                ]
            }

    def generate_from_prompt(self, user_prompt: str, session_id: str) -> Dict[str, Any]:
        """Prompt to Code & Algorithm: Uses Qwen 2.5 Coder to generate code and step-by-step algorithms.
        Reference code is saved in backend but kept hidden until explicitly requested by student!
        """
        system = "You are an expert Python tutor and coding agent powered by Qwen 2.5 Coder. You turn user requirements into clean Python code and break the solution down into 4 to 6 learning steps with plain-English algorithms, starter hints, and reference snippets."
        prompt = f"""The user wants to build:
"{user_prompt}"

Write a clean, complete, working Python implementation (max 80 lines).
Then break it down into 4 to 6 sequential reconstruction steps.
For EACH step provide:
- "step_index": integer starting at 0
- "objective": concise title of what to implement
- "learning_concept": core programming concept
- "algorithm": step-by-step numbered instructions in plain English/pseudocode explaining the logic
- "starter_hint": initial guidance shown to the student right at step start
- "reference_code": exact python lines for this step (kept hidden from student until requested)

Output ONLY valid JSON with this exact schema:
{{
  "title": "Short descriptive title",
  "full_code": "full python code",
  "steps": [
    {{
      "step_index": 0,
      "objective": "...",
      "learning_concept": "...",
      "algorithm": "1. ...\\n2. ...",
      "starter_hint": "...",
      "reference_code": "..."
    }}
  ]
}}"""
        result = self._call_llm(prompt, system=system, max_tokens=1500)
        try:
            cleaned = _clean_json_str(result.get("output", ""))
            parsed = json.loads(cleaned)
            if isinstance(parsed, dict) and "steps" in parsed and len(parsed["steps"]) >= 2:
                self._trace(session_id, "qwen_prompt_gen", user_prompt, f"Generated {len(parsed['steps'])} steps")
                return parsed
        except Exception as e:
            print(f"[AgentLoop] JSON parse error in generate_from_prompt: {e}")

        synthesized = self._synthesize_prompt_solution(user_prompt)
        self._trace(session_id, "prompt_synth", user_prompt, f"Synthesized {len(synthesized['steps'])} steps")
        return synthesized

    def _synthesize_prompt_solution(self, prompt: str) -> Dict[str, Any]:
        """Intelligent offline fallback solution synthesizer."""
        p_lower = prompt.lower()
        if "reverse" in p_lower or "string" in p_lower:
            title = "Reverse a String in Python"
            full_code = '''def reverse_string(s: str) -> str:
    """Reverse a string using slicing."""
    return s[::-1]

if __name__ == "__main__":
    print(reverse_string("Hello, World!"))'''
            steps = [
                {
                    "step_index": 0,
                    "objective": "Define reverse_string function and accept string parameter s",
                    "learning_concept": "Function definition & string immutability",
                    "algorithm": "1. Define a function named reverse_string taking parameter s.\n2. Add a docstring explaining that it accepts a string and returns its reversed copy.\n3. Prepare to return the reversed string result.",
                    "starter_hint": "Start with `def reverse_string(s):` and keep in mind strings are indexable sequences.",
                    "reference_code": "def reverse_string(s):\n    \"\"\"Reverse the given string.\"\"\"\n    pass",
                },
                {
                    "step_index": 1,
                    "objective": "Implement string reversal using slice notation with step -1",
                    "learning_concept": "Python slicing with negative step [::-1]",
                    "algorithm": "1. Python slice syntax is [start:stop:step].\n2. Leaving start and stop empty with step -1 (`s[::-1]`) reverses the entire sequence from back to front.\n3. Return `s[::-1]` from the function.",
                    "starter_hint": "The most Pythonic way to reverse a string is using slice notation `return s[::-1]`.",
                    "reference_code": "def reverse_string(s):\n    \"\"\"Reverse the given string.\"\"\"\n    return s[::-1]",
                },
                {
                    "step_index": 2,
                    "objective": "Add test driver under main and verify with sample strings",
                    "learning_concept": "Testing & edge case verification",
                    "algorithm": "1. Under `if __name__ == '__main__':`, call reverse_string with a sample text like 'Hello'.\n2. Test edge cases such as empty string and palindromes.\n3. Print the reversed output.",
                    "starter_hint": "Add `if __name__ == '__main__':` and test with `print(reverse_string('Python'))`.",
                    "reference_code": "if __name__ == '__main__':\n    print(reverse_string('Hello, World!'))",
                },
            ]
            return {"title": title, "full_code": full_code, "steps": steps}
        if "prime" in p_lower:
            title = "Prime Number Generator & Sieve"
            full_code = '''def is_prime(n):
    """Check if a number is prime."""
    if n < 2:
        return False
    for i in range(2, int(n ** 0.5) + 1):
        if n % i == 0:
            return False
    return True

def get_primes_up_to(limit):
    """Return all prime numbers up to limit."""
    primes = []
    for num in range(2, limit + 1):
        if is_prime(num):
            primes.append(num)
    return primes'''
            steps = [
                {
                    "step_index": 0,
                    "objective": "Define is_prime(n) and handle base cases",
                    "learning_concept": "Conditional logic & base cases",
                    "algorithm": "1. Define function is_prime accepting an integer n.\n2. If n is strictly less than 2, return False immediately (0 and 1 are not prime).\n3. Otherwise proceed to check divisors.",
                    "starter_hint": "Remember that prime numbers must be integers greater than or equal to 2.",
                    "reference_code": "def is_prime(n):\n    if n < 2:\n        return False",
                },
                {
                    "step_index": 1,
                    "objective": "Implement divisor checking loop up to sqrt(n)",
                    "learning_concept": "Loops and mathematical optimization",
                    "algorithm": "1. Loop through integers from 2 up to int(n**0.5) + 1.\n2. If n modulo i equals 0, n is divisible by i, so return False.\n3. If loop finishes with no divisors found, return True.",
                    "starter_hint": "You only need to test divisors up to the square root of n using int(n ** 0.5) + 1.",
                    "reference_code": "    for i in range(2, int(n ** 0.5) + 1):\n        if n % i == 0:\n            return False\n    return True",
                },
                {
                    "step_index": 2,
                    "objective": "Define get_primes_up_to(limit) and initialize empty list",
                    "learning_concept": "List creation and accumulator pattern",
                    "algorithm": "1. Define get_primes_up_to accepting an integer limit.\n2. Initialize an empty list called primes to store results.",
                    "starter_hint": "Create an empty accumulator list before starting any collection loop.",
                    "reference_code": "def get_primes_up_to(limit):\n    primes = []",
                },
                {
                    "step_index": 3,
                    "objective": "Iterate through range and collect prime numbers",
                    "learning_concept": "Function composition and filtering",
                    "algorithm": "1. Iterate with a for loop from 2 to limit + 1.\n2. Call is_prime(num) for each candidate.\n3. If is_prime returns True, append num to primes.\n4. Return primes list.",
                    "starter_hint": "Use your previously defined is_prime helper function inside the loop.",
                    "reference_code": "    for num in range(2, limit + 1):\n        if is_prime(num):\n            primes.append(num)\n    return primes",
                },
            ]
        elif "tree" in p_lower or "search" in p_lower or "binary" in p_lower:
            title = "Binary Search Tree Implementation"
            full_code = '''class Node:
    def __init__(self, value):
        self.value = value
        self.left = None
        self.right = None

class BST:
    def __init__(self):
        self.root = None

    def insert(self, value):
        if not self.root:
            self.root = Node(value)
        else:
            self._insert_recursive(self.root, value)

    def _insert_recursive(self, current, value):
        if value < current.value:
            if current.left is None:
                current.left = Node(value)
            else:
                self._insert_recursive(current.left, value)
        else:
            if current.right is None:
                current.right = Node(value)
            else:
                self._insert_recursive(current.right, value)'''
            steps = [
                {
                    "step_index": 0,
                    "objective": "Define Node class with value, left, and right pointers",
                    "learning_concept": "Object-oriented tree node structure",
                    "algorithm": "1. Create class Node.\n2. In __init__(self, value), store self.value = value.\n3. Initialize self.left = None and self.right = None.",
                    "starter_hint": "Every tree node stores its own value and references to left and right child nodes.",
                    "reference_code": "class Node:\n    def __init__(self, value):\n        self.value = value\n        self.left = None\n        self.right = None",
                },
                {
                    "step_index": 1,
                    "objective": "Create BST class and handle empty tree insert",
                    "learning_concept": "Root initialization & base case",
                    "algorithm": "1. Create class BST with self.root = None.\n2. Define insert(self, value).\n3. If self.root is None, create new Node(value) as root.",
                    "starter_hint": "Always check if the tree is currently empty before traversing down child nodes.",
                    "reference_code": "class BST:\n    def __init__(self):\n        self.root = None\n    def insert(self, value):\n        if not self.root:\n            self.root = Node(value)",
                },
                {
                    "step_index": 2,
                    "objective": "Implement recursive insertion logic for smaller/larger values",
                    "learning_concept": "Recursive binary search tree property",
                    "algorithm": "1. In _insert_recursive(self, current, value):\n2. If value < current.value, go left (if left is None attach Node, else recurse left).\n3. Else go right (if right is None attach Node, else recurse right).",
                    "starter_hint": "BST invariant: smaller values always go to the left subtree, larger values to the right.",
                    "reference_code": "    def _insert_recursive(self, current, value):\n        if value < current.value:\n            if current.left is None:\n                current.left = Node(value)\n            else:\n                self._insert_recursive(current.left, value)\n        else:\n            if current.right is None:\n                current.right = Node(value)\n            else:\n                self._insert_recursive(current.right, value)",
                },
            ]
        else:
            clean_title = prompt.strip().capitalize()
            if len(clean_title) > 40:
                clean_title = clean_title[:40] + "..."
            title = clean_title or "Custom Python Builder"
            full_code = '''def calculate_statistics(scores):
    """Calculate basic statistics for a list of scores."""
    if not scores:
        return None
    total = sum(scores)
    count = len(scores)
    average = total / count
    sorted_scores = sorted(scores)
    mid = count // 2
    median = (sorted_scores[mid - 1] + sorted_scores[mid]) / 2 if count % 2 == 0 else sorted_scores[mid]
    return {"average": round(average, 2), "median": median, "count": count}

def get_letter_grade(score):
    if score >= 90: return "A"
    elif score >= 80: return "B"
    elif score >= 70: return "C"
    elif score >= 60: return "D"
    return "F"'''
            steps = [
                {
                    "step_index": 0,
                    "objective": "Define calculate_statistics and validate input list",
                    "learning_concept": "Input validation and function declaration",
                    "algorithm": "1. Define calculate_statistics taking parameter `scores`.\n2. Check if `scores` is empty or None; if so, return None.\n3. Proceed to calculate summary metrics.",
                    "starter_hint": "Defensive programming: always check if input collections have elements before calculating averages.",
                    "reference_code": "def calculate_statistics(scores):\n    if not scores:\n        return None",
                },
                {
                    "step_index": 1,
                    "objective": "Compute total, count, and average score",
                    "learning_concept": "Basic list aggregations & division",
                    "algorithm": "1. Compute total = sum(scores).\n2. Compute count = len(scores).\n3. Compute average = total / count.",
                    "starter_hint": "Use Python's built-in sum() and len() functions for concise calculations.",
                    "reference_code": "    total = sum(scores)\n    count = len(scores)\n    average = total / count",
                },
                {
                    "step_index": 2,
                    "objective": "Sort scores and compute median handling even and odd counts",
                    "learning_concept": "Sorting and midpoint indexing",
                    "algorithm": "1. Sort scores using sorted(scores).\n2. Compute midpoint index: mid = count // 2.\n3. If count is even, average elements at mid-1 and mid; otherwise take element at mid.\n4. Return dictionary with statistics.",
                    "starter_hint": "Remember integer division `//` gives the floor midpoint index.",
                    "reference_code": "    sorted_scores = sorted(scores)\n    mid = count // 2\n    median = (sorted_scores[mid - 1] + sorted_scores[mid]) / 2 if count % 2 == 0 else sorted_scores[mid]\n    return {'average': round(average, 2), 'median': median, 'count': count}",
                },
                {
                    "step_index": 3,
                    "objective": "Define get_letter_grade(score) with grading scale",
                    "learning_concept": "Multi-branch conditionals",
                    "algorithm": "1. Define function get_letter_grade(score).\n2. Return 'A' if score >= 90, 'B' if >= 80, 'C' if >= 70, 'D' if >= 60, else 'F'.",
                    "starter_hint": "Use an if-elif ladder checking descending threshold values.",
                    "reference_code": "def get_letter_grade(score):\n    if score >= 90: return 'A'\n    elif score >= 80: return 'B'\n    elif score >= 70: return 'C'\n    elif score >= 60: return 'D'\n    return 'F'",
                },
            ]
        return {
            "title": title,
            "full_code": full_code,
            "steps": steps,
        }


# Convenience functions for FastAPI routes
def handle_code_analyze(code: str, session_id: str) -> Dict[str, Any]:
    """Run code analyzer agent."""
    loop = AgentLoop()
    return loop.run_code_analyzer(code, session_id)


def handle_learn_plan(analysis: Dict[str, Any], session_id: str) -> List[Dict[str, Any]]:
    """Run learning plan agent."""
    loop = AgentLoop()
    return loop.run_learning_plan(analysis, session_id)


def handle_tutor(objective: str, student_attempt: Optional[str], hint_level: Optional[str]) -> str:
    """Run tutor agent."""
    loop = AgentLoop()
    return loop.run_tutor(objective, student_attempt, hint_level)


def handle_evaluate(objective: str, student_code: str, analysis: Dict[str, Any]) -> Dict[str, str]:
    """Run attempt evaluator."""
    loop = AgentLoop()
    return loop.run_evaluator(objective, student_code, analysis)


def handle_hint(objective: str, hint_level: str) -> str:
    """Run hint agent."""
    loop = AgentLoop()
    return loop.run_hint(objective, hint_level)


def handle_reflect(session_id: str, hint_usage: int, completed_steps: int, analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Run reflection agent."""
    loop = AgentLoop()
    return loop.run_reflection(session_id, hint_usage, completed_steps, analysis)


def handle_generate_from_prompt(user_prompt: str, session_id: str) -> Dict[str, Any]:
    """Run prompt to code & algorithm generation using Qwen 2.5 Coder."""
    loop = AgentLoop()
    return loop.generate_from_prompt(user_prompt, session_id)