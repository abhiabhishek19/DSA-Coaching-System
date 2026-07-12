# """
# app.py
# Streamlit UI for the DSA Coach — LangGraph-powered DSA preparation assistant.

# Run with:  streamlit run app.py
# """

# import streamlit as st
# from langgraph.types import Command
# import time

# from graph import build_graph
# from dataset import load_dataset, get_all_tags, fuzzy_match_tags, reset_seen_ids

# # ── Page config ───────────────────────────────────────────────────────────────
# st.set_page_config(
#     page_title="DSA Coach — AI Prep Assistant",
#     page_icon="🧠",
#     layout="wide",
#     initial_sidebar_state="expanded",
# )

# # ── Custom CSS ────────────────────────────────────────────────────────────────
# st.markdown("""
# <style>
# /* Question card */
# .question-card {
#     background: #1e1e2e;
#     border: 1px solid #313244;
#     border-radius: 12px;
#     padding: 1.5rem;
#     margin-bottom: 1rem;
# }
# /* Difficulty badges */
# .badge-easy   { background:#1a4d1a; color:#86efac; padding:3px 12px;
#                 border-radius:999px; font-size:0.8rem; font-weight:600; }
# .badge-medium { background:#4a3010; color:#fcd34d; padding:3px 12px;
#                 border-radius:999px; font-size:0.8rem; font-weight:600; }
# .badge-hard   { background:#4a1010; color:#fca5a5; padding:3px 12px;
#                 border-radius:999px; font-size:0.8rem; font-weight:600; }
# /* Tag pill */
# .tag-pill { background:#2d2d3f; color:#a5b4fc; padding:2px 10px;
#             border-radius:999px; font-size:0.75rem; margin:2px;
#             display:inline-block; }
# /* Code header bar */
# .code-header { background:#313244; border-radius:8px 8px 0 0;
#                padding:6px 14px; font-size:0.8rem; color:#cdd6f4;
#                font-family:monospace; }
# /* Analysis box */
# .analysis-box { background:#1e1e2e; border-left:4px solid #f38ba8;
#                 border-radius:0 8px 8px 0; padding:1rem;
#                 margin:0.5rem 0; }
# /* Success box */
# .success-box  { background:#1a4d1a; border-left:4px solid #a6e3a1;
#                 border-radius:0 8px 8px 0; padding:1rem; }
# </style>
# """, unsafe_allow_html=True)


# # ── Graph — compiled once, cached ─────────────────────────────────────────────
# @st.cache_resource
# def get_graph():
#     return build_graph()

# app = get_graph()


# # ── Session state initialisation ──────────────────────────────────────────────
# def init_session():
#     defaults = {
#         "thread_id":       None,
#         "graph_result":    None,
#         "phase":           "setup",      # setup | running | done
#         "interrupt_type":  None,
#         "interrupt_data":  None,
#         "config":          None,
#         "topic_input":     "",
#         "language":        "cpp",
#     }
#     for k, v in defaults.items():
#         if k not in st.session_state:
#             st.session_state[k] = v

# init_session()


# # ── Helper: read interrupt from graph result ───────────────────────────────────
# def get_interrupt(result: dict):
#     """Extract interrupt payload from a graph result dict."""
#     interrupts = result.get("__interrupt__", [])
#     if interrupts:
#         return interrupts[0].value
#     return None


# # ── Helper: determine interrupt type from payload keys ────────────────────────
# def classify_interrupt(payload: dict) -> str:
#     if payload is None:
#         return "none"
#     if "summary" in payload:
#         return "session_summary"
#     if "question_number" in payload:
#         return "question_display"
#     if "generated_code" in payload and "prompt" in payload:
#         return "leetcode_hitl"
#     if "analysis" in payload:
#         return "code_analyser"
#     if "feedback" in payload and "current_approach" in payload:
#         return "approach_wrong"
#     if "prompt" in payload and "question_number" not in payload:
#         return "user_approach"
#     return "unknown"


# # ── Helper: render difficulty badge ───────────────────────────────────────────
# def difficulty_badge(diff: str) -> str:
#     cls = {"Easy": "easy", "Medium": "medium", "Hard": "hard"}.get(diff, "easy")
#     return f'<span class="badge-{cls}">{diff}</span>'


# # ── Helper: render tag pills ──────────────────────────────────────────────────
# def tag_pills(tags: list) -> str:
#     return " ".join(f'<span class="tag-pill">{t}</span>' for t in tags)


# # ════════════════════════════════════════════════════════════════
# # SIDEBAR
# # ════════════════════════════════════════════════════════════════
# with st.sidebar:
#     st.title("🧠 DSA Coach")
#     st.caption("LangGraph · LangChain · Groq")
#     st.divider()

#     if st.session_state["phase"] == "setup":
#         st.subheader("Session Setup")

#         # Load all tags for the autocomplete hint
#         try:
#             problems = load_dataset()
#             all_tags = get_all_tags(problems)
#         except FileNotFoundError:
#             problems = []
#             all_tags = []

#         # Topic input
#         topic_input = st.text_input(
#             "📚 Topics to practice (comma-separated)",
#             placeholder="e.g. Array, Dynamic Programming, Graph",
#             help="Fuzzy matching — 'dp' → 'Dynamic Programming', 'bfs' → 'Breadth-First Search'",
#         )

#         # Show matched tags live
#         if topic_input and all_tags:
#             matched = fuzzy_match_tags(topic_input, all_tags)
#             if matched:
#                 st.caption(f"✅ Matched: **{', '.join(matched)}**")
#             else:
#                 st.caption("⚠️ No tags matched. Try: Array, DP, Graph, Tree, String...")

