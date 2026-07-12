# """
# nodes.py
# All LangGraph node functions for the DSA Coach workflow.

# Node sequence:
#   QuestionPickerNode
#       → QuestionDisplayNode  (interrupt — user reads the question)
#       → UserApproachNode     (interrupt — user types their approach)
#       → CodeGeneratorNode    (LLM writes code from approach)
#       → LeetCodeHITLNode     (interrupt — user pastes success/failure)
#       → [if success] NextQuestionNode
#       → [if failure] ApproachJudgeNode
#                    → CodeAnalyserNode
#                    → FixChoiceNode    (interrupt — self-edit or auto-fix)
#                    → [auto-fix] CodeGeneratorNode (loop)
#                    → [self-edit] LeetCodeHITLNode (loop with edited code)
#       → SessionSummaryNode
# """

# from langgraph.types import interrupt
# from langchain_groq import ChatGroq
# from langchain_core.messages import SystemMessage, HumanMessage
# from dotenv import load_dotenv

# from state import DSAState
# from dataset import pick_daily_questions, fuzzy_match_tags, get_all_tags, load_dataset
# import state

# load_dotenv()

# # ── Shared LLM instance ───────────────────────────────────────────────────────
# # Using Groq (free) — swap to ChatMistralAI or ChatOpenAI if preferred
# llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)


# # ═════════════════════════════════════════════════════════════════════════════
# # NODE 1 — QuestionPickerNode
# # ═════════════════════════════════════════════════════════════════════════════
# def question_picker_node(state: DSAState) -> dict:
#     """
#     Reads topics and language from state (set by Streamlit before invoking),
#     matches them to dataset tags, and picks 5 problems for today's session.
#     """
#     problems = load_dataset()
#     all_tags = get_all_tags(problems)

#     # Fuzzy-match user's topic input to official dataset tags
#     matched_topics = fuzzy_match_tags(state["topic_input"], all_tags)

#     if not matched_topics:
#         # Fallback: use Array + Dynamic Programming if nothing matched
#         matched_topics = ["Array", "Dynamic Programming"]

#     daily_questions, warnings = pick_daily_questions(
#         topics=matched_topics,
#         problems=problems,
#     )

#     return {
#         "topics": matched_topics,
#         "daily_questions": daily_questions,
#         "question_index": 0,
#         "current_question": daily_questions[0],
#         "session_history": [],
#         "attempt": 0,
#         "next_action": "question_display",
#     }


# # ═════════════════════════════════════════════════════════════════════════════
# # NODE 2 — QuestionDisplayNode
# # ═════════════════════════════════════════════════════════════════════════════
# def question_display_node(state: DSAState) -> dict:
#     """
#     Formats the current problem and interrupts so the Streamlit UI
#     can render the question card. No LLM call — pure formatting.
#     """
#     q = state["current_question"]
#     idx = state["question_index"]

#     display_payload = {
#         "question_number": idx + 1,
#         "total": len(state["daily_questions"]),
#         "title": q["task_id"].replace("-", " ").title(),
#         "question_id": q.get("question_id", ""),
#         "difficulty": q["difficulty"],
#         "tags": q.get("tags", []),
#         "problem_description": q["problem_description"],
#         "starter_code": q.get("starter_code", ""),
#         "language": state["language"],
#     }

#     # interrupt() pauses the graph here.
#     # The UI reads display_payload from result['__interrupt__'][0].value
#     # and renders the question card.
#     interrupt(display_payload)

#     return {"next_action": "approach"}


# # ═════════════════════════════════════════════════════════════════════════════
# # NODE 3 — UserApproachNode
# # ═════════════════════════════════════════════════════════════════════════════
# def user_approach_node(state: DSAState) -> dict:
#     """
#     Interrupts to collect the user's approach description.
#     The UI shows a text area. The user's typed text is passed back
#     via Command(resume=approach_text).
#     """
#     approach_text = interrupt({
#         "prompt": (
#             "Describe your approach in plain English. Be as detailed as you want:\n"
#             "- What algorithm / technique are you using?\n"
#             "- What data structures?\n"
#             "- Step-by-step logic if you have it.\n\n"
#             "The code will be generated based ONLY on what you describe here."
#         )
#     })

#     return {
#         "user_approach": approach_text,
#         "next_action": "generate_code",
#     }


# # ═════════════════════════════════════════════════════════════════════════════
# # NODE 4 — CodeGeneratorNode
# # ═════════════════════════════════════════════════════════════════════════════
# def code_generator_node(state: DSAState) -> dict:
#     """
#     Calls the LLM to generate code based ONLY on the user's described approach.

