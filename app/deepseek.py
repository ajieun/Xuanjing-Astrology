"""DeepSeek（OpenAI 兼容）对话接口客户端。

使用标准库实现，避免额外依赖；请求在主线程之外的工作线程中发起。
"""
import json
import ssl
import urllib.error
import urllib.request

from .config import DEFAULT_BASE_URL, DEFAULT_MODEL, DEFAULT_TIMEOUT


class DeepSeekError(Exception):
    pass


def chat_url(base_url):
    root = str(base_url or DEFAULT_BASE_URL).strip().rstrip("/")
    if root.endswith("/chat/completions"):
        return root
    return f"{root}/chat/completions"


def _extract_message(text):
    try:
        payload = json.loads(text)
    except ValueError as exc:
        raise DeepSeekError(f"接口返回内容无法解析：{text[:200]}") from exc
    choices = payload.get("choices") or []
    if not choices:
        raise DeepSeekError(f"接口未返回内容：{text[:200]}")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not content:
        raise DeepSeekError(f"接口返回空消息：{text[:200]}")
    return content, payload.get("usage")


def chat(messages, settings, timeout=None):
    """发起一次对话，返回 (content, usage)。"""
    api_key = str(settings.get("api_key", "")).strip()
    if not api_key:
        raise DeepSeekError("还没有填写 DeepSeek API Key，请先在设置中填写。")
    if not messages:
        raise DeepSeekError("请求内容为空。")

    payload = json.dumps(
        {
            "model": settings.get("model") or DEFAULT_MODEL,
            "messages": messages,
            "temperature": float(settings.get("temperature", 0.85)),
            "max_tokens": int(settings.get("max_tokens", 4096)),
            "stream": False,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        chat_url(settings.get("base_url")),
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="POST",
    )

    context = ssl.create_default_context()
    deadline = timeout or int(settings.get("timeout", DEFAULT_TIMEOUT) or DEFAULT_TIMEOUT)

    try:
        with urllib.request.urlopen(request, timeout=deadline, context=context) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        detail = body
        try:
            parsed = json.loads(body)
            detail = (parsed.get("error") or {}).get("message") or parsed.get("message") or body
        except ValueError:
            pass
        raise DeepSeekError(f"接口返回 {exc.code}：{str(detail)[:300]}") from exc
    except urllib.error.URLError as exc:
        raise DeepSeekError(f"网络请求失败：{exc.reason}") from exc
    except TimeoutError as exc:
        raise DeepSeekError("请求超时，请稍后重试。") from exc

    return _extract_message(raw)


def test_connection(settings):
    content, _ = chat(
        [{"role": "user", "content": "回复两个字：可用"}],
        {**settings, "max_tokens": 32, "temperature": 0.1},
        timeout=60,
    )
    return content.strip()[:60] or "已连通"


def extract_json(text):
    """从模型输出中提取 JSON（兼容 ```json 代码块）。"""
    raw = (text or "").strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    try:
        return json.loads(raw)
    except ValueError:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(raw[start:end + 1])
            except ValueError as exc:
                raise DeepSeekError(f"模型返回的内容不是合法 JSON：{raw[:200]}") from exc
        raise DeepSeekError(f"模型没有返回 JSON：{raw[:200]}")
