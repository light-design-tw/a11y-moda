"""OpenAI-compatible LLM client with on-disk cache.

Works with: OpenAI, Anthropic (compat endpoint), OpenRouter, Together, Groq,
Ollama, vLLM, LM Studio, llama.cpp server, etc. — anything that exposes
`/v1/chat/completions`.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx


# 64×64 white PNG — small enough to be cheap, large enough that VL models with
# image-resize preprocessing (e.g. Qwen-VL) don't choke on degenerate inputs.
_PROBE_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAIAAAAlC+aJAAAAXklEQVR4nO3PMQ0AMAzAsPInvYLY"
    "YVWKESTzjhsd8KsBrQGtAa0BrQGtAa0BrQGtAa0BrQGtAa0BrQGtAa0BrQGtAa0BrQGtAa0BrQGt"
    "Aa0BrQGtAa0BrQGtAa0BbQHKU9LC7/CP1AAAAABJRU5ErkJggg=="
)


_DEFAULT_TIMEOUT = 60.0
_DEFAULT_CACHE_DIR = Path.home() / ".cache" / "a11y-moda" / "llm"


@dataclass
class LLMConfig:
    base_url: str
    api_key: str
    model: str
    timeout: float = _DEFAULT_TIMEOUT
    cache_dir: Path = field(default_factory=lambda: _DEFAULT_CACHE_DIR)
    cache_enabled: bool = True
    max_retries: int = 2

    @classmethod
    def from_env(cls) -> "LLMConfig | None":
        base_url = os.environ.get("A11Y_LLM_BASE_URL") or os.environ.get("OPENAI_BASE_URL")
        api_key = os.environ.get("A11Y_LLM_KEY") or os.environ.get("OPENAI_API_KEY") or "sk-noauth"
        model = os.environ.get("A11Y_LLM_MODEL") or os.environ.get("OPENAI_MODEL")
        if not base_url or not model:
            return None
        return cls(base_url=base_url, api_key=api_key, model=model)


class LLMClient:
    def __init__(self, config: LLMConfig):
        self.cfg = config
        self._call_count = 0
        self._cache_hits = 0
        self._vision_capable: bool | None = None  # lazy-probed
        if config.cache_enabled:
            config.cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def stats(self) -> dict:
        return {
            "calls": self._call_count,
            "cache_hits": self._cache_hits,
            "model": self.cfg.model,
            "vision": self._vision_capable,
        }

    def supports_vision(self) -> bool:
        """Probe once per (base_url, model). Result cached on disk."""
        if self._vision_capable is not None:
            return self._vision_capable
        cache_path = self.cfg.cache_dir / "_vision_capability.json"
        cache_key = f"{self.cfg.base_url}|{self.cfg.model}"
        try:
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            if cache_key in cached:
                self._vision_capable = bool(cached[cache_key])
                return self._vision_capable
        except Exception:
            cached = {}
        # Probe with a 64×64 PNG. Use generous max_tokens — thinking models
        # (Gemini 2.5/3.x Pro, Claude Opus, etc.) need headroom to emit any content.
        try:
            self._call_with_image(
                "Reply only with the word 'ok'.",
                "describe",
                f"data:image/png;base64,{_PROBE_PNG_B64}",
                max_tokens=2048,
            )
            self._vision_capable = True
        except Exception:
            self._vision_capable = False
        cached[cache_key] = self._vision_capable
        try:
            cache_path.write_text(json.dumps(cached, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass
        return self._vision_capable

    _LANG_PREFIX = (
        "【最高優先指令】無論 user 訊息使用何種語言，"
        "你的整個回覆必須【全部使用繁體中文（zh-TW）】。"
        "禁止使用簡體字（无、对、户、说、与、个、为、来、过、级、问、题）。"
        "禁止整段使用英文回覆。專有名詞 / 程式碼 / HTML 標籤可保留原文。\n\n"
    )

    def judge(self, system: str, user: str, *, max_tokens: int = 200, temperature: float = 0.0) -> str:
        # Always prefix the language directive — guarantees Traditional Chinese output
        # regardless of how each rule's SYSTEM prompt was authored.
        system = self._LANG_PREFIX + system
        cache_key = self._cache_key(system, user, max_tokens, temperature)
        cached = self._cache_read(cache_key)
        if cached is not None:
            self._cache_hits += 1
            return cached

        last_err: Exception | None = None
        for attempt in range(self.cfg.max_retries + 1):
            try:
                content = self._call(system, user, max_tokens, temperature)
                self._call_count += 1
                self._cache_write(cache_key, content)
                return content
            except Exception as e:
                last_err = e
                if attempt < self.cfg.max_retries:
                    time.sleep(1.5 ** attempt)
        raise RuntimeError(f"LLM call failed after retries: {last_err}")

    def _call(self, system: str, user: str, max_tokens: int, temperature: float) -> str:
        url = f"{self.cfg.base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.cfg.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        return self._post(url, payload)

    def _call_with_image(self, system: str, user: str, image_url: str, *,
                          max_tokens: int = 200, temperature: float = 0.0) -> str:
        url = f"{self.cfg.base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": self.cfg.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": [
                    {"type": "text", "text": user},
                    {"type": "image_url", "image_url": {"url": image_url}},
                ]},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        return self._post(url, payload)

    def _post(self, url: str, payload: dict) -> str:
        headers = {"Content-Type": "application/json"}
        if self.cfg.api_key and self.cfg.api_key != "sk-noauth":
            headers["Authorization"] = f"Bearer {self.cfg.api_key}"
        with httpx.Client(timeout=self.cfg.timeout) as cli:
            r = cli.post(url, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()
        # Gemini "thinking" models can return a message with no `content`
        # when reasoning tokens consume the budget. Treat as empty + report finish_reason.
        try:
            choice = data["choices"][0]
            msg = choice.get("message") or {}
            content = msg.get("content")
            if content is None:
                finish = choice.get("finish_reason", "unknown")
                raise RuntimeError(f"empty content (finish_reason={finish}, raise max_tokens?)")
            return content
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"unexpected response shape: {e}; body={str(data)[:200]}")

    def judge_with_image(self, system: str, user: str, image_data: bytes | str, *,
                          max_tokens: int = 200, temperature: float = 0.0) -> str:
        """Vision call. image_data accepts raw bytes (PNG/JPEG) or full data: URL string."""
        if isinstance(image_data, bytes):
            b64 = base64.b64encode(image_data).decode("ascii")
            image_url = f"data:image/png;base64,{b64}"
        else:
            image_url = image_data
        cache_key = self._cache_key(self._LANG_PREFIX + system, user, max_tokens, temperature, image_url[-200:])
        cached = self._cache_read(cache_key)
        if cached is not None:
            self._cache_hits += 1
            return cached
        last_err: Exception | None = None
        for attempt in range(self.cfg.max_retries + 1):
            try:
                content = self._call_with_image(self._LANG_PREFIX + system, user, image_url,
                                                  max_tokens=max_tokens, temperature=temperature)
                self._call_count += 1
                self._cache_write(cache_key, content)
                return content
            except Exception as e:
                last_err = e
                if attempt < self.cfg.max_retries:
                    time.sleep(1.5 ** attempt)
        raise RuntimeError(f"LLM vision call failed after retries: {last_err}")

    def _cache_key(self, *parts: Any) -> str:
        h = hashlib.sha256()
        h.update(self.cfg.model.encode())
        for p in parts:
            h.update(b"\0")
            h.update(str(p).encode("utf-8"))
        return h.hexdigest()

    def _cache_read(self, key: str) -> str | None:
        if not self.cfg.cache_enabled:
            return None
        path = self.cfg.cache_dir / f"{key}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))["content"]
        except Exception:
            return None

    def _cache_write(self, key: str, content: str) -> None:
        if not self.cfg.cache_enabled:
            return
        path = self.cfg.cache_dir / f"{key}.json"
        try:
            path.write_text(json.dumps({"content": content}, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


# Common simplified-Chinese chars Qwen sometimes emits — map to Traditional.
_S2T = str.maketrans(
    "无图标线对应说图认为发会显户经济业产体头颜对错给计较实让让议确确该应应该问题题这这种种该该种该让让让说说说会会户户户体体体颜颜颜对对对错錯給給給計計實實讓讓議議確確該該應應該應問問題題種種種該該該該讓讓讓",
    "無圖標線對應說圖認為發會顯戶經濟業產體頭顏對錯給計較實讓讓議確確該應應該問題題這這種種該該種該讓讓讓說說說會會戶戶戶體體體顏顏顏對對對錯錯給給給計計實實讓讓議議確確該該應應該應問問題題種種種該該該該讓讓讓",
)


def to_traditional(s: str) -> str:
    """Best-effort simplified→traditional normalisation for LLM output."""
    return s.translate(_S2T)


def parse_verdict(text: str) -> tuple[str, str]:
    """Extract structured verdict from LLM response, normalising to Traditional Chinese.

    Expected format:
      VERDICT: pass|fail|unsure
      REASON: <short reason>

    Falls back to keyword sniffing when the model ignores the schema.
    """
    verdict = "unsure"
    reason = text.strip()
    for line in text.splitlines():
        s = line.strip()
        low = s.lower()
        if low.startswith("verdict:"):
            v = low.split(":", 1)[1].strip()
            if "fail" in v:
                verdict = "fail"
            elif "pass" in v:
                verdict = "pass"
            elif "unsure" in v or "n/a" in v:
                verdict = "unsure"
        elif low.startswith("reason:"):
            reason = s.split(":", 1)[1].strip()
    if verdict == "unsure":
        low = text.lower()
        if "fail" in low and "pass" not in low:
            verdict = "fail"
        elif "pass" in low and "fail" not in low:
            verdict = "pass"
    return verdict, to_traditional(reason)
