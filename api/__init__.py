"""OpenAI-compatible chat completion client with model fallback."""
import json
import re
import time
from typing import List, Dict, Any, Generator, Optional

import requests

class NVIDIAAgent:
    """API client for OpenAI-compatible chat completions with model fallback."""

    def __init__(self, api_key: str, models: List[str], timeout: int = 45,
                 base_url: str = None, extra_headers: dict = None):
        self.api_key = api_key
        self.models = models
        self.timeout = timeout
        self.base_url = base_url or "https://integrate.api.nvidia.com/v1/chat/completions"
        self.extra_headers = extra_headers or {}
        self.session = requests.Session()
        self.last_model_idx = 0

    def generate_response(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None) -> str:
        if max_tokens is None:
            max_tokens = self._guess_tokens(messages)

        model_list = self.models
        model_idx = self.last_model_idx

        for mi in range(len(model_list)):
            idx = (model_idx + mi) % len(model_list)
            model = model_list[idx]
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.5,
                "top_p": 0.95,
                "stream": False
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
                "Content-Type": "application/json",
                **self.extra_headers
            }

            try:
                r = self.session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=(15, self.timeout)
                )

                if r.status_code == 429:
                    continue

                if r.status_code != 200:
                    continue

                self.last_model_idx = idx
                return self._extract_content(r.json())

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                continue
            except Exception as e:
                    # Sanitize error to prevent API key leak
                    err_str = str(e)
                    if self.api_key and self.api_key in err_str:
                        err_str = err_str.replace(self.api_key, "[REDACTED]")
                    return f"API Error: {err_str}"

        return "All models failed"

    def generate_stream(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None) -> Generator[str, None, None]:
        if max_tokens is None:
            max_tokens = self._guess_tokens(messages)

        model_list = self.models
        model_idx = self.last_model_idx

        for mi in range(len(model_list)):
            idx = (model_idx + mi) % len(model_list)
            model = model_list[idx]
            payload = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.5,
                "top_p": 0.95,
                "stream": True
            }

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "text/event-stream",
                "Content-Type": "application/json",
                **self.extra_headers
            }

            try:
                r = self.session.post(
                    self.base_url,
                    headers=headers,
                    json=payload,
                    timeout=(15, self.timeout),
                    stream=True
                )

                if r.status_code == 429:
                    continue

                if r.status_code != 200:
                    # Don't leak sensitive response data
                    yield f"API Error {r.status_code}"
                    return

                self.last_model_idx = idx

                for line in r.iter_lines(decode_unicode=True):
                    if line is None or not line:
                        continue
                    if line.startswith('data: '):
                        data = line[6:]
                        if data == '[DONE]':
                            return
                        try:
                            chunk = json.loads(data)
                            choices = chunk.get('choices')
                            if choices and len(choices) > 0:
                                delta = choices[0].get('delta', {})
                                content = delta.get('content', '')
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            pass
                return

            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                continue
            except Exception as e:
                # Sanitize error to prevent API key leak
                err_str = str(e)
                if self.api_key and self.api_key in err_str:
                    err_str = err_str.replace(self.api_key, "[REDACTED]")
                yield f"Error: {err_str}"
                return

        yield "All models failed"

    def _guess_tokens(self, messages: List[Dict[str, str]]) -> int:
        total = sum(len(m.get("content", "")) for m in messages if m.get("role") == "user")
        combined = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")
        code_kw = ["create", "build", "write", "make", "app", "code", "file",
                   "implement", "generate", "script", "program", "project"]
        is_code = any(kw in combined.lower() for kw in code_kw)

        if is_code:
            if total < 100:
                return 4096
            if total < 500:
                return 8192
            return 16384

        if total < 100:
            return 4096
        if total < 500:
            return 8192
        return 16384

    def _extract_content(self, data: Dict[str, Any]) -> str:
        msg = data.get("choices", [{}])[0].get("message", {})
        c = msg.get("content")
        if c:
            return self._clean_text(c)
        r = msg.get("reasoning") or msg.get("reasoning_content")
        return self._clean_text(r or str(data)[:200])

    def _clean_text(self, text: str) -> str:
        text = self._strip_reasoning(text)
        if not text:
            return text

        lines = text.split('\n')

        # For coding responses: extract ONLY directive blocks, strip narrative
        directive_blocks: List[str] = []
        current_block: List[str] = []
        in_directive = False

        for line in lines:
            stripped = line.strip()
            # Remove <code> and </code> tags
            stripped = re.sub(r'</?code>', '', stripped).strip()

            if stripped.startswith('WRITE:') or stripped.startswith('EXECUTE:'):
                if in_directive and current_block:
                    directive_blocks.append('\n'.join(current_block))
                in_directive = True
                current_block = [line]
            elif in_directive:
                # Skip code fences
                if stripped in ('```', '~~~', '`') or stripped.startswith('```'):
                    continue
                # Stop at next directive
                if stripped.startswith('WRITE:') or stripped.startswith('EXECUTE:'):
                    if current_block:
                        directive_blocks.append('\n'.join(current_block))
                    current_block = [line]
                    continue
                current_block.append(line)

        if in_directive and current_block:
            directive_blocks.append('\n'.join(current_block))

        # If we found directives, return only directive blocks
        if directive_blocks:
            return '\n'.join(directive_blocks)

        # Fallback for non-coding responses: clean markdown
        text = '\n'.join(lines)
        text = re.sub(r'(?<!\*)\*(?!\*)(.*?)(?<!\*)\*(?!\*)', r'\1', text)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^-{3,}$', '', text, flags=re.MULTILINE)
        text = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', text)
        text = re.sub(r'^>\s+', '', text, flags=re.MULTILINE)
        # Only strip pipes that are NOT in EXECUTE: commands
        result_lines = []
        for line in text.split('\n'):
            if line.strip().startswith('EXECUTE:'):
                result_lines.append(line)
            else:
                result_lines.append(re.sub(r'\|', ' ', line))
        text = '\n'.join(result_lines)
        text = re.sub(r'  +', ' ', text)
        text = re.sub(r'\n{3,}', '\n\n', text)
        return text.strip()

    def _strip_reasoning(self, text: str) -> str:
        lower = text.lower()
        if not any(p in lower for p in ('wait,', 'let me', 'oh right', "that's", "first let's", "first step should", 'make sure')):
            return text

        lines = text.split('\n')
        split_markers = ('wait', 'let me', 'oh right', 'okay, let', 'now let')
        segments: List[List[str]] = []
        current: List[str] = []

        for line in lines:
            lower = line.strip().lower()
            is_marker = any(lower.startswith(m) for m in split_markers)
            if is_marker and current:
                segments.append(current)
                current = [line]
            else:
                current.append(line)

        if current:
            segments.append(current)

        best = segments[-1] if segments else lines
        skip_start = ('got ', 'let ', 'first,', 'first step', 'second step', 'third step',
                      'wait,', 'okay,', "i'll", "let's", 'hmm,', 'oh ', 'make sure',
                      'then,', 'first,', 'now let', 'also,')
        result = []
        started = False

        for line in best:
            lower = line.strip().lower()
            if not started:
                if not line.strip():
                    continue
                if any(lower.startswith(s) for s in skip_start):
                    continue
                started = True
            if lower.startswith(('wait,', 'let me', 'oh right', "that's", 'make sure', 'also, from an')):
                break
            result.append(line)

        return '\n'.join(result).strip()


