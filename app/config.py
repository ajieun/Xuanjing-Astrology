"""本地设置持久化。"""
import json
import os

from .resources import user_dir

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-chat"
DEFAULT_TIMEOUT = 180

CONFIG_FILE = "settings.json"


def config_path():
    return os.path.join(user_dir(), CONFIG_FILE)


def default_settings():
    return {
        "api_key": "",
        "base_url": DEFAULT_BASE_URL,
        "model": DEFAULT_MODEL,
        "temperature": 0.85,
        "max_tokens": 4096,
        "timeout": DEFAULT_TIMEOUT,
    }


def load():
    data = default_settings()
    try:
        with open(config_path(), "r", encoding="utf-8") as handle:
            saved = json.load(handle)
        if isinstance(saved, dict):
            data.update({k: v for k, v in saved.items() if k in data})
    except (OSError, ValueError):
        pass
    return data


def save(settings):
    payload = default_settings()
    payload.update(settings or {})
    path = config_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    return payload


def has_key(settings=None):
    data = settings or load()
    return bool(str(data.get("api_key", "")).strip())