#     Critical system prompt constraint: the LLM must not introduce any logic,
#     optimisation, or data structure that the user did not mention.
#     If the approach is incomplete, the LLM generates as far as described
#     and adds TODO comments for the rest.

#     Supports both C++ and Python output.
#     """
#     q = state["current_question"]
#     language = state.get("language", "cpp")
#     approach = state["user_approach"]
#     analysis = state.get("analysis", "")   # populated on retry iterations

#     lang_label = "C++" if language == "cpp" else "Python"

#     # Build the starter code guidance
#     starter_note = ""
#     if q.get("starter_code") and language == "python":
#         starter_note = f"\nThe Python starter code structure is:\n```python\n{q['starter_code']}\n```\n"
#     elif language == "cpp":
#         starter_note = (
#             "\nFor C++, use the standard LeetCode class structure:\n"
#             "```cpp\nclass Solution {\npublic:\n    // method here\n};\n```\n"
#             "Include only necessary standard headers (e.g. #include <vector>, "
#             "#include <unordered_map>, #include <string>).\n"
#         )

#     # If this is a retry, include the previous analysis as context
#     retry_context = ""
#     if analysis:
#         retry_context = (
#             f"\n\n--- PREVIOUS ATTEMPT ANALYSIS ---\n"
#             f"The user's previous code failed. Here is the analysis:\n{analysis}\n"
#             f"The user has chosen to auto-fix. Revise the code to address the issues "
#             f"described in the analysis, but ONLY using logic consistent with the "
#             f"user's original approach. Do not introduce unrelated changes.\n"
#             f"--- END ANALYSIS ---\n"
#         )

#     system_prompt = f"""You are a strict coding assistant that writes {lang_label} code ONLY based on what the user explicitly describes.

# ABSOLUTE RULES — never break these:
# 1. Implement ONLY what the user's approach says. Word for word.
# 2. Do NOT add optimisations, edge case handling, or logic the user did not mention.
# 3. Do NOT change the algorithm to a different one even if the user's approach is suboptimal.
# 4. If the user's approach is incomplete, write what you can and add a comment:
#    // TODO: [describe what the user needs to specify here]
# 5. Do NOT explain the code. Output only the code block.
# 6. Write syntactically correct, compilable {lang_label}.
# 7. For {lang_label}, use LeetCode's standard submission format.

# Your job is to be the user's hands, not their brain."""

#     human_prompt = f"""Problem: {q['task_id'].replace('-', ' ').title()} (LeetCode #{q.get('question_id', '')})

# Problem Description:
# {q['problem_description']}
# {starter_note}
# User's Approach:
# {approach}
# {retry_context}
# Generate {lang_label} code implementing exactly and only the user's described approach."""

#     messages = [
#         SystemMessage(content=system_prompt),
#         HumanMessage(content=human_prompt),
#     ]

#     response = llm.invoke(messages)
#     code = response.content.strip()

#     # Strip markdown fences if the LLM added them
#     if code.startswith("```"):
#         lines = code.split("\n")
#         # Remove first line (```cpp or ```python) and last line (```)
#         code = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

#     return {
#         "generated_code": code,
#         "next_action": "leetcode_hitl",
#     }


# # ═════════════════════════════════════════════════════════════════════════════
# # NODE 5 — LeetCodeHITLNode
# # ═════════════════════════════════════════════════════════════════════════════
# def leetcode_hitl_node(state: DSAState) -> dict:
#     """
#     Pauses the workflow after code generation.
#     The UI shows the generated code with copy functionality.
#     The user pastes the code into LeetCode, runs it, and then reports back:
#       - "success" → move to next question
#       - "failure" + paste of error/output → go to ApproachJudge + CodeAnalyser
#     """
#     hitl_response = interrupt({
#         "prompt": (
#             "Paste the code above into LeetCode and run it.\n\n"
#             "Come back and tell us:\n"
#             "1. Did it pass? Type 'success'\n"
#             "2. Did it fail? Type 'failure' and then paste the error "
#             "output or wrong answer in the box below."
#         ),
#         "generated_code": state["generated_code"],
#         "language": state.get("language", "cpp"),
#     })

#     # hitl_response is a dict: {"result": "success"/"failure", "error": "..."}
#     result = hitl_response.get("result", "failure")
#     error_paste = hitl_response.get("error", "")