class OpenRouterAgent(NVIDIAAgent):
    """OpenRouter API client — uses OpenAI-compatible format."""

    BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, models: List[str], timeout: int = 45):
        super().__init__(
            api_key=api_key,
            models=models,
            timeout=timeout,
            base_url=self.BASE_URL,
            extra_headers={
                "HTTP-Referer": "https://github.com/terminal-AI-Agent-2",
                "X-Title": "Tell AI Agent",
            }
        )


PROVIDER_REGISTRY = {
    "nvidia": {
        "class": NVIDIAAgent,
        "env_key": "NVIDIA_API_KEY",
        "env_model": "NVIDIA_MODEL",
        "default_models": ["meta/llama-3.1-8b-instruct", "deepseek-ai/deepseek-v4-pro", "mistralai/mistral-small-4-119b-2603"],
    },
    "openrouter": {
        "class": OpenRouterAgent,
        "env_key": "OPENROUTER_API_KEY",
        "env_model": "OPENROUTER_MODEL",
        "default_models": [
            "openrouter/owl-alpha",
            "google/lyria-3-pro-preview",
            "google/lyria-3-clip-preview",
            "qwen/qwen3-coder:free",
            "nvidia/nemotron-3-ultra-550b-a55b:free",
            "nvidia/nemotron-3-super-120b-a12b:free",
            "nex-agi/nex-n2-pro:free",
            "poolside/laguna-xs.2:free",
            "poolside/laguna-m.1:free",
            "google/gemma-4-26b-a4b-it:free",
            "google/gemma-4-31b-it:free",
            "qwen/qwen3-next-80b-a3b-instruct:free",
            "cohere/north-mini-code:free",
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free",
            "nvidia/nemotron-3-nano-30b-a3b:free",
            "openai/gpt-oss-120b:free",
            "openai/gpt-oss-20b:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "meta-llama/llama-3.2-3b-instruct:free",
            "nousresearch/hermes-3-llama-3.1-405b:free",
            "nvidia/nemotron-3.5-content-safety:free",
            "nvidia/nemotron-nano-12b-v2-vl:free",
            "nvidia/nemotron-nano-9b-v2:free",
            "liquid/lfm-2.5-1.2b-thinking:free",
            "liquid/lfm-2.5-1.2b-instruct:free",
            "cognitivecomputations/dolphin-mistral-24b-venice-edition:free",
        ],
    },
}


def create_agent(provider: str, api_key: str, models: List[str], timeout: int = 45):
    """Factory: create the right agent for a given provider name."""
    provider = provider.lower()
    if provider not in PROVIDER_REGISTRY:
        raise ValueError(
            f"Unknown provider '{provider}'. "
            f"Supported: {list(PROVIDER_REGISTRY.keys())}"
        )
    cls = PROVIDER_REGISTRY[provider]["class"]
    return cls(api_key=api_key, models=models, timeout=timeout)


_MULTI_FAIL_PREFIXES = ("All models", "All providers", "API Error", "Error:")


class MultiProviderAgent:
    """Agent that tries models from multiple providers in order."""

    def __init__(self, providers: List[Dict[str, Any]], timeout: int = 45):
        self.providers = []
        for p in providers:
            cls = p["class"]
            self.providers.append(
                cls(api_key=p["api_key"], models=p["models"], timeout=p.get("timeout", timeout))
            )

    def generate_response(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None) -> str:
        for agent in self.providers:
            resp = agent.generate_response(messages, max_tokens=max_tokens)
            if resp and not resp.startswith(_MULTI_FAIL_PREFIXES):
                return resp
        return "All providers failed"

    def generate_stream(self, messages: List[Dict[str, str]], max_tokens: Optional[int] = None):
        for agent in self.providers:
            got = False
            for chunk in agent.generate_stream(messages, max_tokens=max_tokens):
                if chunk and not chunk.startswith(_MULTI_FAIL_PREFIXES):
                    got = True
                    yield chunk
            if got:
                return
        yield "All providers failed"
