# How We Replicated Kodex's Enterprise Architecture Using Hindsight and Groq

Every software engineer knows the exhaustion of modern code reviews. 

You open a Pull Request. Ten minutes later, an automated bot comments on multiple lines, advising you to rewrite idiomatic `dict.get(key, default)` statements into verbose `try/except KeyError` blocks. 

You reply: *"We prefer `dict.get()` with defaults across our microservices to keep the hot path lean."* 

The next week, you submit another PR. What does the AI bot do? It leaves the exact same comment on the exact same pattern.

Stateless AI reviewers suffer from chronic amnesia. They evaluate every diff alphabetically and in isolation, completely oblivious to your team's hard-won architectural conventions, past debates, and dependency order. 

For **HackwithHyderabad 3.0**, we upgraded **Kodex** to replicate the enterprise-grade architecture of **Kodex**, powered by Groq's high-speed inference (`openai/gpt-oss-120b`) and Vectorize's **Hindsight** memory engine.

Here is how we designed it, why dependency ordering and dual memory matter, and what we learned along the way.

---

## 1. Beyond Alphabetical Diffs: Semantic Graphing & Cohorts

Standard reviewers read diffs in alphabetical order: `api/` -> `config/` -> `migrations/` -> `services/` -> `tests/`.

This breaks the cognitive flow of code review. No human builds software alphabetically; you build the database schema first, followed by domain models, business logic, API interfaces, and tests.

Kodex replaces alphabetical ordering with **Semantic Cohorts**:
1. **💾 Database Schema & Migrations** (`migrations/`, `schema/`, `*.sql`)
2. **⚙️ Core Business Logic & Domain Models** (`services/`, `domain/`, `core/`)
3. **🌐 API & Presentation Layer** (`api/`, `routes/`, `views/`, `components/`)
4. **🧪 Tests & Quality Gates** (`tests/`, `fixtures/`, `mocks/`)
5. **📦 Configuration & Infrastructure** (`config/`, `docker`, `k8s/`)

By reorganizing raw diff hunks into conceptual cohorts, Groq's LLM analyzes foundational schema definitions before evaluating the business logic that depends on them.

---

## 2. The Overview Walkthrough: Sequence Diagrams & Mergeability Verdicts

A stream of disjointed line comments creates review fatigue. Kodex generates an enterprise Walkthrough at the top of every review output:

- **1-2 Sentence Executive Summary**: Captures the architectural intent of the PR.
- **Dynamic Mermaid.js Sequence Diagram**: Illustrates the exact runtime data flow introduced or modified by the pull request.
- **Mergeability Verdict**: Explicitly distinguishes between hard blockers (`🛑 BLOCKED`), non-breaking architectural considerations (`⚠️ NEEDS WORK`), and optional style nitpicks (`✅ APPROVED`).
- **Actionable Line-Level Comments**: Placed in a dedicated section underneath the Walkthrough with zero redundant context, complete with GitHub markdown suggestion blocks.

---

## 3. Dual Hindsight Memory Engine: Recall + Reflect

Naive RAG pipelines rely solely on vector search across static documentation. Real engineering teams need memory that evolves with every PR interaction.

Kodex integrates the full Vectorize Hindsight suite:

### Pre-Review: `recall` & `reflect`
Before prompting the Groq LLM, Kodex executes two memory passes:
1. **`client.recall()`**: Fetches specific, concrete syntax rules and past review feedback:
   ```python
   recalled_rules = client.recall(
       bank_id="repo-standards",
       query="team coding conventions, architectural rules, past corrections"
   )
   ```
2. **`client.reflect()`**: Synthesizes the team's overarching architectural philosophy over time:
   ```python
   reflected_style = client.reflect(
       bank_id="repo-standards",
       query="What is the team's overall architectural style?"
   )
   ```

Both the granular rules and the synthesized architectural summary are injected into Groq's system prompt.

### Post-Review: `retain`
When a developer replies to a review comment:
> *"Developer: We actually prefer dict.get() over try/except for dictionaries here."*

The webhook captures the correction with context and timestamp:
```python
client.retain(
    bank_id="repo-standards",
    content="Use dict.get() instead of try/except blocks",
    context="developer PR correction",
    timestamp=datetime.now(timezone.utc)
)
```

Hindsight commits this into the repository's long-term memory graph. On the very next PR containing `dict.get()`, Kodex recalls the convention, validates the pattern, and **never repeats the rejected suggestion**.

---

## 4. Why Groq and openai/gpt-oss-120b

Evaluating multi-file diffs, synthesizing Mermaid sequence diagrams, and rendering line-level AST suggestions requires a model with deep reasoning capacity. 

Running `openai/gpt-oss-120b` on Groq's LPU architecture delivers enterprise reasoning with near-instantaneous latency, processing complex 4-file PRs in seconds.

---

## 5. What We Learned

1. **Cognitive Sequencing Changes Everything:** Sorting diffs into Semantic Cohorts prevents the LLM from hallucinating missing models that simply appeared later in an alphabetical list.
2. **Dual Memory (`recall` + `reflect`) is Superior to Raw RAG:** `recall` gives the agent exact tactical rules, while `reflect` gives it strategic architectural alignment.
3. **Developers Love an Agent That Learns:** When an AI code reviewer remembers a developer's feedback from last Tuesday, it stops feeling like a mechanical linter and starts feeling like a teammate.

Check out the full open-source implementation:
[https://github.com/your-username/kodex](https://github.com/your-username/kodex)