#     if result == "success":
#         # Record in session history
#         q = state["current_question"]
#         history_entry = {
#             "question_number": state["question_index"] + 1,
#             "title": q["task_id"].replace("-", " ").title(),
#             "difficulty": q["difficulty"],
#             "tags": q.get("tags", []),
#             "approach": state["user_approach"],
#             "attempts": state["attempt"] + 1,
#             "outcome": "✅ Solved",
#         }
#         return {
#             "leetcode_result": "success",
#             "session_history": state.get("session_history", []) + [history_entry],
#             "next_action": "next_question",
#         }
#     else:
#         return {
#             "leetcode_result": "failure",
#             "user_error_paste": error_paste,
#             "attempt": state.get("attempt", 0) + 1,
#             "next_action": "judge_approach",
#         }


# # ═════════════════════════════════════════════════════════════════════════════
# # NODE 6 — ApproachJudgeNode
# # ═════════════════════════════════════════════════════════════════════════════
# def approach_judge_node(state: DSAState) -> dict:
#     """
#     Evaluates whether the user's approach is fundamentally correct but had
#     an implementation bug, OR whether the approach itself is flawed.

#     This distinction matters:
#     - Implementation bug → CodeAnalyser can fix the code
#     - Flawed approach → user needs a conceptual redirect first
#     """
#     q = state["current_question"]

#     system_prompt = """You are a senior competitive programmer and DSA coach.
# Your job is to evaluate a student's problem-solving approach and identify
# whether it is conceptually sound or fundamentally flawed.

# Be direct, constructive, and educational. Do not give away the full solution.
# Identify the SPECIFIC gap between the student's approach and what is needed."""

#     human_prompt = f"""Problem: {q['task_id'].replace('-', ' ').title()}

# Problem Description:
# {q['problem_description']}

# Student's Approach:
# {state['user_approach']}

# Generated Code (based on student's approach):
# {state['generated_code']}

# LeetCode Error / Wrong Output:
# {state['user_error_paste']}

# Evaluate:
# 1. Is the student's APPROACH conceptually correct or fundamentally wrong?
# 2. If the approach is correct but implementation failed, what specifically failed?
# 3. If the approach is wrong, what key concept is the student missing?
#    (Give a hint, not the full answer)
# 4. What is your verdict: "approach_ok" or "approach_wrong"?

# Format your response exactly like this:
# VERDICT: approach_ok OR approach_wrong
# ANALYSIS: [your detailed explanation]"""

#     messages = [
#         SystemMessage(content=system_prompt),
#         HumanMessage(content=human_prompt),
#     ]

#     response = llm.invoke(messages)
#     content = response.content.strip()

#     # Parse verdict
#     verdict = "approach_ok"
#     if "VERDICT:" in content:
#         verdict_line = [l for l in content.split("\n") if "VERDICT:" in l]
#         if verdict_line:
#             verdict = "approach_wrong" if "approach_wrong" in verdict_line[0].lower() else "approach_ok"

#     # Parse analysis
#     analysis = content
#     if "ANALYSIS:" in content:
#         analysis = content.split("ANALYSIS:", 1)[1].strip()

#     next_action = "analyse_code" if verdict == "approach_ok" else "approach_wrong"

#     return {
#         "approach_feedback": f"**Verdict:** {'Approach is sound — implementation issue' if verdict == 'approach_ok' else 'Approach needs rethinking'}\n\n{analysis}",
#         "next_action": next_action,
#     }


# # ═════════════════════════════════════════════════════════════════════════════
# # NODE 7 — CodeAnalyserNode
# # ═════════════════════════════════════════════════════════════════════════════
# def code_analyser_node(state: DSAState) -> dict:
#     """
#     Deep analysis of WHY the code failed and HOW to fix it,
#     staying within the bounds of the user's original approach.

#     Then interrupts to offer the user a choice:
#     - "self_edit": user will fix it themselves
#     - "auto_fix":  CodeGeneratorNode re-runs with analysis as context
#     """
#     q = state["current_question"]
#     language = state.get("language", "cpp")
#     lang_label = "C++" if language == "cpp" else "Python"

#     system_prompt = f"""You are a {lang_label} debugging expert and DSA coach.
# Analyse the failing code and explain EXACTLY what is wrong and how to fix it.
# Stay within the logic of the student's described approach — do not suggest a different algorithm.
# Be specific about which line(s) are wrong and why."""

#     human_prompt = f"""Problem: {q['task_id'].replace('-', ' ').title()}

# Student's Approach:
# {state['user_approach']}

# {lang_label} Code (failed):
# {state['generated_code']}

# LeetCode Error / Wrong Output:
# {state['user_error_paste']}

# Previous approach feedback: {state.get('approach_feedback', 'None')}

# Provide:
# 1. Root cause of the failure (be specific — line numbers if relevant)
# 2. Exact fix needed (staying within student's approach)
# 3. Why this fix resolves the issue
# 4. Time and space complexity of the current approach