#         # Language selector
#         language = st.radio(
#             "💻 Code Language",
#             options=["cpp", "python"],
#             format_func=lambda x: "C++" if x == "cpp" else "Python",
#             index=0,
#         )

#         # Difficulty distribution
#         st.subheader("Difficulty Mix (5 questions)")
#         col1, col2, col3 = st.columns(3)
#         with col1:
#             n_easy   = st.number_input("Easy",   min_value=0, max_value=5, value=2)
#         with col2:
#             n_medium = st.number_input("Medium", min_value=0, max_value=5, value=2)
#         with col3:
#             n_hard   = st.number_input("Hard",   min_value=0, max_value=5, value=1)

#         st.divider()

#         start_clicked = st.button(
#             "🚀 Start Today's Session",
#             disabled=not topic_input,
#             use_container_width=True,
#             type="primary",
#         )

#         if start_clicked and topic_input:
#             import uuid
#             thread_id = str(uuid.uuid4())
#             config    = {"configurable": {"thread_id": thread_id}}

#             initial_state = {
#                 "topic_input":      topic_input,
#                 "language":         language,
#                 "daily_questions":  [],
#                 "question_index":   0,
#                 "current_question": {},
#                 "user_approach":    "",
#                 "generated_code":   "",
#                 "leetcode_result":  "",
#                 "user_error_paste": "",
#                 "approach_feedback":"",
#                 "analysis":         "",
#                 "fix_choice":       "",
#                 "revised_approach": "",
#                 "session_history":  [],
#                 "attempt":          0,
#                 "next_action":      "",
#                 "topics":           [],
#             }

#             with st.spinner("Loading dataset and picking questions…"):
#                 result = app.invoke(initial_state, config=config)

#             st.session_state.update({
#                 "thread_id":    thread_id,
#                 "config":       config,
#                 "graph_result": result,
#                 "phase":        "running",
#                 "topic_input":  topic_input,
#                 "language":     language,
#             })
#             st.rerun()

#         st.divider()
#         if st.button("🔄 Reset Seen Questions", use_container_width=True):
#             reset_seen_ids()
#             st.success("Seen questions cleared!")

#     else:
#         # Running / done sidebar info
#         st.subheader("Current Session")
#         result = st.session_state.get("graph_result", {})
#         qi     = result.get("question_index", 0)
#         total  = len(result.get("daily_questions", []))
#         topics = result.get("topics", [])
#         lang   = result.get("language", "cpp")

#         st.metric("Questions", f"{qi}/{total}")
#         st.caption(f"**Topics:** {', '.join(topics)}")
#         st.caption(f"**Language:** {'C++' if lang == 'cpp' else 'Python'}")

#         st.divider()
#         history = result.get("session_history", [])
#         if history:
#             st.subheader("Completed")
#             for h in history:
#                 icon = "✅" if "Solved" in h.get("outcome","") else "❌"
#                 st.caption(f"{icon} Q{h['question_number']}: {h['title']} ({h['difficulty']})")

#         st.divider()
#         if st.button("🏁 End Session Early", use_container_width=True):
#             st.session_state["phase"] = "setup"
#             st.session_state["graph_result"] = None
#             st.rerun()


# # ════════════════════════════════════════════════════════════════
# # MAIN AREA
# # ════════════════════════════════════════════════════════════════

# if st.session_state["phase"] == "setup":
#     # ── Landing screen ────────────────────────────────────────────────────────
#     st.title("🧠 DSA Coach — AI-Powered Interview Preparation")
#     st.markdown("""
#     Welcome to your personal DSA preparation assistant powered by **LangGraph + LangChain**.

#     ### How it works
#     1. **Pick your topics** in the sidebar (e.g. *Array, Dynamic Programming*)
#     2. **Choose your language** — C++ or Python
#     3. **Get 5 curated problems** daily from the LeetCode dataset (2,641 problems)
#     4. **Describe your approach** — the AI generates code based ONLY on your logic
#     5. **Copy the code** to LeetCode and test it yourself
#     6. **Report back** — if it fails, paste the error and get targeted analysis
#     7. **Choose** to fix it yourself or let the AI auto-fix within your approach

#     ### Dataset
#     - **2,641 LeetCode problems** (638 Easy · 1,397 Medium · 606 Hard)
#     - **63 topic tags** — Array, DP, Graph, Tree, String, Backtracking, and more
#     - Problems never repeat across sessions (tracked locally in `seen_ids.json`)

#     ---
#     👈 **Configure your session in the sidebar and click Start!**
#     """)

# elif st.session_state["phase"] == "running":
#     result  = st.session_state["graph_result"]
#     config  = st.session_state["config"]
#     payload = get_interrupt(result)
#     itype   = classify_interrupt(payload)

#     # ── INTERRUPT: Question Display ───────────────────────────────────────────
#     if itype == "question_display":
#         q_num  = payload["question_number"]
#         total  = payload["total"]
#         title  = payload["title"]
#         diff   = payload["difficulty"]
#         tags   = payload["tags"]
#         desc   = payload["problem_description"]
#         sc     = payload.get("starter_code", "")
#         lang   = payload["language"]

#         # Progress bar
#         st.progress(q_num / total, text=f"Question {q_num} of {total}")
#         st.markdown("---")

#         # Title row
#         col1, col2 = st.columns([3, 1])
#         with col1:
#             st.markdown(
#                 f"### #{payload.get('question_id','')} — {title} &nbsp;"
#                 f"{difficulty_badge(diff)}",
#                 unsafe_allow_html=True,
#             )
#         with col2:
#             st.markdown(tag_pills(tags), unsafe_allow_html=True)

