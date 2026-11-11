"""本地设置持久化。"""
import json
import os

from .resources import user_dir

DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
DEFAULT_MODEL = "deepseek-v4-pro"
DEFAULT_TIMEOUT = 180

# 旧版本把 deepseek-chat 当作默认模型；升级后一次性换成 v4-pro，
# 用户在设置里手动选的模型不会被再次覆盖。
MODEL_SCHEME = 2
LEGACY_MODELS = {"", "deepseek-chat"}

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
        "model_scheme": MODEL_SCHEME,
    }


def load():
    data = default_settings()
    try:
        with open(config_path(), "r", encoding="utf-8") as handle:
            saved = json.load(handle)
    except (OSError, ValueError):
        return data
    if not isinstance(saved, dict) or not saved:
        return data

    data.update({k: v for k, v in saved.items() if k in data})

    if int(saved.get("model_scheme", 1) or 1) < MODEL_SCHEME:
        if str(saved.get("model", "")).strip() in LEGACY_MODELS:
            data["model"] = DEFAULT_MODEL
        data["model_scheme"] = MODEL_SCHEME
        save(data)
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
