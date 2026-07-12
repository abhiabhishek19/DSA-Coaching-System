# """
# graph.py
# Builds and compiles the LangGraph StateGraph for the DSA Coach.

# Node sequence with conditional edges:

#   START
#     │
#     ▼
#   question_picker          (selects 5 problems from dataset)
#     │
#     ▼
#   question_display         (interrupt — renders question card)
#     │
#     ▼
#   user_approach            (interrupt — user types approach)
#     │
#     ▼
#   code_generator           (LLM generates code from approach)
#     │
#     ▼
#   leetcode_hitl            (interrupt — user runs on LeetCode, reports result)
#     │
#     ├── success ──────────────────────────────────────────▶ next_question
#     │                                                              │
#     └── failure                                                    │
#           │                                                        │
#           ▼                                                        │
#     approach_judge          (LLM judges if approach is sound)     │
#           │                                                        │
#           ├── approach_ok ──▶ code_analyser                       │
#           │                       │                               │
#           │                       ├── auto_fix ──▶ code_generator  │
#           │                       │                               │
#           │                       └── self_edit ─▶ leetcode_hitl  │
#           │                                                        │
#           └── approach_wrong ─▶ approach_wrong_node               │
#                                       │                           │
#                                       └──▶ code_generator         │
#                                                                    │
#   next_question ◀────────────────────────────────────────────────┘
#     │
#     ├── more questions ──▶ question_display  (loop)
#     │
#     └── all done ──────▶ session_summary
#                                │
#                              END
# """

# from langgraph.graph import StateGraph, START, END
# from langgraph.checkpoint.memory import MemorySaver

# from state import DSAState
# from nodes import (
#     question_picker_node,
#     question_display_node,
#     user_approach_node,
#     code_generator_node,
#     leetcode_hitl_node,
#     approach_judge_node,
#     code_analyser_node,
#     approach_wrong_node,
#     next_question_node,
#     session_summary_node,
# )


# # ── Router functions ──────────────────────────────────────────────────────────

# def route_after_hitl(state: DSAState) -> str:
#     """After LeetCodeHITL: go to next question or judge the approach."""
#     return state.get("next_action", "judge_approach")


# def route_after_judge(state: DSAState) -> str:
#     """After ApproachJudge: go to code analyser or approach revision."""
#     return state.get("next_action", "analyse_code")


# def route_after_analyser(state: DSAState) -> str:
#     """After CodeAnalyser: user chose self_edit (back to hitl) or auto_fix."""
#     choice = state.get("fix_choice", "self_edit")
#     if choice == "auto_fix":
#         return "generate_code"
#     return "leetcode_hitl"   # self_edit: user fixes and re-submits


# def route_after_approach_wrong(state: DSAState) -> str:
#     """After ApproachWrong: always regenerate code from revised approach."""
#     return "generate_code"


# def route_after_next_question(state: DSAState) -> str:
#     """After NextQuestion: loop to display if more, else summary."""
#     return state.get("next_action", "question_display")


# # ── Graph builder ─────────────────────────────────────────────────────────────

# def build_graph():
#     """Build, compile, and return the DSA Coach graph with MemorySaver."""

#     builder = StateGraph(DSAState)

#     # ── Register all nodes ────────────────────────────────────────────────────
#     builder.add_node("question_picker",   question_picker_node)
#     builder.add_node("question_display",  question_display_node)
#     builder.add_node("user_approach",     user_approach_node)
#     builder.add_node("code_generator",    code_generator_node)
#     builder.add_node("leetcode_hitl",     leetcode_hitl_node)
#     builder.add_node("approach_judge",    approach_judge_node)
#     builder.add_node("code_analyser",     code_analyser_node)
#     builder.add_node("approach_wrong",    approach_wrong_node)
#     builder.add_node("next_question",     next_question_node)
#     builder.add_node("session_summary",   session_summary_node)

#     # ── Fixed edges ───────────────────────────────────────────────────────────
#     builder.add_edge(START,              "question_picker")
#     builder.add_edge("question_picker",  "question_display")
#     builder.add_edge("question_display", "user_approach")
#     builder.add_edge("user_approach",    "code_generator")

#     # ── Conditional edges ─────────────────────────────────────────────────────

#     # After code generation → always to leetcode_hitl
#     builder.add_edge("code_generator", "leetcode_hitl")

#     # After HITL result → next_question (success) OR approach_judge (failure)
#     builder.add_conditional_edges(
#         "leetcode_hitl",
#         route_after_hitl,
#         {
#             "next_question":  "next_question",
#             "judge_approach": "approach_judge",
#         },
#     )

#     # After ApproachJudge → code_analyser (ok) OR approach_wrong (flawed)
#     builder.add_conditional_edges(
#         "approach_judge",
#         route_after_judge,
#         {
#             "analyse_code":   "code_analyser",
#             "approach_wrong": "approach_wrong",
#         },
#     )

#     # After CodeAnalyser → code_generator (auto_fix) OR leetcode_hitl (self_edit)
#     builder.add_conditional_edges(
#         "code_analyser",
#         route_after_analyser,
#         {
#             "generate_code": "code_generator",
#             "leetcode_hitl": "leetcode_hitl",
#         },
#     )

