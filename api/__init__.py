"""NVIDIA NIM API client — streaming and non-streaming chat completions."""
import json
import re
import time
from typing import List, Dict, Any, Generator, Optional

import requests

class NVIDIAAgent:
    """API client for NVIDIA NIM chat completions with model fallback."""

    def __init__(self, api_key: str, models: List[str], timeout: int = 45):
        self.api_key = api_key
        self.models = models
        self.timeout = timeout
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
                "Content-Type": "application/json"
            }

            for _ in range(3):
                try:
                    r = self.session.post(
                        "https://integrate.api.nvidia.com/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=(15, self.timeout)
                    )

                    if r.status_code == 429:
                        time.sleep(0.5)
                        continue

                    if r.status_code != 200:
                        break

                    self.last_model_idx = idx
                    return self._extract_content(r.json())

                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                    time.sleep(0.3)
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
                "Content-Type": "application/json"
            }

            for _ in range(2):
                try:
                    r = self.session.post(
                        "https://integrate.api.nvidia.com/v1/chat/completions",
                        headers=headers,
                        json=payload,
                        timeout=(15, self.timeout),
                        stream=True
                    )

                    if r.status_code == 429:
                        time.sleep(0.5)
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
                                        yield self._clean_text(content)
                            except json.JSONDecodeError:
                                pass
                    return

                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError):
                    time.sleep(0.3)
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