# Format as:
# ROOT CAUSE: ...
# FIX NEEDED: ...
# WHY IT WORKS: ...
# COMPLEXITY: Time O(...) | Space O(...)"""

#     messages = [
#         SystemMessage(content=system_prompt),
#         HumanMessage(content=human_prompt),
#     ]

#     response = llm.invoke(messages)
#     analysis = response.content.strip()

#     # Interrupt to show the analysis and ask for fix choice
#     fix_choice = interrupt({
#         "analysis": analysis,
#         "approach_feedback": state.get("approach_feedback", ""),
#         "generated_code": state["generated_code"],
#         "language": language,
#         "prompt": (
#             "Here is the analysis of what went wrong.\n\n"
#             "What would you like to do?\n"
#             "  A) I'll fix it myself  →  type 'self_edit'\n"
#             "  B) Fix it for me       →  type 'auto_fix'"
#         ),
#     })

#     return {
#         "analysis": analysis,
#         "fix_choice": fix_choice,
#         "next_action": fix_choice,  # "self_edit" or "auto_fix"
#     }


# # ═════════════════════════════════════════════════════════════════════════════
# # NODE 8 — ApproachWrongNode
# # ═════════════════════════════════════════════════════════════════════════════
# def approach_wrong_node(state: DSAState) -> dict:
#     """
#     Called when ApproachJudgeNode decides the approach is fundamentally flawed.
#     Interrupts to show the feedback and ask the user to revise their approach
#     before the code is regenerated.
#     """
#     revised_approach = interrupt({
#         "feedback": state.get("approach_feedback", ""),
#         "current_approach": state["user_approach"],
#         "prompt": (
#             "Your approach needs some rethinking. Read the feedback above.\n\n"
#             "Revise your approach and describe it again below.\n"
#             "The code will be regenerated from your revised approach."
#         ),
#     })

#     return {
#         "user_approach": revised_approach,
#         "analysis": "",   # clear previous analysis for fresh generation
#         "next_action": "generate_code",
#     }


# # ═════════════════════════════════════════════════════════════════════════════
# # NODE 9 — NextQuestionNode
# # ═════════════════════════════════════════════════════════════════════════════
# def next_question_node(state: DSAState) -> dict:
#     """
#     Advances to the next question or signals session end.
#     Resets all per-question state fields.
#     """
#     new_index = state["question_index"] + 1

#     if new_index >= len(state["daily_questions"]):
#         return {
#             "question_index": new_index,
#             "next_action": "session_summary",
#         }

#     next_question = state["daily_questions"][new_index]

#     return {
#         "question_index": new_index,
#         "current_question": next_question,
#         "user_approach": "",
#         "generated_code": "",
#         "leetcode_result": "",
#         "user_error_paste": "",
#         "approach_feedback": "",
#         "analysis": "",
#         "fix_choice": "",
#         "attempt": 0,
#         "next_action": "question_display",
#     }


# # ═════════════════════════════════════════════════════════════════════════════
# # NODE 10 — SessionSummaryNode
# # ═════════════════════════════════════════════════════════════════════════════
# def session_summary_node(state: DSAState) -> dict:
#     """
#     Generates a summary of today's session and interrupts to display it.
#     No LLM call — pure data aggregation.
#     """
#     history = state.get("session_history", [])
#     total = len(state["daily_questions"])
#     solved = sum(
#     1 for h in state["session_history"]
#     if "Solved" in h["outcome"]
# )

#     summary = {
#         "topics_practiced": state.get("topics", []),
#         "language": state.get("language", "cpp"),
#         "total_questions": total,
#         "solved": solved,
#         "skipped_or_ongoing": total - solved,
#         "questions": history,
#         "message": (
#             f"Session complete! You solved {solved}/{total} problems today. "
#             f"{'Great work! 🎉' if solved == total else 'Keep practising — consistency beats perfection!'}"
#         ),
#     }

#     interrupt({"summary": summary})

#     return {"next_action": "done"}



























from langgraph.types import interrupt
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv
from typing import Dict, Any

from state import DSAState
from dataset import pick_daily_questions, fuzzy_match_tags, get_all_tags, load_dataset

load_dotenv()

# ── LLM — shared across all nodes that need it ───────────────────────────────
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0.3)