#     # After ApproachWrong (revised approach) → always regenerate code
#     builder.add_edge("approach_wrong", "code_generator")

#     # After NextQuestion → loop back to display OR end with summary
#     builder.add_conditional_edges(
#         "next_question",
#         route_after_next_question,
#         {
#             "question_display": "question_display",
#             "session_summary":  "session_summary",
#         },
#     )

#     # Session summary → END
#     builder.add_edge("session_summary", END)

#     # ── Compile with MemorySaver (required for interrupt()) ───────────────────
#     checkpointer = MemorySaver()
#     return builder.compile(checkpointer=checkpointer)






















from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from state import DSAState
from nodes import (
    question_picker_node,
    question_display_node,
    user_approach_node,
    code_generator_node,
    leetcode_hitl_node,
    approach_judge_node,
    code_analyser_node,
    approach_wrong_node,
    next_question_node,
    session_summary_node,
)


# ── Router functions ──────────────────────────────────────────────────────────

def route_after_hitl(state: DSAState) -> str:
    """
    After LeetCodeHITL:
      next_action="next_question"  → next_question node
      next_action="judge_approach" → approach_judge node
    """
    return state.get("next_action", "judge_approach")


def route_after_analyser(state: DSAState) -> str:
    """
    After CodeAnalyser — three possible paths:
      fix_choice="auto_fix"        → code_generator    (AI regenerates with fix)
      fix_choice="self_edit"       → leetcode_hitl     (user edits themselves)
      fix_choice="revise_approach" → approach_wrong    (user rewrites approach)
    """
    choice = state.get("fix_choice", "self_edit")
    if choice == "auto_fix":
        return "generate_code"
    if choice == "revise_approach":
        return "approach_wrong"
    return "leetcode_hitl"


def route_after_next_question(state: DSAState) -> str:
    """
    After NextQuestion:
      next_action="display"          → question_display (loop to next)
      next_action="session_summary"  → session_summary  (all done)
    """
    action = state.get("next_action", "display")
    if action == "session_summary":
        return "session_summary"
    return "question_display"


# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph():
    """Build, compile, and return the DSA Coach graph with MemorySaver."""

    builder = StateGraph(DSAState)

    # ── Register nodes ────────────────────────────────────────────────────────
    builder.add_node("question_picker",  question_picker_node)
    builder.add_node("question_display", question_display_node)
    builder.add_node("user_approach",    user_approach_node)
    builder.add_node("code_generator",   code_generator_node)
    builder.add_node("leetcode_hitl",    leetcode_hitl_node)
    builder.add_node("approach_judge",   approach_judge_node)
    builder.add_node("code_analyser",    code_analyser_node)
    builder.add_node("approach_wrong",   approach_wrong_node)
    builder.add_node("next_question",    next_question_node)
    builder.add_node("session_summary",  session_summary_node)

    # ── Fixed edges (unconditional) ───────────────────────────────────────────
    builder.add_edge(START,             "question_picker")
    builder.add_edge("question_picker", "question_display")
    builder.add_edge("question_display","user_approach")
    # After user_approach: generate code OR skip straight to next question
    builder.add_conditional_edges(
        "user_approach",
        lambda s: s.get("next_action", "generate_code"),
        {
            "generate_code": "code_generator",
            "skip_to_next":  "next_question",
        },
    )
    builder.add_edge("code_generator",  "leetcode_hitl")

    # approach_wrong always leads back to code_generator (revised approach)
    builder.add_edge("approach_wrong",  "code_generator")

    # session_summary is the terminal node
    builder.add_edge("session_summary", END)

    # ── Conditional edges ─────────────────────────────────────────────────────

    # After HITL: success → next_question | failure → approach_judge
    builder.add_conditional_edges(
        "leetcode_hitl",
        route_after_hitl,
        {
            "next_question":  "next_question",
            "judge_approach": "approach_judge",
        },
    )

    # approach_judge ALWAYS flows to code_analyser.
    # The verdict is stored in approach_verdict and used as context
    # inside code_analyser — not as a routing branch anymore.
    builder.add_edge("approach_judge", "code_analyser")

    # After CodeAnalyser: three paths
    #   auto_fix        → code_generator  (AI regenerates with fix context)
    #   self_edit       → leetcode_hitl   (user edits and re-submits)
    #   revise_approach → approach_wrong  (user rewrites approach from scratch)
    builder.add_conditional_edges(
        "code_analyser",
        route_after_analyser,
        {
            "generate_code":  "code_generator",
            "leetcode_hitl":  "leetcode_hitl",
            "approach_wrong": "approach_wrong",
        },
    )

    # After NextQuestion: more questions → question_display | done → session_summary
    builder.add_conditional_edges(
        "next_question",
        route_after_next_question,
        {
            "question_display": "question_display",
            "session_summary":  "session_summary",
        },
    )

    # ── Compile with MemorySaver (required for interrupt()) ───────────────────
    return builder.compile(checkpointer=MemorySaver())
