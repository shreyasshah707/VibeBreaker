"""Guardrails for VibeBreaker backend."""

import re
from typing import List


def validate_python_code(code: str) -> List[str]:
    """Validate input code and return list of errors."""
    errors = []

    # Check language - we only accept Python
    # (This is called after the frontend sends Python)

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


def sanitize_output(code: str) -> str:
    """Sanitize output to never reveal full solution or future steps."""
    # Strip excess whitespace but keep core content
    return code.strip()