# ═════════════════════════════════════════════════════════════════════════════
# NODE 1 — QuestionPickerNode
# ═════════════════════════════════════════════════════════════════════════════
def question_picker_node(state: DSAState) -> Dict[str, Any]:
    """
    Loads the dataset, fuzzy-matches user topics to official tags,
    and picks 5 problems according to the difficulty distribution.
    Runs once at session start with no LLM call.
    """
    problems  = load_dataset()
    all_tags  = get_all_tags(problems)

    matched_topics = fuzzy_match_tags(state["topic_input"], all_tags)
    if not matched_topics:
        matched_topics = ["Array", "Dynamic Programming"]  # safe fallback

    # Pass difficulty distribution from state if provided, else use default
    distribution = state.get("difficulty_distribution") or {"Easy": 2, "Medium": 2, "Hard": 1}

    daily_questions, warnings = pick_daily_questions(
        topics=matched_topics,
        distribution=distribution,
        problems=problems,
    )

    if not daily_questions:
        # Absolute fallback: reset seen and try again
        from dataset import reset_seen_ids
        reset_seen_ids()
        daily_questions, _ = pick_daily_questions(
            topics=matched_topics,
            distribution=distribution,
            problems=problems,
        )

    return {
        "topics":           matched_topics,
        "daily_questions":  daily_questions,
        "question_index":   0,
        "current_question": daily_questions[0],
        "session_history":  [],
        "attempt":          0,
        "next_action":      "display",
    }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 2 — QuestionDisplayNode
# ═════════════════════════════════════════════════════════════════════════════
def question_display_node(state: DSAState) -> Dict[str, Any]:
    """
    Formats the current problem and interrupts so the Streamlit UI
    can render it. The user acknowledges by clicking a button;
    the resume value (True) is intentionally ignored here — we only
    need the interrupt to pause execution.
    """
    q   = state["current_question"]
    idx = state["question_index"]

    display_payload = {
        "question_number":      idx + 1,
        "total":                len(state["daily_questions"]),
        "title":                q["task_id"].replace("-", " ").title(),
        "question_id":          q.get("question_id", ""),
        "difficulty":           q["difficulty"],
        "tags":                 q.get("tags", []),
        "problem_description":  q["problem_description"],
        "starter_code":         q.get("starter_code", ""),
        "language":             state["language"],
    }

    # Pause — UI renders the question; user clicks "I'm Ready"
    interrupt(display_payload)

    # Resume value is ignored; always move to approach input
    return {"next_action": "approach"}


# ═════════════════════════════════════════════════════════════════════════════
# NODE 3 — UserApproachNode
# ═════════════════════════════════════════════════════════════════════════════
def user_approach_node(state: DSAState) -> Dict[str, Any]:
    """
    Interrupts to collect the user's approach description.

    Two possible resume values from the UI:
      Command(resume="__SKIP__")           -> skip this question entirely
      Command(resume="I'll use a hashmap") -> normal flow, generate code

    Skip bypasses CodeGenerator and LeetCodeHITL entirely and jumps
    straight to NextQuestionNode. The skipped question is recorded in
    skipped_questions (not session_history which tracks solved ones).
    """
    approach_text: str = interrupt({
        "prompt": (
            "Describe your approach in plain English:\n"
            "- What algorithm / technique are you using?\n"
            "- What data structures?\n"
            "- Step-by-step logic if you have it.\n\n"
            "Code will be generated based ONLY on what you describe."
        )
    })

    if approach_text == "__SKIP__":
        q = state["current_question"]
        skip_entry = {
            "question_number": state["question_index"] + 1,
            "title":           q["task_id"].replace("-", " ").title(),
            "difficulty":      q["difficulty"],
            "tags":            q.get("tags", []),
            "outcome":         "Skipped",
        }
        return {
            "user_approach":     "",
            "skipped_questions": state.get("skipped_questions", []) + [skip_entry],
            "next_action":       "skip_to_next",
        }

    return {
        "user_approach": approach_text,
        "next_action":   "generate_code",
    }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 4 — CodeGeneratorNode
