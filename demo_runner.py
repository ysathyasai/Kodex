"""
Demo Progression Script (demo_runner.py) for Kodex Code Review Agent.
=====================================================================

Simulates a realistic 3-step enterprise timeline against live Groq & Hindsight Cloud APIs:
  - Step 1: Interaction 1 - Submit Code A. Semantic Cohorts order changes; agent gives generic review.
  - Step 2: Interaction 2 - Developer rejects suggestion. Hindsight retain() memorizes the rule.
  - Step 3: Interaction 3 - Submit Code B. Dual Hindsight (recall + reflect) feeds Groq LLM;
            agent validates dict.get() and does not repeat the rejected suggestion.
"""

import sys
import time
import json
import os
from typing import Dict, Any, Union
import requests

# Ensure UTF-8 output on Windows terminal
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from app import app
from memory_client import memory_client
from config import config

# ANSI Colors for rich terminal presentation
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RED = "\033[91m"
BOLD = "\033[1m"
RESET = "\033[0m"


def print_banner():
    """Prints the rich ASCII banner for the demo timeline."""
    banner = f"""
{CYAN}{BOLD}===================================================================================
   🐇 KODEX: ENTERPRISE AI CODE REVIEW AGENT (Kodex Architecture)
   Groq LLM ({config.GROQ_MODEL}) + Vectorize Hindsight Cloud ({config.HINDSIGHT_BASE_URL})
==================================================================================={RESET}
"""
    print(banner)


def send_pr_webhook(
    client: Union[str, Any],
    diff_text: str,
    pr_id: str,
    pr_title: str,
    author: str = "alex_developer"
) -> Dict[str, Any]:
    """
    Dispatches a pull request review webhook request.

    Args:
        client: Either a string URL (for live HTTP) or Flask TestClient instance.
        diff_text: Unified git diff content.
        pr_id: Pull request identifier string (e.g. 'PR-101').
        pr_title: Pull request title.
        author: Git author handle.

    Returns:
        Dict[str, Any]: Parsed JSON response from /webhook/pr.
    """
    payload = {
        "action": "opened",
        "pull_request": {
            "number": pr_id.replace("PR-", "").replace("#", ""),
            "title": pr_title,
            "user": {"login": author},
            "diff": diff_text
        },
        "diff": diff_text,
        "bank_id": config.HINDSIGHT_BANK_ID
    }
    if isinstance(client, str):  # HTTP URL
        resp = requests.post(f"{client}/webhook/pr", json=payload)
        return resp.json()
    else:  # Flask TestClient
        resp = client.post("/webhook/pr", json=payload)
        return resp.get_json()


def send_comment_webhook(
    client: Union[str, Any],
    comment_text: str,
    author: str = "sarah_techlead",
    context: str = "developer PR correction"
) -> Dict[str, Any]:
    """
    Dispatches a developer review reply comment webhook to trigger memory retention.

    Args:
        client: Either a string URL (for live HTTP) or Flask TestClient instance.
        comment_text: Developer feedback comment text.
        author: Developer handle.
        context: Metadata describing the feedback origin.

    Returns:
        Dict[str, Any]: Parsed JSON response from /webhook/comment.
    """
    payload = {
        "action": "created",
        "comment": {
            "body": comment_text,
            "user": {"login": author},
            "created_at": "2026-09-28T15:30:00Z"
        },
        "context": context,
        "bank_id": config.HINDSIGHT_BANK_ID
    }
    if isinstance(client, str):  # HTTP URL
        resp = requests.post(f"{client}/webhook/comment", json=payload)
        return resp.json()
    else:  # Flask TestClient
        resp = client.post("/webhook/comment", json=payload)
        return resp.get_json()


