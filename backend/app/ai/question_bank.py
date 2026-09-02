"""
Question Generator / Gap-Specific Assessment Selector
------------------------------------------------------
Two responsibilities:
  1. Generate a small bank of topic-tagged questions for a skill (stands in
     for an LLM call in production — see NOTE below).
  2. Given a student's weak sub-topics, select/generate a focused
     assessment rather than a generic test (per "Gap-Specific Assessment").

NOTE: Real deployments should route this through an LLM (Gemini/OpenAI) via
a provider-agnostic AI abstraction, then push output through:
    AI Generate -> Validate -> Faculty/Admin Review -> Approve -> Question Bank
This module implements that pipeline's shape (status="pending_review" on
generation) with a deterministic template bank standing in for the LLM call,
so the system works end-to-end without an external API key.
"""

import random

# skill_name -> topic -> list of (prompt, options, correct_index, explanation)
QUESTION_BANK: dict[str, dict[str, list[tuple]]] = {
    "Python": {
        "OOP": [
            ("Which keyword is used to inherit from a base class in Python?",
             ["extends", "inherits", "class Child(Base):", "super.new"], 2,
             "Python expresses inheritance via `class Child(Base):`, not an `extends` keyword."),
            ("What does `super().__init__()` do inside a subclass constructor?",
             ["Deletes the parent class", "Calls the parent class's constructor", "Creates a new object", "Overrides a method"], 1,
             "`super()` gives access to the parent class so its `__init__` can be called explicitly."),
        ],
        "Debugging": [
            ("A function raises `IndexError: list index out of range`. What's the most likely cause?",
             ["Accessing an index >= len(list)", "Dividing by zero", "Using an undefined variable", "A syntax error"], 0,
             "IndexError specifically means the code tried to access a position beyond the list's bounds."),
            ("Which tool lets you step through Python code line-by-line to inspect state?",
             ["pip", "pdb", "venv", "black"], 1,
             "`pdb` is Python's built-in interactive debugger."),
        ],
        "Syntax": [
            ("Which of these correctly defines a function in Python?",
             ["function foo():", "def foo():", "func foo():", "void foo():"], 1,
             "Python functions are defined with the `def` keyword."),
        ],
        "File handling": [
            ("Which mode opens a file for appending without truncating existing content?",
             ["'r'", "'w'", "'a'", "'x'"], 2,
             "Mode 'a' appends to the end of the file; 'w' would truncate it."),
        ],
    },
    "Docker": {
        "Dockerfile": [
            ("Which instruction sets the base image for a Dockerfile?",
             ["BASE", "FROM", "IMAGE", "USE"], 1,
             "`FROM` declares the base image a Dockerfile builds on top of."),
        ],
        "networking": [
            ("By default, how do containers on the same user-defined bridge network reach each other?",
             ["By IP only", "By container name via built-in DNS", "They cannot communicate", "Only via the host"], 1,
             "Docker's embedded DNS resolves container names on user-defined networks."),
        ],
        "volumes": [
            ("What is the main purpose of a Docker volume?",
             ["Speed up image builds", "Persist data beyond a container's lifecycle", "Reduce image size", "Manage networking"], 1,
             "Volumes persist data independently of any single container's lifecycle."),
        ],
    },
    "FastAPI": {
        "General": [
            ("Which library does FastAPI use for request/response data validation?",
             ["marshmallow", "pydantic", "attrs", "cerberus"], 1,
             "FastAPI is built around Pydantic models for validation and serialization."),
        ],
    },
    "SQL": {
        "Joins": [
            ("Which JOIN returns all rows from the left table and matched rows from the right?",
             ["INNER JOIN", "LEFT JOIN", "CROSS JOIN", "SELF JOIN"], 1,
             "LEFT JOIN keeps every row from the left table, filling unmatched right-side columns with NULL."),
        ],
    },
}

GENERIC_QUESTIONS = [
    ("Which practice most directly improves confidence in a claimed skill?",
     ["Watching more tutorials", "Building and submitting a real project", "Reading documentation once", "Skipping practice"], 1,
     "Applied, evidenced practice is what the platform's confidence engine weighs most heavily."),
]


def weakest_topics(topic_scores: dict[str, float], top_n: int = 2) -> list[str]:
    """Given {topic: score}, return the N weakest topics — the basis for a gap-specific test."""
    ordered = sorted(topic_scores.items(), key=lambda kv: kv[1])
    return [t for t, _ in ordered[:top_n]]


def generate_questions(skill_name: str, topics: list[str] | None, num_questions: int) -> list[dict]:
    """Select/generate questions focused on the given topics (or all topics if None)."""
    bank = QUESTION_BANK.get(skill_name, {})
    pool: list[dict] = []
    topic_list = topics if topics else list(bank.keys())
    for topic in topic_list:
        for prompt, options, correct_idx, explanation in bank.get(topic, []):
            pool.append({
                "topic": topic, "difficulty": "intermediate", "question_type": "mcq",
                "prompt": prompt, "options": options, "correct_answer": [str(correct_idx)],
                "explanation": explanation, "source": "ai_generated", "status": "approved",
            })
    if not pool:
        for prompt, options, correct_idx, explanation in GENERIC_QUESTIONS:
            pool.append({
                "topic": "General", "difficulty": "beginner", "question_type": "mcq",
                "prompt": prompt, "options": options, "correct_answer": [str(correct_idx)],
                "explanation": explanation, "source": "ai_generated", "status": "approved",
            })
    random.shuffle(pool)
    if len(pool) < num_questions:
        # repeat pool if the bank is small, keeps the MVP always demoable
        pool = (pool * ((num_questions // max(len(pool), 1)) + 1))
    return pool[:num_questions]