# ═════════════════════════════════════════════════════════════════════════════
def code_generator_node(state: DSAState) -> Dict[str, Any]:
    """
    Calls the LLM to write code based ONLY on the user's described approach.

    - Supports C++ and Python output.
    - On retry (analysis != ""), injects previous failure analysis as context.
    - Strips all markdown code fences from the LLM output.
    - NEVER introduces logic the user did not describe.
    """
    q          = state["current_question"]
    language   = state.get("language", "cpp")
    approach   = state.get("user_approach", "")
    analysis   = state.get("analysis", "")
    lang_label = "C++" if language == "cpp" else "Python"

    # Starter code hint
    if language == "python" and q.get("starter_code"):
        starter_note = (
            f"\nUse this Python starter code structure:\n"
            f"```python\n{q['starter_code']}\n```\n"
        )
    elif language == "cpp":
        starter_note = (
            "\nUse standard LeetCode C++ class structure:\n"
            "```cpp\nclass Solution {\npublic:\n    // method here\n};\n```\n"
            "Include only necessary headers "
            "(e.g. #include <vector>, #include <unordered_map>).\n"
        )
    else:
        starter_note = ""

    # Retry context (only present on auto-fix iteration)
    retry_context = ""
    if analysis:
        retry_context = (
            f"\n\n--- PREVIOUS ATTEMPT ANALYSIS ---\n"
            f"{analysis}\n"
            f"Revise the code to fix the issues above. "
            f"Stay within the user's original approach — do NOT change the algorithm.\n"
            f"--- END ANALYSIS ---\n"
        )

    system_prompt = (
        f"You are a strict coding assistant. Write {lang_label} code ONLY based "
        f"on what the user explicitly describes.\n\n"
        f"RULES:\n"
        f"1. Implement ONLY what the user's approach says.\n"
        f"2. Do NOT add optimisations or logic the user did not mention.\n"
        f"3. Do NOT switch to a different algorithm.\n"
        f"4. If the approach is incomplete, write what you can and add "
        f"   // TODO: <what the user needs to specify> comments.\n"
        f"5. Output ONLY the code block. No explanations, no prose.\n"
        f"6. Write syntactically correct, compilable {lang_label}.\n"
        f"7. Use LeetCode's standard submission format."
    )

    human_prompt = (
        f"Problem: {q['task_id'].replace('-', ' ').title()} "
        f"(LeetCode #{q.get('question_id', '')})\n\n"
        f"Problem Description:\n{q['problem_description']}\n"
        f"{starter_note}\n"
        f"User's Approach:\n{approach}\n"
        f"{retry_context}\n"
        f"Generate {lang_label} code implementing exactly the user's described approach."
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ])

    code = _strip_code_fences(response.content.strip())

    return {
        "generated_code": code,
        "next_action":    "leetcode_hitl",
    }


def _strip_code_fences(text: str) -> str:
    """
    Remove markdown code fences (```cpp, ```python, ```) from LLM output.
    Handles both opening and closing fences robustly.
    """
    lines = text.split("\n")
    if lines and lines[0].startswith("```"):
        lines = lines[1:]           # remove opening fence
    if lines and lines[-1].strip() == "```":
        lines = lines[:-1]          # remove closing fence
    return "\n".join(lines).strip()


# ═════════════════════════════════════════════════════════════════════════════
# NODE 5 — LeetCodeHITLNode
# ═════════════════════════════════════════════════════════════════════════════
def leetcode_hitl_node(state: DSAState) -> Dict[str, Any]:
    """
    Pauses after code generation. UI shows the code and two buttons:
      ✅ "It Passed"  → Command(resume={"result": "success", "error": ""})
      ❌ "It Failed"  → Command(resume={"result": "failure", "error": "<paste>"})

    The resume value is a dict — parsed here to update state.
    """
    hitl_response: Dict = interrupt({
        "generated_code": state["generated_code"],
        "language":       state.get("language", "cpp"),
        "prompt": (
            "Paste the code into LeetCode and run it.\n\n"
            "Then report back:\n"
            "  • Passed → click 'It Passed'\n"
            "  • Failed → click 'It Failed' and paste the error output"
        ),
    })

    # hitl_response is guaranteed to be a dict by the UI layer
    result      = hitl_response.get("result", "failure")
    error_paste = hitl_response.get("error", "")

    if result == "success":
        q = state["current_question"]
        history_entry = {
            "question_number": state["question_index"] + 1,
            "title":           q["task_id"].replace("-", " ").title(),
            "difficulty":      q["difficulty"],
            "tags":            q.get("tags", []),
            "approach":        state.get("user_approach", ""),
            "attempts":        state.get("attempt", 0) + 1,
            "outcome":         "✅ Solved",
        }
        return {
            "leetcode_result":  "success",
            "session_history":  state.get("session_history", []) + [history_entry],
            "next_action":      "next_question",
        }
    else:
        return {
            "leetcode_result":  "failure",
            "user_error_paste": error_paste,
            "attempt":          state.get("attempt", 0) + 1,
            "next_action":      "judge_approach",
        }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 6 — ApproachJudgeNode
