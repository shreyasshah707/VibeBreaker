# 2-Minute Hackathon Demo Script

## Introduction (30 seconds)
"Welcome to VibeBreaker, an anti–vibe-coding learning tool. I'll demonstrate how it helps students reconstruct Python code step by step, ensuring they actually understand what they're writing."

## Demo Flow (2 minutes)

### Step 1: Paste the Reference Code (30 seconds)
"Here's a simple Python code that calculates student grades. The student will paste this reference code, and VibeBreaker will break it down into reconstruction objectives."

**Code shown:**
```python
def calculate_average(scores):
    """Calculate the average of a list of scores."""
    total = 0
    for score in scores:
        total += score
    return total / len(scores)

def main():
    scores = [85, 90, 78, 92, 88]
    average = calculate_average(scores)
    print(f"Class average: {average}")
```

### Step 2: Generate Objectives ( instant)
"Click 'Break the Vibe' and VibeBreaker uses an open-weight LLM to analyze the code and generate 7 reconstruction objectives, ordered from simplest to most complex."

**First objective shown:** "Define a function named `calculate_average` that accepts a list of numeric scores and returns their average."

### Step 3: Student Reconstruction (45 seconds)
"The student types the code objective by objective. Let me demonstrate with the first objective..."

**Student types:** `def calculate_average(scores):` ✓

**Click 'Check my code'** → Feedback: "Good start! Now add the return statement."

### Step 4: Hints Escalation (30 seconds)
"If the student gets stuck, they can request hints that escalate:

1. **Conceptual hint**: High-level guidance about what the objective is asking
2. **Narrower hint**: More specific direction toward the solution
3. **Code hint**: Maximum 3 lines of code pointing in the right direction

Each hint level must be explicitly requested before the next one is available."

### Step 5: Session Completion (20 seconds)
"After completing all 7 objectives, the student gets a summary:

- **Patterns practiced**: function definition, control flow, variable usage
- **Areas needing hints**: variable scope, function returns
- **Viva questions**: 3 questions based on their reconstructed code"

## Conclusion (10 seconds)
"VibeBreaker ensures students actively learn by reconstructing code themselves. No code generation for the student — just guided reconstruction. Thank you!"

## Key Demo Points
- Student pastes AI-generated reference code
- System generates 5-10 reconstruction objectives
- Student types code one objective at a time
- Meaningful feedback on each attempt
- Hints escalate correctly (conceptual → narrower → code, max 3 lines)
- Session summary with patterns and viva questions
- No full solution revealed at any point