# """
# dataset.py
# Handles loading, filtering, and daily selection of LeetCode problems
# from the newfacade/LeetCodeDataset JSONL file.

# All dataset logic lives here — nodes import from this module.
# """

# import gzip
# import json
# import random
# import os
# from pathlib import Path
# from difflib import get_close_matches

# # ── Path to the data file ─────────────────────────────────────────────────────
# # Place LeetCodeDataset-v0.3.1-train.jsonl.gz in the same folder as this file.
# DATA_FILE = Path(__file__).parent / "LeetCodeDataset-v0.3.1-train.jsonl"

# # ── Seen-questions tracker ────────────────────────────────────────────────────
# # Prevents repeating the same problem across sessions.
# SEEN_FILE = Path(__file__).parent / "seen_ids.json"


# def load_dataset() -> list[dict]:
#     """Load and return all problems from the gzipped JSONL file."""
#     if not DATA_FILE.exists():
#         raise FileNotFoundError(
#             f"Dataset not found at {DATA_FILE}.\n"
#             "Download LeetCodeDataset-v0.3.1-train.jsonl.gz from:\n"
#             "https://github.com/newfacade/LeetCodeDataset/tree/main/data\n"
#             "and place it next to dataset.py"
#         )
#     # problems = []
#     # with gzip.open(DATA_FILE, "rt", encoding="utf-8") as f:
#     #     for line in f:
#     #         line = line.strip()
#     #         if line:
#     #             problems.append(json.loads(line))
#     problems = []

#     with open(DATA_FILE, "r", encoding="utf-8") as f:
#         for line in f:
#             line = line.strip()
#             if line:
#                 problems.append(json.loads(line))
#     return problems


# def load_seen_ids() -> set:
#     """Return the set of task_ids already seen in previous sessions."""
#     if SEEN_FILE.exists():
#         with open(SEEN_FILE, "r") as f:
#             return set(json.load(f))
#     return set()


# def save_seen_ids(seen: set) -> None:
#     """Persist seen task_ids to disk."""
#     with open(SEEN_FILE, "w") as f:
#         json.dump(list(seen), f)


# def get_all_tags(problems: list[dict]) -> list[str]:
#     """Return sorted list of all unique tag strings in the dataset."""
#     tags = set()
#     for p in problems:
#         tags.update(p.get("tags", []))
#     return sorted(tags)


# def fuzzy_match_tags(user_input: str, all_tags: list[str]) -> list[str]:
#     """
#     Takes the user's raw comma-separated topic input and maps each token
#     to the closest official tag in the dataset using fuzzy matching.

#     Example:
#         user_input = "dp, arrays, bfs"
#         → ["Dynamic Programming", "Array", "Breadth-First Search"]
#     """
#     tokens = [t.strip() for t in user_input.split(",") if t.strip()]
#     matched = []
#     for token in tokens:
#         # Try exact case-insensitive match first
#         lower_tags = {t.lower(): t for t in all_tags}
#         if token.lower() in lower_tags:
#             matched.append(lower_tags[token.lower()])
#             continue
#         # Fall back to fuzzy matching
#         close = get_close_matches(token.lower(), lower_tags.keys(), n=1, cutoff=0.5)
#         if close:
#             matched.append(lower_tags[close[0]])
#     return list(dict.fromkeys(matched))  # deduplicate preserving order


# def pick_daily_questions(
#     topics: list[str],
#     distribution: dict = None,
#     problems: list[dict] = None,
# ) -> tuple[list[dict], list[str]]:
#     """
#     Select 5 problems for today's session.

#     Args:
#         topics: list of official tag strings to filter by
#         distribution: difficulty counts, default {"Easy": 2, "Medium": 2, "Hard": 1}
#         problems: pre-loaded dataset (loaded fresh if None)

#     Returns:
#         (selected_problems, warnings)
#         warnings: list of strings if fewer problems found than requested
#     """
#     if distribution is None:
#         distribution = {"Easy": 2, "Medium": 2, "Hard": 1}

#     if problems is None:
#         problems = load_dataset()

#     seen = load_seen_ids()

#     # Filter to problems matching ANY of the requested topics
#     def matches_topic(problem: dict) -> bool:
#         problem_tags = [t.lower() for t in problem.get("tags", [])]
#         return any(topic.lower() in problem_tags for topic in topics)

#     filtered = [p for p in problems if matches_topic(p)]

#     # Prefer unseen; if not enough unseen fall back to seen
#     unseen = [p for p in filtered if p["task_id"] not in seen]
#     seen_pool = [p for p in filtered if p["task_id"] in seen]

#     selected = []
#     warnings = []

#     for difficulty, count in distribution.items():
#         pool = [p for p in unseen if p["difficulty"] == difficulty]
#         if len(pool) < count:
#             # Not enough unseen — top up from seen pool
#             pool += [p for p in seen_pool if p["difficulty"] == difficulty]
#             if len(pool) < count:
#                 warnings.append(
#                     f"Only {len(pool)} {difficulty} problems found for topics {topics}. "
#                     f"Requested {count}."
#                 )
#         chosen = random.sample(pool, min(count, len(pool)))
#         selected.extend(chosen)

#     # Shuffle so Easy/Medium/Hard are not always in the same order
#     random.shuffle(selected)

#     # Mark newly selected as seen
#     new_seen = seen | {p["task_id"] for p in selected}
#     save_seen_ids(new_seen)

#     return selected, warnings


# def reset_seen_ids() -> None:
#     """Clear the seen history — call this when all problems have been exhausted."""
#     if SEEN_FILE.exists():
#         os.remove(SEEN_FILE)































import gzip
import json
import random
import os
from pathlib import Path
from difflib import get_close_matches
from typing import List, Dict, Tuple, Optional