# ═════════════════════════════════════════════════════════════════════════════
def approach_judge_node(state: DSAState) -> Dict[str, Any]:
    """
    LLM evaluates whether the failure was:
      (a) an implementation bug — approach is conceptually OK → route to CodeAnalyser
      (b) a fundamentally wrong approach → route to ApproachWrongNode

    Parses VERDICT: from LLM output to determine next_action.
    """
    q = state["current_question"]

    system_prompt = (
        "You are a senior competitive programmer and DSA coach.\n"
        "Evaluate the student's approach and determine whether it is "
        "conceptually sound (just a code bug) or fundamentally wrong.\n"
        "Be direct and educational. Do NOT give away the full solution.\n"
        "Identify the SPECIFIC gap.\n\n"
        "Respond in EXACTLY this format (no extra lines before VERDICT:):\n"
        "VERDICT: approach_ok\n"
        "ANALYSIS: <your explanation>\n\n"
        "OR\n\n"
        "VERDICT: approach_wrong\n"
        "ANALYSIS: <your explanation>"
    )

    human_prompt = (
        f"Problem: {q['task_id'].replace('-', ' ').title()}\n\n"
        f"Problem Description:\n{q['problem_description']}\n\n"
        f"Student's Approach:\n{state.get('user_approach', '')}\n\n"
        f"Generated Code (based on approach):\n{state.get('generated_code', '')}\n\n"
        f"LeetCode Error / Wrong Output:\n{state.get('user_error_paste', '')}\n\n"
        "Evaluate and respond using the VERDICT/ANALYSIS format above."
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ])
    content = response.content.strip()

    # Parse verdict — default to approach_ok so we don't lose context
    verdict = "approach_ok"
    for line in content.split("\n"):
        if line.strip().upper().startswith("VERDICT:"):
            if "approach_wrong" in line.lower():
                verdict = "approach_wrong"
            break

    # Parse analysis
    analysis_text = content
    if "ANALYSIS:" in content:
        analysis_text = content.split("ANALYSIS:", 1)[1].strip()

    verdict_label = (
        "Approach is sound — implementation issue"
        if verdict == "approach_ok"
        else "Approach needs rethinking"
    )
    feedback = f"**Verdict:** {verdict_label}\n\n{analysis_text}"

    # Always route to code_analyser so the user sees the full code analysis
    # regardless of verdict. The verdict is passed as context into code_analyser
    # which then offers the appropriate fix options (including revise_approach
    # when the approach is fundamentally wrong).
    return {
        "approach_feedback": feedback,
        "approach_verdict":  verdict,          # "approach_ok" or "approach_wrong"
        "next_action":       "analyse_code",   # always — no more skipping analyser
    }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 7 — CodeAnalyserNode
# ═════════════════════════════════════════════════════════════════════════════
def code_analyser_node(state: DSAState) -> Dict[str, Any]:
    """
    Always runs after ApproachJudge — regardless of verdict.

    Two modes depending on approach_verdict:
      "approach_ok"    → deep line-by-line code debug. Fix options:
                          A) self_edit   — user edits on LeetCode themselves
                          B) auto_fix    — AI regenerates with fix context
      "approach_wrong" → explains what the approach is missing conceptually
                         AND still analyses the code. Fix options:
                          A) self_edit      — user edits on LeetCode themselves
                          B) auto_fix       — AI regenerates with fix context
                          C) revise_approach — user rewrites their approach
                                              from scratch (goes to ApproachWrongNode)

    interrupt() returns the user's choice string:
      Command(resume="self_edit") / Command(resume="auto_fix") / Command(resume="revise_approach")
    """
    q               = state["current_question"]
    language        = state.get("language", "cpp")
    lang_label      = "C++" if language == "cpp" else "Python"
    approach_verdict = state.get("approach_verdict", "approach_ok")

    # Build system prompt based on verdict
    if approach_verdict == "approach_wrong":
        system_prompt = (
            f"You are a {lang_label} debugging expert and DSA coach.\n"
            "The student's approach has a conceptual flaw, but you must STILL "
            "analyse the generated code in detail so the student understands "
            "exactly what went wrong at the code level AND at the logic level.\n\n"
            "Do NOT just say 'change your approach'. Show:\n"
            "1. What the code is doing wrong line by line\n"
            "2. Why the current approach leads to this failure\n"
            "3. What conceptual insight the student is missing (hint, not full answer)\n"
            "Be specific, educational, and constructive."
        )
    else:
        system_prompt = (
            f"You are a {lang_label} debugging expert and DSA coach.\n"
            "The student's approach is conceptually sound but the code has a bug.\n"
            "Analyse the failing code and explain EXACTLY what is wrong and how to fix it.\n"
            "Stay within the student's described approach — do NOT suggest a different algorithm.\n"
            "Be specific about which lines are wrong and why."
        )

    human_prompt = (
        f"Problem: {q['task_id'].replace('-', ' ').title()}\n\n"
        f"Student's Approach:\n{state.get('user_approach', '')}\n\n"
        f"{lang_label} Code (failed):\n{state.get('generated_code', '')}\n\n"
        f"LeetCode Error / Wrong Output:\n{state.get('user_error_paste', '')}\n\n"
        f"Approach verdict: {approach_verdict}\n"
        f"Approach feedback from judge: {state.get('approach_feedback', 'None')}\n\n"
        "Respond in this format:\n"
        "ROOT CAUSE: ...\n"
        "CODE ISSUE: ...\n"
        "FIX NEEDED: ...\n"
        "WHY IT WORKS: ...\n"
        "COMPLEXITY: Time O(...) | Space O(...)"
    )

    response = llm.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ])
    analysis = response.content.strip()

    # Build interrupt payload — include approach_verdict so UI knows
    # whether to show the third "Revise Approach" button
    fix_choice: str = interrupt({
        "analysis":          analysis,
        "approach_feedback": state.get("approach_feedback", ""),
        "approach_verdict":  approach_verdict,
        "generated_code":    state.get("generated_code", ""),
        "language":          language,
        "prompt": (
            "Read the analysis above.\n\n"
            "What would you like to do?\n"
            "  A) I'll fix it myself\n"
            "  B) Auto-fix for me\n"
            + ("  C) My approach is wrong — let me revise it\n"
               if approach_verdict == "approach_wrong" else "")
        ),
    })

    # Normalise fix_choice to one of three valid values
    if not isinstance(fix_choice, str):
        fix_choice = "self_edit"
    fix_choice = fix_choice.strip().lower()
    if fix_choice not in ("self_edit", "auto_fix", "revise_approach"):
        fix_choice = "self_edit"

    return {
        "analysis":    analysis,
        "fix_choice":  fix_choice,
        "next_action": fix_choice,
    }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 8 — ApproachWrongNode
