# src/claude/client.py
"""
Claude API client wrapper.

WHY THIS EXISTS:
  Every agent needs Claude. Instead of each agent importing anthropic
  directly, they all use this wrapper. This means:
  - One place to change the model
  - One place to add logging
  - One place to handle errors
  - One place to add prompt caching later

SENIOR NOTE:
  Your certification notes cover prompt caching (content lives 1 hour,
  reduces cost on repeated calls). We leave a clear hook for it here.
  Don't implement it now — get things working first.
"""

import logging
from typing import Any
import anthropic
from config.settings import settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """
    Wrapper around the Anthropic SDK.
    Agents use this — never import anthropic directly in agent files.
    """

    def __init__(self) -> None:
        # NEVER pass the API key anywhere else in the codebase
        # It lives only here, read from settings
        self._client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        logger.info(
            "ClaudeClient initialised",
            extra={"component": "ClaudeClient"}
        )

    def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        model: str | None = None,
        max_tokens: int = 1000,
        tools: list[dict] | None = None,
        temperature: float = 1.0,
    ) -> anthropic.types.Message:
        """
        Send a message to Claude and get a response.

        IMPORTANT FROM YOUR NOTES:
          - Never pass system=None — it raises an API error
          - We conditionally include system only when provided
          - Claude does NOT store history — you pass the full
            messages list every single time

        Args:
            messages: Full conversation history. You manage this.
            system:   The system prompt. Optional but recommended.
            model:    Override the default model for this call.
            max_tokens: Safety net — Claude generates what it thinks
                        is right and cuts at this threshold.
            tools:    List of tool schemas if this call needs tools.
            temperature: 0=deterministic, 1=creative. Use low values
                         for analysis agents, higher for report writing.
        """
        chosen_model = model or settings.CLAUDE_ORCHESTRATOR_MODEL

        # Build params dict — only include optional fields when present
        # This is the pattern your notes show for system=None safety
        params: dict[str, Any] = {
            "model": chosen_model,
            "max_tokens": max_tokens,
            "messages": messages,
            "temperature": temperature,
        }

        # CRITICAL: Only add system if it's actually provided
        if system:
            params["system"] = system

        # Only add tools if this call needs them
        if tools:
            params["tools"] = tools

        logger.info(
            "Calling Claude",
            extra={
                "component": "ClaudeClient",
                "model": chosen_model,
                "message_count": len(messages),
                "has_tools": bool(tools),
            }
        )

        response = self._client.messages.create(**params)
        return response

    def extract_text(self, response: anthropic.types.Message) -> str:
        """
        Pull just the text from a Claude response.

        WHY THIS EXISTS:
          Claude returns a list of content blocks. Some are text,
          some are tool_use. This helper extracts only the text.
          Your notes explain this multi-block structure in detail.
        """
        text_parts = [
            block.text
            for block in response.content
            if block.type == "text"
        ]
        return "\n".join(text_parts)

    def has_tool_use(self, response: anthropic.types.Message) -> bool:
        """Check if Claude wants to call a tool."""
        return any(block.type == "tool_use" for block in response.content)

    def get_tool_calls(
        self, response: anthropic.types.Message
    ) -> list[anthropic.types.ToolUseBlock]:
        """
        Extract all tool use blocks from a response.

        Claude can request MULTIPLE tool calls in one response.
        Your notes cover this — you must handle each one and
        match results back by tool_use_id.
        """
        return [
            block
            for block in response.content
            if block.type == "tool_use"
        ]


# Single shared instance — import this everywhere
claude_client = ClaudeClient()