#         st.markdown("---")

#         # Problem description
#         st.markdown("#### 📋 Problem Description")
#         st.markdown(
#             f'<div class="question-card">{desc.replace(chr(10), "<br>")}</div>',
#             unsafe_allow_html=True,
#         )

#         # Starter code (Python reference only — user writes C++ on LeetCode)
#         if sc:
#             lang_label = "cpp" if lang == "cpp" else "python"
#             note = " (Python reference — you'll write C++ on LeetCode)" if lang == "cpp" else ""
#             st.markdown(f"#### 🔧 Starter Code{note}")
#             st.code(sc, language="python")

#         st.markdown("---")
#         st.info("✅ Read the problem carefully, then click below to describe your approach.")

#         if st.button("📝 I'm Ready — Describe My Approach →", type="primary", use_container_width=True):
#             with st.spinner("Loading approach input…"):
#                 result = app.invoke(Command(resume=True), config=config)
#             st.session_state["graph_result"] = result
#             st.rerun()

#     # ── INTERRUPT: User Approach Input ────────────────────────────────────────
#     elif itype == "user_approach":
#         q_state = result
#         qi = q_state.get("question_index", 0)
#         cq = q_state.get("current_question", {})
#         lang = q_state.get("language", "cpp")

#         st.markdown(f"### 💭 Describe Your Approach")
#         st.caption(
#             f"**{cq.get('task_id','').replace('-',' ').title()}** · "
#             f"{cq.get('difficulty','')} · "
#             f"{', '.join(cq.get('tags',[]))}"
#         )
#         st.markdown("---")

#         st.info(
#             "Describe your approach in plain English. Be as detailed as you want.\n\n"
#             f"The AI will generate **{'C++' if lang == 'cpp' else 'Python'}** code "
#             "based **ONLY** on what you describe here — nothing more, nothing less."
#         )

#         approach_text = st.text_area(
#             "Your approach:",
#             height=200,
#             placeholder=(
#                 "Example:\n"
#                 "I'll use a hash map to store each number and its index as I iterate.\n"
#                 "For each number, I'll check if target - current_number exists in the map.\n"
#                 "If yes, return [map[target-num], current_index].\n"
#                 "If no, add current_number:index to the map and continue."
#             ),
#         )

#         col1, col2 = st.columns([1, 1])
#         with col1:
#             generate = st.button(
#                 "⚡ Generate Code from My Approach",
#                 disabled=not approach_text.strip(),
#                 type="primary",
#                 use_container_width=True,
#             )
#         with col2:
#             skip = st.button("⏭️ Skip This Question", use_container_width=True)

#         if generate and approach_text.strip():
#             with st.spinner("Generating code from your approach…"):
#                 result = app.invoke(Command(resume=approach_text.strip()), config=config)
#             st.session_state["graph_result"] = result
#             st.rerun()

#         if skip:
#             # Resume with a placeholder approach, then mark as skipped
#             with st.spinner("Skipping…"):
#                 result = app.invoke(Command(resume="[SKIPPED BY USER]"), config=config)
#             st.session_state["graph_result"] = result
#             st.rerun()

#     # ── INTERRUPT: LeetCode HITL ──────────────────────────────────────────────
#     elif itype == "leetcode_hitl":
#         q_state = result
#         lang    = payload.get("language", "cpp")
#         code    = payload["generated_code"]
#         lang_label = "cpp" if lang == "cpp" else "python"

#         qi = q_state.get("question_index", 0)
#         cq = q_state.get("current_question", {})
#         attempt = q_state.get("attempt", 0)

#         st.markdown("### ⚡ Generated Code")
#         if attempt > 0:
#             st.warning(f"🔄 Attempt {attempt + 1} — revised code based on previous analysis")

#         st.caption(
#             f"**{cq.get('task_id','').replace('-',' ').title()}** · "
#             f"Language: {'C++' if lang == 'cpp' else 'Python'}"
#         )

#         # Code header bar + code block
#         st.markdown(
#             f'<div class="code-header">{"C++" if lang == "cpp" else "Python"} · '
#             f'{cq.get("task_id","").replace("-"," ").title()}</div>',
#             unsafe_allow_html=True,
#         )
#         st.code(code, language=lang_label)

#         # Copy instructions
#         st.info(
#             "📋 **Next steps:**\n\n"
#             "1. Select all the code above and copy it  \n"
#             "2. Go to LeetCode → find the problem → paste into the code editor  \n"
#             "3. Change the language to **C++** (or Python) if needed  \n"
#             "4. Click **Run** or **Submit**  \n"
#             "5. Come back here and report the result below"
#         )

#         st.markdown("---")
#         st.markdown("#### 📊 What happened on LeetCode?")

#         col1, col2 = st.columns(2)

#         with col1:
#             if st.button("✅ It Passed! Move to Next Question", type="primary", use_container_width=True):
#                 with st.spinner("Recording success…"):
#                     result = app.invoke(
#                         Command(resume={"result": "success", "error": ""}),
#                         config=config,
#                     )
#                 st.session_state["graph_result"] = result
#                 st.balloons()
#                 time.sleep(0.5)
#                 st.rerun()

#         with col2:
#             if st.button("❌ It Failed — Let's Analyse", use_container_width=True):
#                 st.session_state["show_error_input"] = True

