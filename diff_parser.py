"""
Git Diff Parser Module for Kodex Code Review Agent.
===================================================

Provides unified git diff parsing and semantic cohort classification.
Re-orders diff files from naive alphabetical order into dependency sequence:
  1. Database Schema & Migrations (DDL, SQL, Prisma, Alembic)
  2. Core Business Logic & Domain Models (Services, Handlers, Core)
  3. API & Presentation Layer (Routes, Controllers, Components)
  4. Tests & Quality Gates (Unit Tests, E2E, Fixtures)
  5. Configuration & Infrastructure (Docker, K8s, YAML, Config)
"""

import re
import os
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple


class SemanticCohort:
    """
    Defines architectural cohorts to order files by cognitive build sequence.

    Attributes:
        DATABASE_SCHEMA: Priority 1 (Schema definitions and migrations)
        BUSINESS_LOGIC: Priority 2 (Domain models and services)
        API_PRESENTATION: Priority 3 (HTTP routes and UI components)
        TESTS_FIXTURES: Priority 4 (Unit tests and verification suites)
        CONFIG_INFRA: Priority 5 (Deployment configs and container specs)
        GENERAL: Priority 6 (Unclassified documentation and assets)
    """
    DATABASE_SCHEMA = (1, "Database Schema & Migrations", "💾")
    BUSINESS_LOGIC = (2, "Core Business Logic & Domain Models", "⚙️")
    API_PRESENTATION = (3, "API & Presentation Layer", "🌐")
    TESTS_FIXTURES = (4, "Tests & Quality Gates", "🧪")
    CONFIG_INFRA = (5, "Configuration & Infrastructure", "📦")
    GENERAL = (6, "General Application Assets", "📄")

    @classmethod
    def classify(cls, path: str) -> Tuple[int, str, str]:
        """
        Classifies a file path into its logical dependency cohort based on directory
        structure, naming conventions, and file extensions.

        Args:
            path: Relative or absolute file path from the git diff.

        Returns:
            Tuple[int, str, str]: (priority_number, cohort_name, cohort_icon)
        """
        if not path:
            return cls.GENERAL

        p = path.lower().replace("\\", "/")
        filename = os.path.basename(p)

        # 1. Database Schema & Migrations: Foundation of data persistence
        db_indicators = [
            "migration", "alembic", "prisma", "schema", "db/", "sql/",
            "entities/", "entity/", "table", "ddl"
        ]
        if any(ind in p for ind in db_indicators) or p.endswith(".sql") or p.endswith(".prisma"):
            return cls.DATABASE_SCHEMA

        # 4. Tests & Quality Gates: Check before business logic to catch test_service.py
        test_indicators = [
            "test/", "tests/", "spec/", "fixtures/", "mock/", "mocks/",
            "e2e/", "test_", "_test.", ".spec.", ".test."
        ]
        if any(ind in p for ind in test_indicators):
            return cls.TESTS_FIXTURES

        # 5. Configuration & Infrastructure: Build configs and environment manifests
        infra_indicators = [
            "config", "infra", "k8s", "terraform", "helm", "deploy",
            ".github", "docker", "requirements.txt", "pyproject.toml",
            "package.json", ".env", "makefile"
        ]
        if any(ind in p for ind in infra_indicators) or filename.startswith(".env") or p.endswith(".yml") or p.endswith(".yaml"):
            return cls.CONFIG_INFRA

        # 3. API & Presentation Layer: External boundary and UI interfaces
        api_indicators = [
            "api/", "routes/", "endpoints/", "views/", "templates/",
            "components/", "frontend/", "ui/", "static/", "web/",
            "graphql/", "serializers/", "controllers/", "pages/"
        ]
        ui_exts = (".jsx", ".tsx", ".vue", ".html", ".css", ".scss", ".svelte")
        if any(ind in p for ind in api_indicators) or p.endswith(ui_exts):
            return cls.API_PRESENTATION

        # 2. Core Business Logic & Domain Models: Application core
        biz_indicators = [
            "services/", "service", "domain/", "core/", "use_cases/",
            "handlers/", "managers/", "billing/", "payments/", "auth/",
            "logic/", "utils/", "lib/", "models/"
        ]
        if any(ind in p for ind in biz_indicators) or p.endswith(".py") or p.endswith(".go") or p.endswith(".java") or p.endswith(".ts"):
            return cls.BUSINESS_LOGIC

        return cls.GENERAL


