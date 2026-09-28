"""
Flask Webhook API Server for Kodex Enterprise AI Code Review Agent.
===================================================================

Exposes REST endpoints for PR reviews, developer learning loops,
and an interactive Tailwind CSS web dashboard.
"""

import logging
import re
import datetime
from flask import Flask, request, jsonify, render_template, Response

from config import config
from memory_client import memory_client
from review_engine import review_engine

logger = logging.getLogger("kodex.api")
logging.basicConfig(level=logging.INFO)

app = Flask(__name__, template_folder="templates")


def extract_rule_from_comment(comment_text: str) -> str:
    """
    Extracts or normalizes an architectural rule from natural language developer comments.

    Examples:
        'Developer: We actually prefer dict.get() over try/except for dictionaries here.'
        -> 'Use dict.get() instead of try/except blocks'

    Args:
        comment_text: Raw comment string from GitHub/GitLab PR review reply.

    Returns:
        str: Concise, normalized rule statement ready for memory retention.
    """
    text = comment_text.strip()
    if len(text.split()) <= 12 and not text.lower().startswith("developer:"):
        return text

    # Strip prefixes like 'Developer:', 'User:', 'Reviewer:'
    clean_text = re.sub(r"^(developer|user|reviewer|lead)\s*:\s*", "", text, flags=re.IGNORECASE).strip()

    # Detect common preference pattern: prefer X over Y
    lower = clean_text.lower()
    if "prefer" in lower and "over" in lower:
        match = re.search(r"prefer\s+([a-zA-Z0-9_\.\(\)]+)\s+over\s+([a-zA-Z0-9_\.\(\)\s/]+)", clean_text, re.IGNORECASE)
        if match:
            preferred = match.group(1).strip()
            rejected = match.group(2).split("for")[0].split("here")[0].strip()
            return f"Use {preferred} instead of {rejected} blocks"

    return clean_text


@app.route("/", methods=["GET"])
def index() -> str:
    """
    Renders the interactive Tailwind CSS dark-mode dashboard.

    Returns:
        HTML string of the rendered dashboard.
    """
    return render_template("index.html", config=config)


@app.route("/health", methods=["GET"])
def health() -> Response:
    """
    Health check and introspection endpoint for container probes and monitoring.

    Returns:
        JSON response with service health, active Groq model, and Hindsight status.
    """
    return jsonify({
        "status": "healthy",
        "service": "Kodex Enterprise AI Code Review Agent",
        "groq_model": config.GROQ_MODEL,
        "hindsight_bank": config.HINDSIGHT_BANK_ID,
        "hindsight_base_url": config.HINDSIGHT_BASE_URL,
        "hindsight_connected": memory_client.client is not None
    })


@app.route("/webhook/pr", methods=["POST"])
def webhook_pr() -> Response:
    """
    Webhook endpoint to trigger an automated code review on a pull request diff.
    Supports both rich GitHub webhook event JSON payloads and direct test payloads.

    Request Body:
        {
            "diff": "unified git diff text...",
            "pr_id": "PR-101",
            "title": "PR Title",
            "bank_id": "repo-standards" (optional)
        }

    Returns:
        JSON response containing the generated Kodex review, Mermaid sequence
        diagram, Mergeability Verdict, and recalled Hindsight context.
    """
    data = request.get_json(force=True, silent=True) or {}

    diff_text = data.get("diff", "")
    pr_id = "PR-101"
    pr_title = "Enterprise Feature Enhancement"
    bank_id = data.get("bank_id", config.HINDSIGHT_BANK_ID)
    sender = "developer"

    # Support rich GitHub webhook event structure
    if "pull_request" in data and isinstance(data["pull_request"], dict):
        pr_obj = data["pull_request"]
        pr_id = f"PR-#{pr_obj.get('number', 101)}"
        pr_title = pr_obj.get("title", pr_title)
        sender = pr_obj.get("user", {}).get("login", sender)
        diff_text = data.get("diff") or pr_obj.get("diff", "")
    else:
        pr_id = str(data.get("pr_id", data.get("number", pr_id)))
        pr_title = data.get("title", data.get("pr_title", pr_title))

    if not diff_text:
        return jsonify({
            "status": "error",
            "message": "Missing 'diff' field in request body. Provide unified git diff content."
        }), 400

    try:
        logger.info(f"Processing PR review request for {pr_id}: '{pr_title}' (Author: {sender})")
        review_result = review_engine.generate_review(
            diff_text=diff_text,
            pr_id=pr_id,
            pr_title=pr_title,
            bank_id=bank_id
        )
        return jsonify({
            "status": "success",
            "data": review_result
        }), 200
    except Exception as e:
        logger.exception("Error processing PR review")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route("/webhook/comment", methods=["POST"])