# ── Locate the data file — accept both zipped and plain ──────────────────────
_DIR = Path(__file__).parent
_PLAIN  = _DIR / "LeetCodeDataset-v0.3.1-train.jsonl"
_ZIPPED = _DIR / "LeetCodeDataset-v0.3.1-train.jsonl.gz"

# ── Seen-questions tracker ────────────────────────────────────────────────────
SEEN_FILE = _DIR / "seen_ids.json"


def load_dataset() -> List[Dict]:
    """
    Load and return all problems from the JSONL file.
    Accepts both plain .jsonl and gzipped .jsonl.gz automatically.
    """
    if _PLAIN.exists():
        data_file = _PLAIN
        opener = open
        kwargs: dict = {"encoding": "utf-8"}
    elif _ZIPPED.exists():
        data_file = _ZIPPED
        opener = gzip.open          # type: ignore[assignment]
        kwargs = {"mode": "rt", "encoding": "utf-8"}
    else:
        raise FileNotFoundError(
            f"Dataset not found. Expected one of:\n"
            f"  {_PLAIN}\n"
            f"  {_ZIPPED}\n\n"
            "Download from:\n"
            "  https://github.com/newfacade/LeetCodeDataset/tree/main/data\n"
            "and place it in the same folder as dataset.py."
        )

    problems: List[Dict] = []
    with opener(data_file, **kwargs) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    problems.append(json.loads(line))
                except json.JSONDecodeError:
                    continue  # skip malformed lines silently
    return problems


def load_seen_ids() -> set:
    """Return the set of task_ids already seen in previous sessions."""
    if SEEN_FILE.exists():
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except (json.JSONDecodeError, ValueError):
            return set()
    return set()


def save_seen_ids(seen: set) -> None:
    """Persist seen task_ids to disk."""
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f)


def get_all_tags(problems: List[Dict]) -> List[str]:
    """Return sorted list of all unique tag strings in the dataset."""
    tags: set = set()
    for p in problems:
        tags.update(p.get("tags", []))
    return sorted(tags)


def fuzzy_match_tags(user_input: str, all_tags: List[str]) -> List[str]:
    """
    Maps comma-separated user input to the closest official dataset tags.

    Strategy:
      1. Exact case-insensitive match
      2. Substring match (e.g. "dp" matches "Dynamic Programming")
      3. difflib fuzzy match (cutoff=0.5)

    Returns deduplicated list preserving input order.
    """
    tokens = [t.strip() for t in user_input.split(",") if t.strip()]
    lower_to_official: Dict[str, str] = {t.lower(): t for t in all_tags}
    matched: List[str] = []

    for token in tokens:
        token_lower = token.lower()

        # 1. Exact match
        if token_lower in lower_to_official:
            matched.append(lower_to_official[token_lower])
            continue

        # 2. Substring match — e.g. "dp" → "Dynamic Programming"
        substring_hits = [
            official for lower, official in lower_to_official.items()
            if token_lower in lower or lower in token_lower
        ]
        if substring_hits:
            matched.append(substring_hits[0])
            continue

        # 3. Fuzzy match
        close = get_close_matches(token_lower, list(lower_to_official.keys()), n=1, cutoff=0.5)
        if close:
            matched.append(lower_to_official[close[0]])

    # Deduplicate preserving order
    seen_set: set = set()
    result: List[str] = []
    for tag in matched:
        if tag not in seen_set:
            seen_set.add(tag)
            result.append(tag)
    return result


def pick_daily_questions(
    topics: List[str],
    distribution: Optional[Dict[str, int]] = None,
    problems: Optional[List[Dict]] = None,
) -> Tuple[List[Dict], List[str]]:
    """
    Select problems for today's session.

    Args:
        topics:       List of official tag strings to filter by.
        distribution: {difficulty: count}. Default: {"Easy": 2, "Medium": 2, "Hard": 1}.
        problems:     Pre-loaded dataset. Loaded fresh if None.

    Returns:
        (selected_problems, warnings)
    """
    if distribution is None:
        distribution = {"Easy": 2, "Medium": 2, "Hard": 1}

    if problems is None:
        problems = load_dataset()

    seen = load_seen_ids()

    # Filter to problems matching ANY requested topic
    topic_lowers = [t.lower() for t in topics]

    def matches_topic(problem: Dict) -> bool:
        problem_tags_lower = [tag.lower() for tag in problem.get("tags", [])]
        return any(topic in problem_tags_lower for topic in topic_lowers)

    filtered = [p for p in problems if matches_topic(p)]

    unseen   = [p for p in filtered if p["task_id"] not in seen]
    seen_pool = [p for p in filtered if p["task_id"] in seen]

    selected: List[Dict] = []
    warnings: List[str] = []

    for difficulty, count in distribution.items():
        # Build pool: prefer unseen, fall back to seen if needed
        pool = [p for p in unseen if p["difficulty"] == difficulty]
        if len(pool) < count:
            pool += [p for p in seen_pool if p["difficulty"] == difficulty]
        if len(pool) < count:
            warnings.append(
                f"Only {len(pool)} {difficulty} problem(s) found for "
                f"topics {topics}. Requested {count}."
            )
        if pool:
            chosen = random.sample(pool, min(count, len(pool)))
            selected.extend(chosen)

    # Shuffle so difficulty order is unpredictable
    random.shuffle(selected)

    # Mark selected questions as seen
    new_seen = seen | {p["task_id"] for p in selected}
    save_seen_ids(new_seen)

    return selected, warnings


def reset_seen_ids() -> None:
    """Clear the seen-questions history."""
    if SEEN_FILE.exists():
        os.remove(SEEN_FILE)