@dataclass
class DiffLine:
    """
    Represents a single line of code within a diff hunk.

    Attributes:
        line_type: '+' for addition, '-' for deletion, ' ' for unchanged context.
        content: Code string without the leading diff marker character.
        old_line_num: 1-indexed line number in the original file (if context or deletion).
        new_line_num: 1-indexed line number in the modified file (if context or addition).
    """
    line_type: str
    content: str
    old_line_num: Optional[int] = None
    new_line_num: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the diff line to a dictionary."""
        return asdict(self)


@dataclass
class DiffHunk:
    """
    Represents a unified diff hunk enclosed by @@ -old +new @@ markers.

    Attributes:
        old_start: Starting line number in the source file.
        old_count: Line count in the source file hunk.
        new_start: Starting line number in the target file.
        new_count: Line count in the target file hunk.
        header: Optional section header text after the @@ markers.
        lines: Sequential list of DiffLine instances.
    """
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    header: str
    lines: List[DiffLine] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the diff hunk to a dictionary."""
        return {
            "old_start": self.old_start,
            "old_count": self.old_count,
            "new_start": self.new_start,
            "new_count": self.new_count,
            "header": self.header,
            "lines": [line.to_dict() for line in self.lines]
        }


@dataclass
class FileDiff:
    """
    Represents all modifications made to a single file within a pull request.

    Attributes:
        old_path: Original file path (None if added).
        new_path: New file path (None if deleted).
        status: 'modified', 'added', 'deleted', or 'renamed'.
        hunks: List of parsed DiffHunk objects.
        additions: Total line insertions count.
        deletions: Total line deletions count.
    """
    old_path: Optional[str]
    new_path: Optional[str]
    status: str
    hunks: List[DiffHunk] = field(default_factory=list)
    additions: int = 0
    deletions: int = 0

    @property
    def display_path(self) -> str:
        """Returns the active display path for the file."""
        return self.new_path or self.old_path or "unknown_file"

    @property
    def cohort(self) -> Tuple[int, str, str]:
        """Returns the classified semantic cohort tuple."""
        return SemanticCohort.classify(self.display_path)

    @property
    def cohort_priority(self) -> int:
        """Returns the numeric priority of the cohort (1 to 6)."""
        return self.cohort[0]

    @property
    def cohort_name(self) -> str:
        """Returns the human-readable cohort name."""
        return self.cohort[1]

    @property
    def cohort_icon(self) -> str:
        """Returns the cohort emoji icon."""
        return self.cohort[2]

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the file diff and metadata to a dictionary."""
        return {
            "old_path": self.old_path,
            "new_path": self.new_path,
            "display_path": self.display_path,
            "status": self.status,
            "additions": self.additions,
            "deletions": self.deletions,
            "cohort": {
                "priority": self.cohort_priority,
                "name": self.cohort_name,
                "icon": self.cohort_icon
            },
            "hunks": [hunk.to_dict() for hunk in self.hunks]
        }


@dataclass
class ParsedDiff:
    """
    Container representing the entire parsed pull request diff.

    Attributes:
        files: List of FileDiff objects for all modified files.
        total_additions: Total insertions across all files.
        total_deletions: Total deletions across all files.
    """
    files: List[FileDiff] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0

    @property
    def summary(self) -> str:
        """Returns a standard git-style summary string (e.g. '3 files changed, 10 insertions(+)')."""
        num_files = len(self.files)
        files_str = f"{num_files} file{'s' if num_files != 1 else ''} changed"
        return f"{files_str}, {self.total_additions} insertions(+), {self.total_deletions} deletions(-)"

    def get_dependency_ordered_files(self) -> List[FileDiff]:
        """
        Orders files by their semantic cohort dependency sequence:
        Schema (1) -> Business Logic (2) -> API/Presentation (3) -> Tests (4) -> Config (5).

        Returns:
            List[FileDiff]: Files sorted by (cohort_priority, display_path).
        """
        return sorted(self.files, key=lambda f: (f.cohort_priority, f.display_path))

    def get_cohort_breakdown(self) -> Dict[str, List[FileDiff]]:
        """
        Groups files by their semantic cohort for the review walkthrough.

        Returns:
            Dict[str, List[FileDiff]]: Mapping of cohort label to list of files.
        """
        groups: Dict[str, List[FileDiff]] = {}
        for f in self.get_dependency_ordered_files():
            key = f"{f.cohort_icon} {f.cohort_name}"
            if key not in groups:
                groups[key] = []
            groups[key].append(f)
        return groups

    def to_dict(self) -> Dict[str, Any]:
        """Serializes the parsed diff to a dictionary representation."""
        return {
            "files": [f.to_dict() for f in self.get_dependency_ordered_files()],
            "total_additions": self.total_additions,
            "total_deletions": self.total_deletions,
            "summary": self.summary,
            "cohorts": {
                k: [f.display_path for f in v]
                for k, v in self.get_cohort_breakdown().items()
            }
        }


class GitDiffParser:
    """
    Parser for unified git diff format.
    Transforms raw git diff strings into structured, line-numbered objects.
    """

    HUNK_HEADER_REGEX = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")

    @classmethod
    def parse(cls, diff_content: str) -> ParsedDiff:
        """
        Parses a raw unified git diff string into a ParsedDiff instance.

        Args:
            diff_content: Raw git diff text (e.g. from `git diff` or PR webhook).

        Returns:
            ParsedDiff: Structured collection of modified files and hunks.
        """
        lines = diff_content.splitlines()
        parsed = ParsedDiff()

        current_file: Optional[FileDiff] = None
        current_hunk: Optional[DiffHunk] = None
        old_line_cursor = 0
        new_line_cursor = 0

        i = 0
        while i < len(lines):
            line = lines[i]

            # Detect git diff file header: diff --git a/path b/path
            if line.startswith("diff --git "):
                if current_file:
                    if current_hunk:
                        current_file.hunks.append(current_hunk)
                        current_hunk = None
                    parsed.files.append(current_file)

                parts = line.split(" ")
                old_p = parts[2][2:] if len(parts) > 2 and parts[2].startswith("a/") else None
                new_p = parts[3][2:] if len(parts) > 3 and parts[3].startswith("b/") else None

                current_file = FileDiff(
                    old_path=old_p,
                    new_path=new_p,
                    status="modified"
                )
                i += 1
                continue

            # Detect file mode lines
            if line.startswith("new file mode"):
                if current_file:
                    current_file.status = "added"
                i += 1
                continue
            elif line.startswith("deleted file mode"):
                if current_file:
                    current_file.status = "deleted"
                i += 1
                continue

            # Explicit file path markers
            if line.startswith("--- "):
                if current_file is None:
                    current_file = FileDiff(old_path=None, new_path=None, status="modified")
                path_part = line[4:].strip()
                if path_part == "/dev/null":
                    current_file.status = "added"
                    current_file.old_path = None
                elif path_part.startswith("a/"):
                    current_file.old_path = path_part[2:]
                else:
                    current_file.old_path = path_part
                i += 1
                continue

            if line.startswith("+++ "):
                if current_file is None:
                    current_file = FileDiff(old_path=None, new_path=None, status="modified")
                path_part = line[4:].strip()
                if path_part == "/dev/null":
                    current_file.status = "deleted"
                    current_file.new_path = None
                elif path_part.startswith("b/"):
                    current_file.new_path = path_part[2:]
                else:
                    current_file.new_path = path_part
                i += 1
                continue

            # Hunk header matching: @@ -old_start,old_count +new_start,new_count @@
            hunk_match = cls.HUNK_HEADER_REGEX.match(line)
            if hunk_match:
                if current_file is None:
                    current_file = FileDiff(old_path="unknown", new_path="unknown", status="modified")

                if current_hunk:
                    current_file.hunks.append(current_hunk)

                old_start = int(hunk_match.group(1))
                old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
                new_start = int(hunk_match.group(3))
                new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1
                header_text = hunk_match.group(5).strip()

                current_hunk = DiffHunk(
                    old_start=old_start,
                    old_count=old_count,
                    new_start=new_start,
                    new_count=new_count,
                    header=header_text
                )
                old_line_cursor = old_start
                new_line_cursor = new_start
                i += 1
                continue

            # Content lines inside a hunk
            if current_hunk is not None:
                if line.startswith("+"):
                    parsed.total_additions += 1
                    if current_file:
                        current_file.additions += 1
                    diff_line = DiffLine(
                        line_type="+",
                        content=line[1:],
                        old_line_num=None,
                        new_line_num=new_line_cursor
                    )
                    current_hunk.lines.append(diff_line)
                    new_line_cursor += 1
                elif line.startswith("-"):
                    parsed.total_deletions += 1
                    if current_file:
                        current_file.deletions += 1
                    diff_line = DiffLine(
                        line_type="-",
                        content=line[1:],
                        old_line_num=old_line_cursor,
                        new_line_num=None
                    )
                    current_hunk.lines.append(diff_line)
                    old_line_cursor += 1
                elif line.startswith(" "):
                    diff_line = DiffLine(
                        line_type=" ",
                        content=line[1:],
                        old_line_num=old_line_cursor,
                        new_line_num=new_line_cursor
                    )
                    current_hunk.lines.append(diff_line)
                    old_line_cursor += 1
                    new_line_cursor += 1
                elif line.startswith(r"\ No newline at end of file"):
                    pass

            i += 1

        if current_file:
            if current_hunk:
                current_file.hunks.append(current_hunk)
            parsed.files.append(current_file)

        return parsed

    @classmethod
    def format_for_llm(cls, parsed: ParsedDiff, max_chars: int = 16000) -> str:
        """
        Formats a parsed diff into an LLM-optimized presentation grouped by Semantic Cohorts.
        Includes explicit line numbers for accurate line-level code suggestions.

        Args:
            parsed: ParsedDiff instance containing file hunks.
            max_chars: Upper character limit to prevent token overflows.

        Returns:
            str: Markdown-formatted diff view with line coordinates.
        """
        output_chunks = []
        output_chunks.append(f"### Diff Summary: {parsed.summary}")
        output_chunks.append("Files grouped by Dependency Cohorts (Review Sequence):")
        output_chunks.append("")

        cohort_groups = parsed.get_cohort_breakdown()
        for cohort_label, files in cohort_groups.items():
            output_chunks.append(f"==================================================")
            output_chunks.append(f"## COHORT: {cohort_label} ({len(files)} file{'s' if len(files) != 1 else ''})")
            output_chunks.append(f"==================================================")
            output_chunks.append("")

            for f in files:
                file_header = f"File: {f.display_path} ({f.status.upper()} | +{f.additions} -{f.deletions})"
                output_chunks.append(file_header)
                output_chunks.append("-" * len(file_header))

                for hunk in f.hunks:
                    output_chunks.append(f"--- Hunk @@ -{hunk.old_start},{hunk.old_count} +{hunk.new_start},{hunk.new_count} @@ {hunk.header}")
                    for line in hunk.lines:
                        if line.line_type == "+":
                            output_chunks.append(f"  + L{line.new_line_num:4d} | {line.content}")
                        elif line.line_type == "-":
                            output_chunks.append(f"  - L{line.old_line_num:4d} | {line.content}")
                        else:
                            output_chunks.append(f"    L{line.new_line_num:4d} | {line.content}")
                    output_chunks.append("")

        result = "\n".join(output_chunks)
        if len(result) > max_chars:
            result = result[:max_chars] + f"\n\n[Diff truncated to {max_chars} characters for review context]"
        return result


def parse_diff_file(file_path: str) -> ParsedDiff:
    """
    Convenience helper function to parse a diff directly from a filesystem file.

    Args:
        file_path: Path to the .diff or .patch file.

    Returns:
        ParsedDiff: Structured representation of the diff file.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return GitDiffParser.parse(f.read())