#         # Error paste area — shown only when user clicks "It Failed"
#         if st.session_state.get("show_error_input", False):
#             st.markdown("---")
#             st.markdown("#### 🔍 Paste the Error / Wrong Output")
#             st.caption(
#                 "Paste the full error message, wrong answer output, or "
#                 "Time Limit Exceeded message from LeetCode."
#             )
#             error_paste = st.text_area(
#                 "LeetCode output:",
#                 height=150,
#                 placeholder=(
#                     "e.g.\nWrong Answer\nInput: nums = [2,7,11,15], target = 9\n"
#                     "Output: []\nExpected: [0,1]\n\nor\n\nRuntime Error: ...\n"
#                     "or\nTime Limit Exceeded"
#                 ),
#             )

#             if st.button(
#                 "🔬 Analyse the Failure →",
#                 disabled=not error_paste.strip(),
#                 type="primary",
#                 use_container_width=True,
#             ):
#                 st.session_state["show_error_input"] = False
#                 with st.spinner("Analysing your code and approach…"):
#                     result = app.invoke(
#                         Command(resume={"result": "failure", "error": error_paste.strip()}),
#                         config=config,
#                     )
#                 st.session_state["graph_result"] = result
#                 st.rerun()

#     # ── INTERRUPT: Code Analyser (fix choice) ─────────────────────────────────
#     elif itype == "code_analyser":
#         approach_feedback = payload.get("approach_feedback", "")
#         analysis          = payload["analysis"]
#         code              = payload.get("generated_code", "")
#         lang              = payload.get("language", "cpp")
#         lang_label        = "cpp" if lang == "cpp" else "python"

#         st.markdown("### 🔬 Code Analysis")
#         st.markdown("---")

#         # Show approach feedback if available
#         if approach_feedback:
#             st.markdown("#### 🧠 Approach Verdict")
#             st.markdown(
#                 f'<div class="success-box">{approach_feedback}</div>',
#                 unsafe_allow_html=True,
#             )
#             st.markdown("")

#         # Show full analysis
#         st.markdown("#### 🔍 Detailed Analysis")
#         st.markdown(
#             f'<div class="analysis-box">{analysis.replace(chr(10), "<br>")}</div>',
#             unsafe_allow_html=True,
#         )

#         # Show the failing code for reference
#         with st.expander("📄 View the failing code"):
#             st.code(code, language=lang_label)

#         st.markdown("---")
#         st.markdown("#### What would you like to do?")

#         col1, col2 = st.columns(2)

#         with col1:
#             st.markdown("**Option A — I'll fix it myself**")
#             st.caption(
#                 "You've read the analysis. Go back to LeetCode, "
#                 "edit the code yourself, and re-submit. "
#                 "Then come back and report the result."
#             )
#             if st.button("✏️ I'll Fix It Myself", use_container_width=True):
#                 with st.spinner("Noted — heading back to result reporting…"):
#                     result = app.invoke(Command(resume="self_edit"), config=config)
#                 st.session_state["graph_result"] = result
#                 st.session_state["show_error_input"] = False
#                 st.rerun()

#         with col2:
#             st.markdown("**Option B — Auto-fix for me**")
#             st.caption(
#                 "The AI will revise the code based on the analysis above, "
#                 "staying within your original approach. "
#                 "A new code block will be generated."
#             )
#             if st.button("🤖 Auto-Fix My Code", type="primary", use_container_width=True):
#                 with st.spinner("Regenerating code with fix applied…"):
#                     result = app.invoke(Command(resume="auto_fix"), config=config)
#                 st.session_state["graph_result"] = result
#                 st.session_state["show_error_input"] = False
#                 st.rerun()

#     # ── INTERRUPT: Approach Wrong (needs revision) ────────────────────────────
#     elif itype == "approach_wrong":
#         feedback         = payload["feedback"]
#         current_approach = payload["current_approach"]

#         st.markdown("### 🔄 Approach Needs Rethinking")
#         st.markdown("---")

#         st.warning("Your approach has a conceptual issue. Read the feedback and revise it.")

#         st.markdown("#### 💬 Coach Feedback")
#         st.markdown(
#             f'<div class="analysis-box">{feedback.replace(chr(10), "<br>")}</div>',
#             unsafe_allow_html=True,
#         )

#         with st.expander("Your previous approach (for reference)"):
#             st.text(current_approach)

#         st.markdown("---")
#         st.markdown("#### ✏️ Revise Your Approach")
#         st.info(
#             "Rewrite your approach based on the hint above. "
#             "The code will be regenerated from your revised description."
#         )

#         revised = st.text_area(
#             "Revised approach:",
#             height=180,
#             placeholder="Describe your updated approach here…",
#         )

#         if st.button(
#             "⚡ Regenerate Code from Revised Approach",
#             disabled=not revised.strip(),
#             type="primary",
#             use_container_width=True,
#         ):
#             with st.spinner("Generating revised code…"):
#                 result = app.invoke(Command(resume=revised.strip()), config=config)
#             st.session_state["graph_result"] = result
#             st.rerun()

#     # ── INTERRUPT: Session Summary ────────────────────────────────────────────
#     elif itype == "session_summary":
#         summary = payload["summary"]
#         st.markdown("## 🎉 Session Complete!")
#         st.markdown("---")

#         col1, col2, col3 = st.columns(3)
#         with col1:
#             st.metric("Total Questions", summary["total_questions"])
#         with col2:
#             st.metric("Solved", summary["solved"])
#         with col3:
#             pct = int(summary["solved"] / max(summary["total_questions"], 1) * 100)
#             st.metric("Success Rate", f"{pct}%")

#         st.markdown(f"**{summary['message']}**")
#         st.markdown(f"Topics: {', '.join(summary['topics_practiced'])}")
#         st.markdown(f"Language: {'C++' if summary['language'] == 'cpp' else 'Python'}")

#         st.markdown("---")
#         st.markdown("#### 📋 Question-by-Question Breakdown")

