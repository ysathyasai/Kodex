"""
Unit and integration tests for Kodex Code Review Agent.
Tests diff parsing, memory retention/recall, and webhook endpoints.
"""

import pytest
from app import app
from memory_client import memory_client
from diff_parser import GitDiffParser


@pytest.fixture
def client():
    """
    Creates and configures a Flask test client instance for testing HTTP endpoints.

    Yields:
        FlaskClient: Configured Flask test client.
    """
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def clean_memory():
    """
    Autouse fixture that ensures an isolated, clean Hindsight memory bank
    before and after each test execution to prevent test pollution.
    """
    memory_client.clear_bank("repo-standards")
    yield
    memory_client.clear_bank("repo-standards")


def test_git_diff_parser() -> None:
    """
    Tests the unified git diff parsing engine.
    Verifies that file paths, addition/deletion counters, and LLM formatting
    are accurately extracted from raw unified diff strings.
    """
    sample_diff = """diff --git a/services/auth.py b/services/auth.py
index 1234567..89abcdef 100644
--- a/services/auth.py
+++ b/services/auth.py
@@ -10,4 +10,6 @@ class AuthService:
     def authenticate(self, token: str) -> bool:
-        return token == "secret"
+        # Secure verification
+        return hmac.compare_digest(token, "secret")
"""
    parsed = GitDiffParser.parse(sample_diff)
    assert len(parsed.files) == 1
    assert parsed.files[0].display_path == "services/auth.py"
    assert parsed.total_additions == 2
    assert parsed.total_deletions == 1
    assert "1 file changed" in parsed.summary

    formatted = GitDiffParser.format_for_llm(parsed)
    assert "services/auth.py" in formatted
    assert "hmac.compare_digest" in formatted


def test_memory_retain_and_recall() -> None:
    """
    Tests the Hindsight Cloud memory client operations:
    1. Initial state verification (empty bank).
    2. Retaining a new convention via `client.retain(...)`.
    3. Recalling the convention via `client.recall(...)` with read-your-own-writes consistency.
    4. Synthesizing high-level architectural philosophy via `client.reflect(...)`.
    """
    bank = "repo-standards"

    # Initially empty
    initial_recall = memory_client.recall(bank_id=bank, query="coding conventions")
    assert len(initial_recall.results) == 0

    # Retain rule
    retain_res = memory_client.retain(
        bank_id=bank,
        content="Use dict.get() instead of try/except blocks",
        context="PR feedback correction"
    )
    assert retain_res.success is True
    assert retain_res.bank_id == bank

    # Recall rule
    recalled = memory_client.recall(bank_id=bank, query="team coding conventions, architectural rules, past corrections")
    assert len(recalled.results) >= 1
    assert any("dict.get()" in r.text for r in recalled.results)

    # Reflect synthesized architectural style
    reflected = memory_client.reflect(bank_id=bank)
    assert isinstance(reflected, str)
    assert len(reflected) > 0


def test_semantic_cohorts_ordering() -> None:
    """
    Tests the Semantic Cohort classification and dependency ordering.
    Verifies that files in a multi-file diff are re-ordered into cognitive dependency
    sequence: Database Schema (SQL) -> Business Logic (Python service) -> Tests (test_api).
    """
    multi_diff = """diff --git a/tests/test_api.py b/tests/test_api.py
--- a/tests/test_api.py
+++ b/tests/test_api.py
@@ -1,2 +1,3 @@
+def test_api(): pass
diff --git a/migrations/001_init.sql b/migrations/001_init.sql
--- a/migrations/001_init.sql
+++ b/migrations/001_init.sql
@@ -1,2 +1,3 @@
+CREATE TABLE test();
diff --git a/src/services/billing.py b/src/services/billing.py
--- a/src/services/billing.py
+++ b/src/services/billing.py
@@ -1,2 +1,3 @@
+def bill(): pass
"""
    parsed = GitDiffParser.parse(multi_diff)
    ordered = [f.display_path for f in parsed.get_dependency_ordered_files()]
    # Schema (001_init.sql) -> Business Logic (billing.py) -> Tests (test_api.py)
    assert ordered == ["migrations/001_init.sql", "src/services/billing.py", "tests/test_api.py"]


def test_webhook_pr_endpoint(client) -> None:
    """
    Tests the `/webhook/pr` endpoint with a sample pull request diff.
    Verifies that the endpoint returns 200 OK and includes a Kodex-formatted
    review with walkthrough and architecture overview.
    """
    diff = """diff --git a/app/config.py b/app/config.py
--- a/app/config.py
+++ b/app/config.py
@@ -1,3 +1,4 @@
 def load():
+    return config.get('port', 8080)
"""
    res = client.post("/webhook/pr", json={
        "pr_id": "PR-999",
        "title": "Configure port",
        "diff": diff
    })
    assert res.status_code == 200
    data = res.get_json()["data"]
    assert data["pr_id"] == "PR-999"
    assert "Kodex" in data["review_markdown"]
    assert "Walkthrough" in data["review_markdown"] or "Overview" in data["review_markdown"]


def test_webhook_comment_endpoint(client) -> None:
    """
    Tests the `/webhook/comment` endpoint simulating a developer PR reply.
    Verifies that the rule is extracted, committed to Hindsight Cloud memory,
    and immediately accessible via the `/memories` inspection endpoint.
    """
    res = client.post("/webhook/comment", json={
        "comment": "Developer: We actually prefer dict.get() over try/except for dictionaries here.",
        "context": "PR feedback correction",
        "bank_id": "repo-standards"
    })
    assert res.status_code == 200
    json_data = res.get_json()
    assert json_data["status"] == "success"
    assert "dict.get()" in json_data["retained_rule"]

    # Verify memory is listed in /memories
    mem_res = client.get("/memories")
    assert mem_res.status_code == 200
    memories = mem_res.get_json()["memories"]
    assert len(memories) >= 1