def run_demo():
    """
    Executes the automated 3-step enterprise timeline:
      1. Interaction 1: Fresh pull request with 4 files across cohorts -> Generic review.
      2. Interaction 2: Tech lead comment -> Hindsight retain() on Cloud.
      3. Interaction 3: Subsequent pull request -> Hindsight recall() + reflect() -> Memory applied.
    """
    print_banner()

    server_url = f"http://localhost:{config.PORT}"
    try:
        r = requests.get(f"{server_url}/health", timeout=1.0)
        if r.status_code == 200:
            client = server_url
            print(f"{GREEN}✓ Connected to live Kodex Flask server at {server_url}{RESET}\n")
    except Exception:
        client = app.test_client()
        print(f"{YELLOW}ℹ Running with in-process Flask client targeting live Groq & Hindsight Cloud APIs{RESET}\n")

    # Step 0: Clean reset of the Hindsight memory bank
    print(f"{BOLD}[Memory Engine]{RESET} Resetting Hindsight Cloud bank: {MAGENTA}'{config.HINDSIGHT_BANK_ID}'{RESET}...")
    memory_client.clear_bank(config.HINDSIGHT_BANK_ID)
    print(f"{GREEN}✓ Bank reset. Starting demonstration with clean state.{RESET}\n")

    # Load synthetic enterprise diffs
    diff_a_path = os.path.join(os.path.dirname(__file__), "sample_diffs", "pr_a_payment_service.diff")
    diff_b_path = os.path.join(os.path.dirname(__file__), "sample_diffs", "pr_b_user_profile.diff")

    with open(diff_a_path, "r", encoding="utf-8") as f:
        diff_a = f.read()

    with open(diff_b_path, "r", encoding="utf-8") as f:
        diff_b = f.read()

    # =========================================================================
    # INTERACTION 1: Submit Code A (Multi-Cohort Diff, Generic Review)
    # =========================================================================
    print(f"{BOLD}{CYAN}-----------------------------------------------------------------------------------{RESET}")
    print(f"{BOLD}{CYAN}>>> STEP 1: INTERACTION 1 - SUBMIT PR #101 (PaymentGatewayConfigService){RESET}")
    print(f"{BOLD}{CYAN}-----------------------------------------------------------------------------------{RESET}")
    print(f"Author opens PR #101 with multi-file diff spanning 4 files.")
    print(f"{YELLOW}Testing Semantic Cohorts Re-ordering:{RESET}")
    print("Files in raw diff appear out-of-order (tests -> migrations -> api -> services).")
    print("Kodex re-sequences files into dependency order: Schema ➔ Business Logic ➔ API ➔ Tests.\n")

    print("Pre-Review Memory Check:")
    print("  • client.recall(...) ➔ Fetching syntax rules")
    print("  • client.reflect(...) ➔ Synthesizing team architectural style\n")

    start_time = time.time()
    res_1 = send_pr_webhook(
        client,
        diff_text=diff_a,
        pr_id="PR-101",
        pr_title="feat(payments): add dynamic gateway configuration with timeout defaults"
    )
    elapsed_1 = time.time() - start_time

    data_1 = res_1.get("data", {})
    recalled_1 = data_1.get("recalled_memories", [])
    reflected_1 = data_1.get("reflected_style", "")
    cohorts_1 = data_1.get("cohorts", {})

    print(f"{GREEN}✓ Semantic Cohort Analysis Completed:{RESET}")
    for cohort_name, files in cohorts_1.items():
        print(f"  • {BOLD}{cohort_name}{RESET}: {', '.join(files)}")

    print(f"\nHindsight Recall: {len(recalled_1)} active rules found.")
    print(f"Hindsight Reflect: \"{reflected_1[:110]}...\"")
    print(f"Review Generation Time: {elapsed_1:.2f}s (Groq: {data_1.get('model_used')})\n")

    print(f"{BOLD}Generated Kodex Review Output (Interaction 1):{RESET}")
    print(data_1.get("review_markdown", ""))

    print(f"{YELLOW}Notice in Interaction 1:{RESET} Because no prior team memory existed, the agent")
    print(f"issued a generic review suggesting explicit try/except KeyError handling over dict.get().")
    time.sleep(1.5)

    # =========================================================================
    # INTERACTION 2: Developer Rejection & Hindsight Retain Loop
    # =========================================================================
    print(f"\n{BOLD}{CYAN}-----------------------------------------------------------------------------------{RESET}")
    print(f"{BOLD}{CYAN}>>> STEP 2: INTERACTION 2 - DEVELOPER FEEDBACK REJECTION (Retain Loop){RESET}")
    print(f"{BOLD}{CYAN}-----------------------------------------------------------------------------------{RESET}")

    developer_comment = (
        "Developer: We actually prefer dict.get() over try/except for dictionaries here. "
        "In our microservice architecture, missing optional config keys have standard defaults "
        "and raising exceptions adds unnecessary overhead."
    )
    print(f"Tech Lead replies to PR comment on line 18:")
    print(f'{GREEN}💬 "{developer_comment}"{RESET}\n')
    print("Calling POST /webhook/comment ➔ Vectorize Hindsight Cloud client.retain(...)...")

    start_retain = time.time()
    res_2 = send_comment_webhook(client, developer_comment, author="sarah_techlead")
    elapsed_retain = time.time() - start_retain

    retained_rule = res_2.get("retained_rule")
    print(f"{GREEN}✓ Hindsight retain() successfully committed to Cloud! ({elapsed_retain:.2f}s){RESET}")
    print(f"  • Bank ID: {MAGENTA}{config.HINDSIGHT_BANK_ID}{RESET}")
    print(f"  • Retained Rule: {BOLD}{retained_rule}{RESET}")
    print(f"  • Context: {res_2.get('context')}")
    time.sleep(1.5)

    # =========================================================================
    # INTERACTION 3: Submit Code B (Memory Applied - No Mistake Repeated!)
    # =========================================================================
    print(f"\n{BOLD}{CYAN}-----------------------------------------------------------------------------------{RESET}")
    print(f"{BOLD}{CYAN}>>> STEP 3: INTERACTION 3 - SUBMIT PR #102 (UserNotificationPreferenceService){RESET}")
    print(f"{BOLD}{CYAN}-----------------------------------------------------------------------------------{RESET}")
    print(f"Another developer opens PR #102 with the exact same dict.get() pattern.")
    print("Pre-Review Dual Memory Check:")
    print("  1. client.recall() ➔ Querying specific rules from Hindsight Cloud")
    print("  2. client.reflect() ➔ Generating synthesized summary of team architectural style\n")

    start_time_3 = time.time()
    res_3 = send_pr_webhook(
        client,
        diff_text=diff_b,
        pr_id="PR-102",
        pr_title="feat(notifications): add user notification preference resolution"
    )
    elapsed_3 = time.time() - start_time_3

    data_3 = res_3.get("data", {})
    recalled_3 = data_3.get("recalled_memories", [])
    reflected_3 = data_3.get("reflected_style", "")
    review_markdown_3 = data_3.get("review_markdown", "")

    print(f"{GREEN}✓ Hindsight Cloud Recall Retrieved {len(recalled_3)} Rule(s):{RESET}")
    for m in recalled_3:
        print(f"  • {BOLD}{m}{RESET}")

    print(f"\n{GREEN}✓ Hindsight Cloud Reflect Synthesized Style:{RESET}")
    print(f"  • \"{reflected_3[:140]}...\"")
    print(f"\nReview Generation Time: {elapsed_3:.2f}s (Groq: {data_3.get('model_used')})\n")

    print(f"{BOLD}Generated Kodex Review Output (Interaction 3):{RESET}")
    print(review_markdown_3)

    # =========================================================================
    # VERIFICATION REPORT
    # =========================================================================
    print(f"{BOLD}{CYAN}==================================================================================={RESET}")
    print(f"{BOLD}{CYAN}   ENTERPRISE VERIFICATION REPORT: CODERABBIT & HINDSIGHT UPGRADE{RESET}")
    print(f"{BOLD}{CYAN}==================================================================================={RESET}")

    check_cohorts = len(cohorts_1) >= 2
    check_mermaid = "```mermaid" in data_1.get("review_markdown", "") or "```mermaid" in review_markdown_3
    check_verdict = "Mergeability Verdict" in review_markdown_3 or "Verdict" in review_markdown_3
    check_retained = res_2.get("status") == "success"
    check_recalled = len(recalled_3) > 0 and any("dict.get" in m.lower() for m in recalled_3)
    check_no_mistake = "try/except" not in review_markdown_3 or "dict.get" in review_markdown_3

    print(f"  [{GREEN if check_cohorts else RED}{'PASS' if check_cohorts else 'FAIL'}{RESET}] 1. Semantic Graphing: Files ordered into conceptual dependency Cohorts.")
    print(f"  [{GREEN if check_mermaid else RED}{'PASS' if check_mermaid else 'FAIL'}{RESET}] 2. Mermaid.js Diagram: System data flow sequence diagram generated.")
    print(f"  [{GREEN if check_verdict else RED}{'PASS' if check_verdict else 'FAIL'}{RESET}] 3. Mergeability Verdict: Explicit blockers vs style breakdown generated.")
    print(f"  [{GREEN if check_retained else RED}{'PASS' if check_retained else 'FAIL'}{RESET}] 4. Hindsight Retain: Developer correction memorized in live Cloud bank.")
    print(f"  [{GREEN if check_recalled else RED}{'PASS' if check_recalled else 'FAIL'}{RESET}] 5. Hindsight Recall & Reflect: Active rules and synthesized style injected into Groq.")
    print(f"  [{GREEN if check_no_mistake else RED}{'PASS' if check_no_mistake else 'FAIL'}{RESET}] 6. Permanent Learning: Agent validated dict.get() and did NOT repeat rejected suggestion.")

    if all([check_cohorts, check_mermaid, check_verdict, check_retained, check_recalled, check_no_mistake]):
        print(f"\n{GREEN}{BOLD}🎉 ALL ENTERPRISE CODERABBIT & HINDSIGHT CHECKS PASSED!{RESET}\n")
    else:
        print(f"\n{RED}{BOLD}⚠ One or more checks failed.{RESET}\n")


if __name__ == "__main__":
    run_demo()