#         for h in summary["questions"]:
#             outcome_color = "✅" if "Solved" in h.get("outcome", "") else "🔄"
#             with st.expander(
#                 f"{outcome_color} Q{h['question_number']}: {h['title']} "
#                 f"({h['difficulty']}) — {h['attempts']} attempt(s)"
#             ):
#                 st.caption(f"**Tags:** {', '.join(h.get('tags', []))}")
#                 st.markdown("**Your approach:**")
#                 st.text(h.get("approach", ""))

#         st.markdown("---")
#         if st.button("🚀 Start New Session", type="primary", use_container_width=True):
#             st.session_state["phase"] = "setup"
#             st.session_state["graph_result"] = None
#             st.session_state["show_error_input"] = False
#             st.rerun()

#     # ── Fallback: graph completed (END reached) ────────────────────────────────
#     elif itype == "none":
#         st.session_state["phase"] = "done"
#         st.rerun()

# elif st.session_state["phase"] == "done":
#     st.success("Session finished! Start a new one from the sidebar.")
#     if st.button("🚀 New Session", type="primary"):
#         st.session_state["phase"] = "setup"
#         st.session_state["graph_result"] = None
#         st.rerun()


























































import uuid
import time
import streamlit as st
from langgraph.types import Command

from graph import build_graph
from dataset import load_dataset, get_all_tags, fuzzy_match_tags, reset_seen_ids


# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DSA Coach — AI Prep Assistant",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.question-card {
    background: #1e1e2e;
    border: 1px solid #313244;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.badge-easy   { background:#1a4d1a; color:#86efac; padding:3px 12px;
                border-radius:999px; font-size:0.8rem; font-weight:600; }
.badge-medium { background:#4a3010; color:#fcd34d; padding:3px 12px;
                border-radius:999px; font-size:0.8rem; font-weight:600; }
.badge-hard   { background:#4a1010; color:#fca5a5; padding:3px 12px;
                border-radius:999px; font-size:0.8rem; font-weight:600; }
.tag-pill     { background:#2d2d3f; color:#a5b4fc; padding:2px 10px;
                border-radius:999px; font-size:0.75rem; margin:2px;
                display:inline-block; }
.code-header  { background:#313244; border-radius:8px 8px 0 0;
                padding:6px 14px; font-size:0.8rem; color:#cdd6f4;
                font-family:monospace; }
.analysis-box { background:#1e1e2e; border-left:4px solid #f38ba8;
                border-radius:0 8px 8px 0; padding:1rem; margin:0.5rem 0; }
.success-box  { background:#1a4d1a; border-left:4px solid #a6e3a1;
                border-radius:0 8px 8px 0; padding:1rem; }
