"""
Memory Client Module for Vectorize Hindsight API.
=================================================

Provides an interface to Vectorize Hindsight Cloud (https://api.hindsight.vectorize.io)
implementing the core biomimetic memory operations:
  - recall: Searches and fetches concrete syntax rules & developer corrections.
  - reflect: Synthesizes high-level team architectural philosophy over time.
  - retain: Memorizes developer review feedback with context and timestamps.
"""

import logging
import uuid
import datetime
from typing import List, Dict, Any, Optional

from hindsight_client import (
    Hindsight,
    RecallResponse,
    RecallResult,
    RetainResponse
)
from config import config

logger = logging.getLogger("kodex.memory")
logging.basicConfig(level=logging.INFO)


class HindsightMemoryClient:
    """
    Client managing the repository's persistent memory bank using Vectorize Hindsight.

    Attributes:
        base_url: The Hindsight Cloud API base URL (default: https://api.hindsight.vectorize.io).
        api_key: Secret API key for authentication.
        bank_id: Isolated memory namespace for the target repository (default: repo-standards).
        client: Underlying Hindsight SDK client instance.
        _local_memories: In-memory cache providing read-your-own-writes consistency.
    """

    def __init__(self, base_url: str = None, api_key: str = None, bank_id: str = None):
        """
        Initializes the Hindsight memory client and provisions the target memory bank.

        Args:
            base_url: URL of the Hindsight instance.
            api_key: Hindsight Cloud authentication token.
            bank_id: Name of the memory bank to connect to.
        """
        self.base_url = base_url or config.HINDSIGHT_BASE_URL
        self.api_key = api_key or config.HINDSIGHT_API_KEY
        self.bank_id = bank_id or config.HINDSIGHT_BANK_ID

        self.client: Optional[Hindsight] = None
        self._local_memories: List[Dict[str, Any]] = []

        try:
            self.client = Hindsight(
                base_url=self.base_url,
                api_key=self.api_key or None,
                timeout=config.HINDSIGHT_TIMEOUT
            )
            logger.info(f"Connected to Hindsight Cloud at {self.base_url} (Bank: {self.bank_id})")
            self._ensure_bank_exists(self.bank_id)
        except Exception as e:
            logger.warning(f"Could not connect to live Hindsight Cloud ({e}). Operating in resilient mode.")
            self.client = None

    def _ensure_bank_exists(self, bank_id: str):
        """
        Checks if the bank exists on Hindsight Cloud, automatically creating it if not found.

        Args:
            bank_id: Target memory bank identifier.
        """
        if not self.client:
            return
        try:
            self.client.get_bank_config(bank_id)
        except Exception:
            try:
                logger.info(f"Provisioning memory bank '{bank_id}' on Hindsight Cloud...")
                self.client.create_bank(
                    bank_id=bank_id,
                    name=f"Kodex Standards - {bank_id}",
                    mission="Maintain enterprise team coding conventions, architectural patterns, and PR review corrections"
                )
                logger.info(f"Memory bank '{bank_id}' successfully provisioned.")
            except Exception as e:
                logger.warning(f"Note on bank provisioning for '{bank_id}': {e}")

    def recall(
        self,
        bank_id: str = None,
        query: str = "team coding conventions, architectural rules, past corrections"
    ) -> RecallResponse:
        """
        Searches the repository memory bank for specific coding conventions and past review corrections.

        Implements read-your-own-writes consistency: if cloud vectorization is in-flight,
        recently retained items from local memory are served seamlessly.

        Args:
            bank_id: Target memory bank identifier.
            query: Natural language retrieval query.

        Returns:
            RecallResponse: Hindsight response containing ranked RecallResult objects.
        """
        target_bank = bank_id or self.bank_id
        logger.info(f"🧠 [Hindsight:recall] Querying bank '{target_bank}' with query: '{query}'")

        if self.client:
            try:
                response = self.client.recall(bank_id=target_bank, query=query)
                if response and hasattr(response, "results") and response.results:
                    logger.info(f"🧠 [Hindsight:recall] Retrieved {len(response.results)} memories from Hindsight Cloud.")
                    return response
                elif self._local_memories:
                    logger.info(f"🧠 [Hindsight:recall] Serving {len(self._local_memories)} in-flight memories.")
                    results = [
                        RecallResult(
                            id=m.get("id", f"mem_{i}"),
                            text=m["text"],
                            type="architectural_rule",
                            context=m.get("context", "")
                        )
                        for i, m in enumerate(self._local_memories)
                    ]
                    return RecallResponse(results=results)
                return RecallResponse(results=[])
            except Exception as e:
                logger.warning(f"Hindsight recall failed or timed out ({e}). Serving cached memories.")

        # Local cache fallback
        results = [
            RecallResult(
                id=m.get("id", f"mem_{i}"),
                text=m["text"],
                type="architectural_rule",
                context=m.get("context", "")
            )
            for i, m in enumerate(self._local_memories)
        ]
        return RecallResponse(results=results)

    def reflect(
        self,
        bank_id: str = None,
        query: str = "What is the team's overall architectural style?"
    ) -> str:
        """
        Synthesizes a high-level summary of the team's architectural norms over time
        using Hindsight's LLM reasoning and reflection layer.

        Args:
            bank_id: Target memory bank identifier.
            query: Reasoning prompt for synthesis.

        Returns:
            str: Synthesized architectural summary text.
        """
        target_bank = bank_id or self.bank_id
        logger.info(f"🧠 [Hindsight:reflect] Synthesizing architectural style from bank '{target_bank}'...")

        if self.client:
            try:
                reflect_resp = self.client.reflect(bank_id=target_bank, query=query)
                reflect_text = getattr(reflect_resp, "text", str(reflect_resp))
                if reflect_text and len(reflect_text.strip()) > 10:
                    logger.info(f"🧠 [Hindsight:reflect] Synthesis generated ({len(reflect_text)} chars).")
                    return reflect_text.strip()
            except Exception as e:
                logger.warning(f"Hindsight reflect failed or timed out ({e}). Using synthesized baseline.")

        if self._local_memories:
            rules_summary = "; ".join(m["text"] for m in self._local_memories)
            return f"The team adheres to pragmatic, idiomatic patterns. Active team conventions: {rules_summary}."
        return "No historical conventions recorded yet. Reviewing against standard industry best practices."

    def retain(
        self,
        bank_id: str = None,
        content: str = "",
        context: str = "developer PR correction",
        timestamp: Optional[datetime.datetime] = None
    ) -> RetainResponse:
        """
        Memorizes a new coding convention or developer correction into the repository's bank.

        Args:
            bank_id: Target memory bank identifier.
            content: The rule or convention statement to memorize.
            context: Metadata describing the origin (e.g. 'developer PR correction').
            timestamp: Optional UTC timestamp when the interaction took place.

        Returns:
            RetainResponse: Hindsight retain confirmation object.
        """
        target_bank = bank_id or self.bank_id
        now = timestamp or datetime.datetime.now(datetime.timezone.utc)
        logger.info(f"🧠 [Hindsight:retain] Retaining rule in bank '{target_bank}': '{content}' (context: '{context}')")

        op_id = f"mem_{uuid.uuid4().hex[:8]}"

        # Record locally for instant consistency
        self._local_memories.append({
            "id": op_id,
            "text": content,
            "context": context,
            "timestamp": now.isoformat()
        })

        if self.client:
            try:
                resp = self.client.retain(
                    bank_id=target_bank,
                    content=content,
                    context=context,
                    timestamp=now
                )
                logger.info(f"🧠 [Hindsight:retain] Stored on Hindsight Cloud. Items: {resp.items_count}")
                return resp
            except Exception as e:
                logger.warning(f"Hindsight cloud retain failed ({e}). Retained locally.")

        return RetainResponse(
            success=True,
            bank_id=target_bank,
            items_count=1,
            var_async=False,
            operation_id=op_id
        )

    def get_all_memories(self, bank_id: str = None) -> List[Dict[str, Any]]:
        """
        Retrieves all currently stored memories in the bank for dashboard inspection.

        Args:
            bank_id: Target memory bank identifier.

        Returns:
            List[Dict[str, Any]]: List of memory dictionary records.
        """
        target_bank = bank_id or self.bank_id
        if self.client:
            try:
                rec = self.client.recall(bank_id=target_bank, query="all team coding conventions and architectural rules")
                if rec and hasattr(rec, "results") and rec.results:
                    cloud_memories = [
                        {
                            "id": r.id or f"mem_{i}",
                            "text": r.text,
                            "context": r.context or "PR feedback correction",
                            "type": r.type or "rule"
                        }
                        for i, r in enumerate(rec.results)
                    ]
                    if cloud_memories:
                        return cloud_memories
            except Exception:
                pass
        return self._local_memories

    def clear_bank(self, bank_id: str = None):
        """
        Resets and clears the memory bank (ideal for tests or fresh demo runs).

        Args:
            bank_id: Target memory bank identifier.
        """
        target_bank = bank_id or self.bank_id
        self._local_memories = []
        if self.client:
            try:
                logger.info(f"Resetting bank '{target_bank}' on Hindsight Cloud...")
                self.client.delete_bank(target_bank)
            except Exception:
                pass
            self._ensure_bank_exists(target_bank)
        logger.info(f"Memory bank '{target_bank}' cleared and reset.")


# Global singleton client instance
memory_client = HindsightMemoryClient()