# ═════════════════════════════════════════════════════════════════════════════
def approach_wrong_node(state: DSAState) -> Dict[str, Any]:
    """
    Called when the approach is fundamentally flawed.
    Interrupts to show coach feedback and collect the user's revised approach.
    Command(resume="revised approach text...") → stored as user_approach.
    """
    revised_approach: str = interrupt({
        "feedback":         state.get("approach_feedback", ""),
        "current_approach": state.get("user_approach", ""),
        "prompt": (
            "Your approach needs rethinking. Read the feedback above.\n\n"
            "Revise your approach below — the code will be regenerated from it."
        ),
    })

    return {
        "user_approach": revised_approach,
        "analysis":      "",   # clear so code_generator won't inject old analysis
        "next_action":   "generate_code",
    }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 9 — NextQuestionNode
# ═════════════════════════════════════════════════════════════════════════════
def next_question_node(state: DSAState) -> Dict[str, Any]:
    """
    Advances to the next question or signals session end.
    Resets all per-question state fields so previous question data
    does not bleed into the next question.
    """
    new_index = state["question_index"] + 1

    if new_index >= len(state["daily_questions"]):
        return {
            "question_index": new_index,
            "next_action":    "session_summary",
        }

    return {
        "question_index":   new_index,
        "current_question": state["daily_questions"][new_index],
        "user_approach":    "",
        "generated_code":   "",
        "leetcode_result":  "",
        "user_error_paste": "",
        "approach_feedback": "",
        "analysis":         "",
        "fix_choice":       "",
        "attempt":          0,
        "next_action":      "display",
    }


# ═════════════════════════════════════════════════════════════════════════════
# NODE 10 — SessionSummaryNode
# ═════════════════════════════════════════════════════════════════════════════
def session_summary_node(state: DSAState) -> Dict[str, Any]:
    """
    Aggregates session results and interrupts for the summary screen.
    No LLM call — pure data collection.

    session_history  = questions the user actually attempted (solved or failed)
    skipped_questions = questions the user explicitly skipped
    """
    history  = state.get("session_history", [])
    skipped  = state.get("skipped_questions", [])
    solved   = sum(1 for h in history if "Solved" in h.get("outcome", ""))
    attempted = len(history)
    total_qs  = len(state.get("daily_questions", [])) or (attempted + len(skipped))

    summary = {
        "topics_practiced": state.get("topics", []),
        "language":         state.get("language", "cpp"),
        "total_questions":  total_qs,
        "attempted":        attempted,
        "solved":           solved,
        "skipped":          len(skipped),
        "attempted_questions": history,
        "skipped_questions":   skipped,
        "message": (
            f"Session complete! Solved {solved}/{total_qs} · "
            f"Attempted {attempted} · Skipped {len(skipped)}. "
            + ("Perfect score! 🎉" if solved == total_qs
               else "Great effort — keep practising! 💪")
        ),
    }

    interrupt({"summary": summary})
    return {"next_action": "done"}