def webhook_comment() -> Response:
    """
    Webhook endpoint simulating developer review comment replies.
    Captures context and timestamp, calling client.retain(...) to permanently memorize corrections.

    Request Body:
        {
            "comment": "Developer feedback text...",
            "context": "developer PR correction" (optional),
            "bank_id": "repo-standards" (optional)
        }

    Returns:
        JSON response confirming memory retention in Hindsight Cloud.
    """
    data = request.get_json(force=True, silent=True) or {}

    comment_text = ""
    author = "developer"
    timestamp_str = None

    # Handle rich GitHub comment payload
    if "comment" in data and isinstance(data["comment"], dict):
        comment_obj = data["comment"]
        comment_text = comment_obj.get("body", "")
        author = comment_obj.get("user", {}).get("login", author)
        timestamp_str = comment_obj.get("created_at")
    else:
        comment_text = data.get("comment", data.get("text", data.get("content", "")))
        author = data.get("author", author)

    context = data.get("context", "developer PR correction")
    bank_id = data.get("bank_id", config.HINDSIGHT_BANK_ID)

    if not comment_text:
        return jsonify({
            "status": "error",
            "message": "Missing comment text in payload."
        }), 400

    # Parse ISO timestamp if provided
    ts = None
    if timestamp_str:
        try:
            ts = datetime.datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        except Exception:
            pass

    rule_content = data.get("content") or extract_rule_from_comment(comment_text)

    # Retain the rule in Hindsight Cloud
    retain_response = memory_client.retain(
        bank_id=bank_id,
        content=rule_content,
        context=context,
        timestamp=ts
    )

    return jsonify({
        "status": "success",
        "message": "Feedback retained in Hindsight memory bank",
        "bank_id": bank_id,
        "retained_rule": rule_content,
        "context": context,
        "author": author,
        "operation_id": getattr(retain_response, "operation_id", "live_retained"),
        "original_comment": comment_text
    }), 200


@app.route("/api/memories", methods=["GET"])
@app.route("/memories", methods=["GET"])
def get_memories() -> Response:
    """
    Lists all active memories and the reflected architectural style for the bank.
    Powers the Live Memory Viewer panel on the dashboard.

    Query Params:
        bank_id: Memory bank identifier (defaults to repo-standards).

    Returns:
        JSON response with memories list and reflected architectural summary.
    """
    bank_id = request.args.get("bank_id", config.HINDSIGHT_BANK_ID)
    memories = memory_client.get_all_memories(bank_id=bank_id)
    reflected = memory_client.reflect(bank_id=bank_id)
    return jsonify({
        "bank_id": bank_id,
        "total_memories": len(memories),
        "memories": memories,
        "reflected_style": reflected
    }), 200


@app.route("/api/memories", methods=["DELETE"])
@app.route("/memories", methods=["DELETE"])
def clear_memories() -> Response:
    """
    Resets the memory bank on Hindsight Cloud.
    Allows judges and testers to cleanly reset the demonstration state.

    Query Params:
        bank_id: Memory bank identifier (defaults to repo-standards).

    Returns:
        JSON response confirming bank reset.
    """
    bank_id = request.args.get("bank_id", config.HINDSIGHT_BANK_ID)
    memory_client.clear_bank(bank_id=bank_id)
    return jsonify({
        "status": "success",
        "message": f"Memory bank '{bank_id}' reset on Hindsight Cloud."
    }), 200


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