</style>
""", unsafe_allow_html=True)


# ── Graph — compiled once per server session ──────────────────────────────────
@st.cache_resource
def get_graph():
    return build_graph()

app = get_graph()


# ── Session state bootstrap ───────────────────────────────────────────────────
def _init():
    defaults = {
        "thread_id":       None,
        "graph_result":    None,
        "phase":           "setup",
        "config":          None,
        "show_error_input": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_interrupt(result):
    """Extract interrupt payload from graph result. Returns None if no interrupt."""
    if result is None:
        return None
    interrupts = result.get("__interrupt__", [])
    if interrupts:
        return interrupts[0].value
    return None


def _classify(payload) -> str:
    """
    Classify the interrupt payload by its unique key set.
    Ordered from most-specific to least-specific to avoid false matches.
    """
    if payload is None:
        return "none"
    if "summary" in payload:
        return "session_summary"
    if "question_number" in payload:
        return "question_display"
    if "feedback" in payload and "current_approach" in payload:
        return "approach_wrong"
    if "analysis" in payload and "generated_code" in payload:
        return "code_analyser"
    if "generated_code" in payload:
        return "leetcode_hitl"
    if "prompt" in payload:
        return "user_approach"
    return "unknown"


def _badge(diff: str) -> str:
    cls = {"Easy": "easy", "Medium": "medium", "Hard": "hard"}.get(diff, "easy")
    return f'<span class="badge-{cls}">{diff}</span>'


def _pills(tags: list) -> str:
    return " ".join(f'<span class="tag-pill">{t}</span>' for t in tags)


def _rerun_clean():
    """Reset transient UI flags then rerun."""
    st.session_state["show_error_input"] = False
    st.rerun()


# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("🧠 DSA Coach")
    st.caption("LangGraph · LangChain · Groq (free)")
    st.divider()

    if st.session_state["phase"] == "setup":
        st.subheader("Session Setup")

        # Load tags for live preview
        try:
            _problems = load_dataset()
            _all_tags = get_all_tags(_problems)
        except FileNotFoundError:
            _problems, _all_tags = [], []

        topic_input = st.text_input(
            "📚 Topics (comma-separated)",
            placeholder="e.g. Array, Dynamic Programming, Graph",
            help="Fuzzy matching: 'dp' → 'Dynamic Programming', 'bfs' → 'Breadth-First Search'",
        )

        if topic_input and _all_tags:
            matched = fuzzy_match_tags(topic_input, _all_tags)
            if matched:
                st.caption(f"✅ Matched: **{', '.join(matched)}**")
            else:
                st.caption("⚠️ No tags matched. Try: Array, DP, Graph, Tree, String…")

        language = st.radio(
            "💻 Language",
            options=["cpp", "python"],
            format_func=lambda x: "C++" if x == "cpp" else "Python",
            index=0,
        )

        st.subheader("Difficulty Mix (total = 5)")
        c1, c2, c3 = st.columns(3)
        with c1: n_easy   = st.number_input("Easy",   min_value=0, max_value=5, value=2)
        with c2: n_medium = st.number_input("Medium", min_value=0, max_value=5, value=2)
        with c3: n_hard   = st.number_input("Hard",   min_value=0, max_value=5, value=1)

        st.divider()

        start = st.button(
            "🚀 Start Today's Session",
            disabled=not topic_input.strip(),
            use_container_width=True,
            type="primary",
        )

        if start and topic_input.strip():
            thread_id = str(uuid.uuid4())
            config    = {"configurable": {"thread_id": thread_id}}

            initial_state = {
                "topic_input":           topic_input.strip(),
                "language":              language,
                "difficulty_distribution": {
                    "Easy":   int(n_easy),
                    "Medium": int(n_medium),
                    "Hard":   int(n_hard),
                },
                "daily_questions":       [],
                "question_index":        0,
                "current_question":      {},
                "user_approach":         "",
                "generated_code":        "",
                "leetcode_result":       "",
                "user_error_paste":      "",
                "approach_feedback":     "",
                "approach_verdict":      "",
                "analysis":              "",
                "fix_choice":            "",
                "revised_approach":      "",
                "session_history":       [],
                "skipped_questions":     [],
                "attempt":               0,
                "next_action":           "",
                "topics":                [],
            }

            with st.spinner("Loading dataset and picking questions…"):
                result = app.invoke(initial_state, config=config)

            st.session_state.update({
                "thread_id":        thread_id,
                "config":           config,
                "graph_result":     result,
                "phase":            "running",
                "show_error_input": False,
            })
            st.rerun()

        st.divider()
        if st.button("🔄 Reset Seen Questions", use_container_width=True):
            reset_seen_ids()
            st.success("Seen questions cleared! Next session will have fresh problems.")

    else:
        # Running session sidebar
        st.subheader("Current Session")
        result = st.session_state.get("graph_result") or {}
        qi     = result.get("question_index", 0)
        total  = len(result.get("daily_questions", []))
        topics = result.get("topics", [])
        lang   = result.get("language", "cpp")

        st.metric("Progress", f"{qi} / {total}")
        if topics:
            st.caption(f"**Topics:** {', '.join(topics)}")
        st.caption(f"**Language:** {'C++' if lang == 'cpp' else 'Python'}")

        st.divider()
        history = result.get("session_history", [])
        if history:
            st.subheader("Completed")
            for h in history:
                icon = "✅" if "Solved" in h.get("outcome", "") else "❌"
                st.caption(f"{icon} Q{h['question_number']}: {h['title']} ({h['difficulty']})")

        st.divider()
        if st.button("🏁 End Session", use_container_width=True):
            st.session_state["phase"]        = "setup"
            st.session_state["graph_result"] = None
            st.session_state["show_error_input"] = False
            st.rerun()


# ════════════════════════════════════════════════════════════════
# MAIN AREA
# ════════════════════════════════════════════════════════════════

# ── Landing page ──────────────────────────────────────────────
if st.session_state["phase"] == "setup":
    st.title("🧠 DSA Coach — AI-Powered Interview Preparation")
    st.markdown("""
    Your personal DSA preparation assistant powered by **LangGraph + LangChain + Groq**.

    ### How it works
    1. **Pick topics** in the sidebar — Array, DP, Graph, Tree, String, and 60+ more
    2. **Choose your language** — C++ or Python
    3. **Get 5 curated problems** daily from 2,641 real LeetCode problems (never repeats)
    4. **Describe your approach** in plain English — AI generates code from YOUR logic only
    5. **Test on LeetCode** — copy the generated code and paste it yourself
    6. **Report back** — success → next question; failure → paste the error for analysis
    7. **Choose** to fix it yourself or let the AI auto-fix within your approach

    ---
    👈 **Configure your session in the sidebar and click Start!**
    """)

# ── Running session ────────────────────────────────────────────
elif st.session_state["phase"] == "running":
    result  = st.session_state["graph_result"]
    config  = st.session_state["config"]
    payload = _get_interrupt(result)
    itype   = _classify(payload)

    # ── QUESTION DISPLAY ──────────────────────────────────────
    if itype == "question_display":
        q_num = payload["question_number"]
        total = payload["total"]
        title = payload["title"]
        diff  = payload["difficulty"]
        tags  = payload["tags"]
        desc  = payload["problem_description"]
        sc    = payload.get("starter_code", "")
        lang  = payload["language"]

        st.progress(q_num / total, text=f"Question {q_num} of {total}")
        st.markdown("---")

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                f"### #{payload.get('question_id', '')} — {title} &nbsp;{_badge(diff)}",
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown(_pills(tags), unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### 📋 Problem Description")
        st.markdown(
            f'<div class="question-card">{desc.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )

        if sc:
            note = " (Python reference — you'll write C++ on LeetCode)" if lang == "cpp" else ""
            st.markdown(f"#### 🔧 Starter Code{note}")
            st.code(sc, language="python")

        st.markdown("---")
        st.info("✅ Read the problem carefully, then click below to describe your approach.")

        if st.button("📝 I'm Ready — Describe My Approach →", type="primary", use_container_width=True):
            with st.spinner("Loading approach input…"):
                # Resume value is ignored by question_display_node but must be sent
                result = app.invoke(Command(resume=True), config=config)
            st.session_state["graph_result"] = result
            st.rerun()

    # ── USER APPROACH INPUT ───────────────────────────────────
    elif itype == "user_approach":
        # Read current question context from the graph state
        cq   = result.get("current_question", {})
        lang = result.get("language", "cpp")

        st.markdown("### 💭 Describe Your Approach")
        st.caption(
            f"**{cq.get('task_id', '').replace('-', ' ').title()}** · "
            f"{cq.get('difficulty', '')} · "
            f"{', '.join(cq.get('tags', []))}"
        )
        st.markdown("---")
        st.info(
            "Describe your approach in plain English.\n\n"
            f"The AI will generate **{'C++' if lang == 'cpp' else 'Python'}** code "
            "based **ONLY** on what you describe — nothing more, nothing less."
        )

        approach_text = st.text_area(
            "Your approach:",
            height=200,
            placeholder=(
                "Example:\n"
                "I'll use a hash map to store each number and its index as I iterate.\n"
                "For each number, check if target - current_number exists in the map.\n"
                "If yes, return both indices. If no, add the number to the map."
            ),
        )

        col1, col2 = st.columns(2)
        with col1:
            generate = st.button(
                "⚡ Generate Code from My Approach",
                disabled=not approach_text.strip(),
                type="primary",
                use_container_width=True,
            )
        with col2:
            skip = st.button("⏭️ Skip This Question", use_container_width=True)

        if generate and approach_text.strip():
            with st.spinner("Generating code…"):
                result = app.invoke(Command(resume=approach_text.strip()), config=config)
            st.session_state["graph_result"] = result
            st.rerun()

        if skip:
            with st.spinner("Skipping question…"):
                result = app.invoke(Command(resume="__SKIP__"), config=config)
            st.session_state["graph_result"] = result
            _rerun_clean()

    # ── LEETCODE HITL (show code + await result) ──────────────
    elif itype == "leetcode_hitl":
        lang       = payload.get("language", "cpp")
        code       = payload["generated_code"]
        lang_label = "cpp" if lang == "cpp" else "python"
        cq         = result.get("current_question", {})
        attempt    = result.get("attempt", 0)

        st.markdown("### ⚡ Generated Code")
        if attempt > 0:
            st.warning(f"🔄 Attempt {attempt + 1} — revised code based on previous analysis")

        st.caption(
            f"**{cq.get('task_id', '').replace('-', ' ').title()}** · "
            f"Language: {'C++' if lang == 'cpp' else 'Python'}"
        )
        st.markdown(
            f'<div class="code-header">{"C++" if lang == "cpp" else "Python"} · '
            f'{cq.get("task_id", "").replace("-", " ").title()}</div>',
            unsafe_allow_html=True,
        )
        st.code(code, language=lang_label)

        st.info(
            "📋 **Next steps:**\n\n"
            "1. Copy the code above  \n"
            "2. Go to LeetCode → find the problem → paste into the code editor  \n"
            "3. Set language to **C++** (or Python) if needed  \n"
            "4. Click **Run** or **Submit**  \n"
            "5. Come back here and report the result"
        )

        st.markdown("---")
        st.markdown("#### 📊 What happened on LeetCode?")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ It Passed! Next Question →", type="primary", use_container_width=True):
                with st.spinner("Recording success…"):
                    result = app.invoke(
                        Command(resume={"result": "success", "error": ""}),
                        config=config,
                    )
                st.session_state["graph_result"] = result
                st.balloons()
                time.sleep(0.4)
                _rerun_clean()

        with col2:
            if st.button("❌ It Failed — Analyse", use_container_width=True):
                st.session_state["show_error_input"] = True
                st.rerun()

        if st.session_state.get("show_error_input", False):
            st.markdown("---")
            st.markdown("#### 🔍 Paste LeetCode Output")
            st.caption("Paste the full error, wrong answer, or TLE message from LeetCode.")
            error_paste = st.text_area(
                "LeetCode output:",
                height=150,
                placeholder=(
                    "Wrong Answer\n"
                    "Input: nums = [2,7,11,15], target = 9\n"
                    "Output: []\n"
                    "Expected: [0,1]\n\n"
                    "or\n\nRuntime Error: ...\nor\nTime Limit Exceeded"
                ),
            )
            if st.button(
                "🔬 Analyse the Failure →",
                disabled=not error_paste.strip(),
                type="primary",
                use_container_width=True,
            ):
                with st.spinner("Analysing your code and approach…"):
                    result = app.invoke(
                        Command(resume={"result": "failure", "error": error_paste.strip()}),
                        config=config,
                    )
                st.session_state["graph_result"] = result
                _rerun_clean()

    # ── CODE ANALYSER (show analysis + fix choice) ────────────
    elif itype == "code_analyser":
        approach_feedback = payload.get("approach_feedback", "")
        approach_verdict  = payload.get("approach_verdict", "approach_ok")
        analysis          = payload["analysis"]
        code              = payload.get("generated_code", "")
        lang              = payload.get("language", "cpp")
        lang_label        = "cpp" if lang == "cpp" else "python"

        st.markdown("### 🔬 Code Analysis")
        st.markdown("---")

        # Approach verdict box — colour-coded by verdict
        if approach_feedback:
            st.markdown("#### 🧠 Approach Verdict")
            box_class = "analysis-box" if approach_verdict == "approach_wrong" else "success-box"
            st.markdown(
                f'<div class="{box_class}">{approach_feedback.replace(chr(10), "<br>")}</div>',
                unsafe_allow_html=True,
            )
            st.markdown("")

        st.markdown("#### 🔍 Detailed Code Analysis")
        st.markdown(
            f'<div class="analysis-box">{analysis.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )

        with st.expander("📄 View the failing code"):
            st.code(code, language=lang_label)

        st.markdown("---")
        st.markdown("#### What would you like to do?")

        # Show 2 or 3 columns depending on whether approach is wrong
        if approach_verdict == "approach_wrong":
            col1, col2, col3 = st.columns(3)
        else:
            col1, col2 = st.columns(2)
            col3 = None

        with col1:
            st.markdown("**Option A — I'll fix it myself**")
            st.caption(
                "Go back to LeetCode, edit the code based on the analysis above, "
                "resubmit, then come back and report the result here."
            )
            if st.button("✏️ I'll Fix It Myself", use_container_width=True):
                with st.spinner("Heading back to result reporting…"):
                    result = app.invoke(Command(resume="self_edit"), config=config)
                st.session_state["graph_result"] = result
                _rerun_clean()

        with col2:
            st.markdown("**Option B — Auto-fix for me**")
            st.caption(
                "The AI will regenerate the code applying the fix described in the "
                "analysis above, staying within your original approach."
            )
            if st.button("🤖 Auto-Fix My Code", type="primary", use_container_width=True):
                with st.spinner("Regenerating with fix applied…"):
                    result = app.invoke(Command(resume="auto_fix"), config=config)
                st.session_state["graph_result"] = result
                _rerun_clean()

        # Option C — only shown when the approach itself is conceptually wrong
        if col3 is not None:
            with col3:
                st.markdown("**Option C — Revise my approach**")
                st.caption(
                    "Your approach has a conceptual flaw. "
                    "Rewrite your approach from scratch and the AI will regenerate the code."
                )
                if st.button("🔄 Revise My Approach", use_container_width=True):
                    with st.spinner("Loading approach revision screen…"):
                        result = app.invoke(Command(resume="revise_approach"), config=config)
                    st.session_state["graph_result"] = result
                    _rerun_clean()

    # ── APPROACH WRONG (show feedback + collect revision) ─────
    elif itype == "approach_wrong":
        feedback         = payload.get("feedback", "")
        current_approach = payload.get("current_approach", "")

        st.markdown("### 🔄 Approach Needs Rethinking")
        st.markdown("---")
        st.warning("Your approach has a conceptual issue. Read the feedback and revise it.")

        st.markdown("#### 💬 Coach Feedback")
        st.markdown(
            f'<div class="analysis-box">{feedback.replace(chr(10), "<br>")}</div>',
            unsafe_allow_html=True,
        )

        with st.expander("Your previous approach (for reference)"):
            st.text(current_approach)

        st.markdown("---")
        st.markdown("#### ✏️ Revise Your Approach")
        st.info("Rewrite your approach — the code will be regenerated from your new description.")

        revised = st.text_area(
            "Revised approach:",
            height=180,
            placeholder="Describe your updated approach here…",
        )

        if st.button(
            "⚡ Regenerate from Revised Approach",
            disabled=not revised.strip(),
            type="primary",
            use_container_width=True,
        ):
            with st.spinner("Generating revised code…"):
                result = app.invoke(Command(resume=revised.strip()), config=config)
            st.session_state["graph_result"] = result
            _rerun_clean()

    # ── SESSION SUMMARY ───────────────────────────────────────
    elif itype == "session_summary":
        summary   = payload["summary"]
        total_qs  = summary["total_questions"]
        solved    = summary["solved"]
        attempted = summary["attempted"]
        n_skipped = summary["skipped"]
        pct       = int(solved / max(total_qs, 1) * 100)

        st.markdown("## 🎉 Session Complete!")
        st.markdown("---")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total",         total_qs)
        c2.metric("✅ Solved",      solved)
        c3.metric("🔄 Attempted",   attempted)
        c4.metric("⏭️ Skipped",    n_skipped)

        st.markdown(f"**{summary['message']}**")
        st.caption(
            f"Topics: {', '.join(summary['topics_practiced'])}  |  "
            f"Language: {'C++' if summary['language'] == 'cpp' else 'Python'}"
        )

        st.markdown("---")

        # Attempted questions (solved or failed)
        if summary.get("attempted_questions"):
            st.markdown("#### 📋 Attempted Questions")
            for h in summary["attempted_questions"]:
                icon = "✅" if "Solved" in h.get("outcome", "") else "❌"
                with st.expander(
                    f"{icon} Q{h['question_number']}: {h['title']} "
                    f"({h['difficulty']}) — {h['attempts']} attempt(s)"
                ):
                    st.caption(f"**Tags:** {', '.join(h.get('tags', []))}")
                    st.markdown("**Your approach:**")
                    st.text(h.get("approach", ""))

        # Skipped questions shown separately
        if summary.get("skipped_questions"):
            st.markdown("#### ⏭️ Skipped Questions")
            for s in summary["skipped_questions"]:
                st.caption(
                    f"Q{s['question_number']}: **{s['title']}** "
                    f"({s['difficulty']})  —  "
                    f"Tags: {', '.join(s.get('tags', []))}"
                )

        st.markdown("---")
        if st.button("🚀 Start New Session", type="primary", use_container_width=True):
            st.session_state["phase"]            = "setup"
            st.session_state["graph_result"]     = None
            st.session_state["show_error_input"] = False
            st.rerun()

    # ── Graph reached END (no interrupt) ─────────────────────
    elif itype == "none":
        st.session_state["phase"] = "done"
        st.rerun()

    # ── Unknown interrupt (safety net) ───────────────────────
    else:
        st.error(f"Unexpected state: interrupt type = '{itype}'. Please restart.")
        if st.button("🔄 Restart"):
            st.session_state["phase"]        = "setup"
            st.session_state["graph_result"] = None
            st.rerun()

# ── Done state ─────────────────────────────────────────────────
elif st.session_state["phase"] == "done":
    st.success("Session finished! Start a new one from the sidebar.")
    if st.button("🚀 New Session", type="primary"):
        st.session_state["phase"]        = "setup"
        st.session_state["graph_result"] = None
        st.rerun()
