"""PlainTextRenderer — format CommandResult as plain text with budget."""

from __future__ import annotations

import json

from biome_mcp.models.result import CommandResult, CommandStatus
from biome_mcp.render.profiles import DEFAULT, RenderProfile


class PlainTextRenderer:
    def __init__(self, profile: RenderProfile = DEFAULT) -> None:
        self._profile = profile

    @property
    def profile(self) -> RenderProfile:
        return self._profile

    def render(self, result: CommandResult) -> str:
        parts: list[str] = []
        if self._profile.include_status and result.status != CommandStatus.OK:
            parts.append(f"[{result.status}]")
        parts.append(result.text)
        if self._profile.include_data and result.data is not None:
            parts.append(json.dumps(result.data, default=str, ensure_ascii=False))
        if result.error_code:
            parts.append(f"(error: {result.error_code})")
        text = " ".join(parts)
        return self._apply_budget(text)

    def render_batch(self, results: list[CommandResult]) -> str:
        lines = [self.render(r) for r in results]
        text = "\n".join(lines)
        return self._apply_budget(text)

    def _apply_budget(self, text: str) -> str:
        limit = self._profile.max_chars
        if len(text) <= limit:
            return text
        suffix = self._profile.truncation_suffix
        return text[: limit - len(suffix)] + suffix
