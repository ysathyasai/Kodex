# Kodex Enterprise Walkthrough Video Script (2-3 Minutes)

> **Theme**: Demonstrating how Kodex replicates Kodex's enterprise architecture using Semantic Cohorts, Mermaid sequence diagrams, and Vectorize Hindsight's dual memory engine.

---

### [0:00 - 0:35] Scene 1: The Code Review Bottleneck (Hook)
- **Visual**: Screen showing a GitHub PR with an annoying generic bot comment suggesting `try/except KeyError` on a clean `dict.get()` line, followed by an alphabetical diff view where tests are reviewed before database schema.
- **Narrator**:
  > *"Traditional AI code reviewers have two major flaws. First, they review files alphabetically, breaking the author's logical dependency sequence. Second, they suffer from amnesia—repeating rejected suggestions PR after PR.
  > Today, we're demonstrating Kodex: an enterprise AI Code Review Agent replicating Kodex, built with Groq for ultra-fast reasoning with openai/gpt-oss-120b, and Vectorize Hindsight Cloud for persistent long-term memory."*

---

### [0:35 - 1:15] Scene 2: Semantic Cohorts & Interaction 1 (The Baseline)
- **Visual**: Terminal running `python demo_runner.py` showing files re-sequenced into Cohorts.
- **Narrator**:
  > *"Watch what happens when an author submits PR #101 with four files.
  > Instead of reading alphabetically, Kodex groups the diff into Semantic Cohorts:
  > Database Schema first, then Core Business Logic, then API routes, and finally Tests.
  > Before reviewing, Kodex calls Hindsight Cloud:
  > `client.recall()` to fetch explicit rules, and `client.reflect()` to synthesize the team's overall architectural style.
  > Since this is a fresh repository, zero rules exist.
  > Groq generates an enterprise Kodex review featuring an Executive Summary, a Mermaid.js Sequence Diagram, and a Mergeability Verdict.
  > Because it lacks past context, it suggests replacing dict.get() with explicit try/except KeyError handling."*

---

### [1:15 - 1:45] Scene 3: Developer Correction & Hindsight Retain Loop
- **Visual**: Tech lead's comment being submitted to `/webhook/comment`.
- **Narrator**:
  > *"Now, the tech lead replies on GitHub:
  > 'Developer: We actually prefer dict.get() over try/except for dictionaries here. In our microservices, configurations have standard fallbacks and exception handling adds unnecessary overhead.'
  > The webhook fires to `/webhook/comment`.
  > Kodex calls `client.retain()` on Hindsight Cloud, capturing the rule, the context, and the timestamp.
  > Hindsight indexes this into the repository's long-term memory bank."*

---

### [1:45 - 2:30] Scene 4: Interaction 3 (The Memory Payoff & Validation)
- **Visual**: Terminal executing Step 3, highlighting the Kodex review markdown.
- **Narrator**:
  > *"Days later, another engineer opens PR #102 with the exact same dict.get() pattern.
  > Kodex runs its dual pre-review memory check:
  > `recall()` returns the retained rule, and `reflect()` synthesizes the team's error handling philosophy.
  > Look at the generated Kodex output:
  > Under the Walkthrough, it generates a complete Mermaid.js sequence diagram of the notification pipeline.
  > The Mergeability Verdict is marked 'APPROVED'.
  > Under 'Hindsight Memory Alignment', it explicitly validates the author's use of dict.get(), citing the team convention learned from past review feedback.
  > It DOES NOT repeat the rejected try/except advice!
  > All six enterprise verification checks pass."*

---

### [2:30 - 3:00] Scene 5: Conclusion
- **Visual**: Kodex Web Dashboard showing active memory rules and reflected architectural style.
- **Narrator**:
  > *"Kodex transforms AI from a noisy linter into an intelligent code reviewer that respects dependency order and gets smarter with every single pull request.
  > Powered by Groq and Vectorize Hindsight Cloud. Thank you for watching!"*
