# """
# state.py
# Defines the shared LangGraph state for the DSA Coach workflow.
# Every node reads from and writes to this TypedDict.
# """

# from typing import TypedDict, Optional


# class DSAState(TypedDict):
#     # ── Session setup ─────────────────────────────────────────────────────────
#     topic_input: str            # raw comma-separated topics from the user
#     topics: list[str]           # cleaned list e.g. ["Array", "Dynamic Programming"]
#     language: str               # "cpp" or "python" — chosen by user at start

#     # ── Daily question pool ───────────────────────────────────────────────────
#     daily_questions: list[dict] # 5 selected problem dicts from dataset
#     question_index: int         # which question we are on (0-4)
#     current_question: dict      # the active problem dict

#     # ── Per-question working state ────────────────────────────────────────────
#     user_approach: str          # user's typed approach description
#     generated_code: str         # code produced by CodeGeneratorNode
#     leetcode_result: str        # "success" or "failure"
#     user_error_paste: str       # error/output pasted by user from LeetCode
#     approach_feedback: str      # ApproachJudgeNode's verdict on the approach
#     analysis: str               # CodeAnalyserNode's detailed fix explanation
#     fix_choice: str             # "self_edit" or "auto_fix"
#     revised_approach: str       # only used when user chooses to revise approach

#     # ── Session history ───────────────────────────────────────────────────────
#     session_history: list[dict] # one entry per completed question
#     attempt: int                # retry attempts on the current question

#     # ── Flow control ─────────────────────────────────────────────────────────
#     next_action: str            # used by routers to signal next node


























from typing import TypedDict, List, Dict, Optional


class DSAState(TypedDict):
    # ── Session setup ─────────────────────────────────────────────────────────
    topic_input: str            # raw comma-separated topics from the user
    topics: List[str]           # cleaned list e.g. ["Array", "Dynamic Programming"]
    language: str               # "cpp" or "python" — chosen by user at start

    # ── Daily question pool ───────────────────────────────────────────────────
    daily_questions: List[Dict] # 5 selected problem dicts from dataset
    question_index: int         # which question we are on (0-4)
    current_question: Dict      # the active problem dict

    # ── Per-question working state ────────────────────────────────────────────
    user_approach: str          # user's typed approach description
    generated_code: str         # code produced by CodeGeneratorNode
    leetcode_result: str        # "success" or "failure"
    user_error_paste: str       # error/output pasted by user from LeetCode
    approach_feedback: str      # ApproachJudgeNode's human-readable verdict
    approach_verdict: str       # "approach_ok" or "approach_wrong" — raw routing signal
    analysis: str               # CodeAnalyserNode's detailed fix explanation
    fix_choice: str             # "self_edit" or "auto_fix"
    revised_approach: str       # only used when user chooses to revise approach

    # ── Session history ───────────────────────────────────────────────────────
    session_history: List[Dict]  # attempted questions (solved or failed)
    skipped_questions: List[Dict] # questions the user explicitly skipped
    attempt: int                # retry attempts on the current question

    # ── Flow control ─────────────────────────────────────────────────────────
    next_action: str            # used by routers to signal next node
