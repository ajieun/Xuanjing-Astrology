"""DeepSeek（OpenAI 兼容）对话接口客户端。

使用标准库实现，避免额外依赖；请求在主线程之外的工作线程中发起。

约定：解读类请求一律要求模型返回 JSON，但界面只展示人话——
任何情况下都不把 JSON 原文直接丢给用户，见 `as_text`。
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


def strip_fence(text):
    """去掉模型偶尔加上的 ```json 围栏。"""
    raw = (text or "").strip()
    if raw.startswith("```"):
        lines = raw.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        raw = "\n".join(lines).strip()
    return raw


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


class _HttpFailure(Exception):
    def __init__(self, code, detail):
        super().__init__(detail)
        self.code = code


def _post(payload, api_key, settings, deadline):
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        chat_url(settings.get("base_url")),
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        },
        method="POST",
    )

    context = ssl.create_default_context()
    try:
        with urllib.request.urlopen(request, timeout=deadline, context=context) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="replace")
        detail = text
        try:
            parsed = json.loads(text)
            detail = (parsed.get("error") or {}).get("message") or parsed.get("message") or text
        except ValueError:
            pass
        raise _HttpFailure(exc.code, f"接口返回 {exc.code}：{str(detail)[:300]}") from exc
    except urllib.error.URLError as exc:
        raise DeepSeekError(f"网络请求失败：{exc.reason}") from exc
    except TimeoutError as exc:
        raise DeepSeekError("请求超时，请稍后重试。") from exc


def chat(messages, settings, timeout=None, json_mode=False):
    """发起一次对话，返回 (content, usage)。

    json_mode=True 时要求接口以 JSON 对象作答，显著降低格式跑偏的概率；
    若第三方兼容接口不支持 response_format，会自动去掉该参数重试一次。
    """
    api_key = str(settings.get("api_key", "")).strip()
    if not api_key:
        raise DeepSeekError("还没有填写 DeepSeek API Key，请先在设置中填写。")
    if not messages:
        raise DeepSeekError("请求内容为空。")

    payload = {
        "model": settings.get("model") or DEFAULT_MODEL,
        "messages": messages,
        "temperature": float(settings.get("temperature", 0.85)),
        "max_tokens": int(settings.get("max_tokens", 4096)),
        "stream": False,
    }
    if json_mode and settings.get("json_mode", True):
        payload["response_format"] = {"type": "json_object"}

    deadline = timeout or int(settings.get("timeout", DEFAULT_TIMEOUT) or DEFAULT_TIMEOUT)

    try:
        raw = _post(payload, api_key, settings, deadline)
    except _HttpFailure as exc:
        if exc.code == 400 and "response_format" in payload:
            payload.pop("response_format")
            raw = _post(payload, api_key, settings, deadline)
        else:
            raise DeepSeekError(str(exc)) from exc

    return _extract_message(raw)


def test_connection(settings):
    content, _ = chat(
        [{"role": "user", "content": "回复两个字：可用"}],
        {**settings, "max_tokens": 32, "temperature": 0.1},
        timeout=60,
    )
    return content.strip()[:60] or "已连通"


def extract_json(text):
    """从模型输出中提取 JSON 对象；失败时给出可读提示，绝不回传原文。"""
    raw = strip_fence(text)
    data = None
    try:
        data = json.loads(raw)
    except ValueError:
        start, end = raw.find("{"), raw.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(raw[start:end + 1])
            except ValueError:
                data = None
    if not isinstance(data, (dict, list)):
        raise DeepSeekError("模型这次没有按格式返回解读内容，请再点一次重试。")
    return data


# 字段名 -> 中文标签，用于把结构化结果压成可读文本时的兜底
_LABELS = {
    "overall": "总断",
    "summary": "总述",
    "current_decadal_display": "当前大限",
    "cards": "解读",
    "cards_reading": "牌面解读",
    "sections": "分节",
    "title": "标题",
    "badge": "标签",
    "body": "正文",
    "reading": "解读",
    "position": "牌位",
    "card": "牌",
    "lines_reading": "爻辞白话",
    "actions": "宜",
    "cautions": "忌",
    "advice": "建议",
    "timing": "时机",
    "text": "问题",
    "hint": "提示",
    "calibration_questions": "校准问题",
}

# 纯展示参数，不参与转文本
_SKIP_KEYS = {"pct", "full", "highlight", "teal", "probabilities", "confidence"}


def as_text(value):
    """把任意模型返回值压平成可读中文。

    - 字符串若本身是 JSON（模型把结构塞进了正文），先解析再压平；
    - dict / list 按字段转成「标签：内容」的段落；
    - 结果里不会出现大括号、键值对符号，界面可安全渲染。
    """
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        raw = value.strip()
        if raw[:1] in "{[":
            try:
                return as_text(json.loads(raw))
            except ValueError:
                pass
        return strip_fence(raw)
    if isinstance(value, (list, tuple)):
        lines = [as_text(item) for item in value]
        return "\n".join(f"- {line}" for line in lines if line)
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if key in _SKIP_KEYS:
                continue
            text = as_text(item)
            if not text:
                continue
            label = _LABELS.get(key, "")
            if isinstance(item, (dict, list)):
                parts.append(f"{label}：\n{text}" if label else text)
            else:
                parts.append(f"{label}：{text}" if label else text)
        return "\n\n".join(parts)
    return str(value)
