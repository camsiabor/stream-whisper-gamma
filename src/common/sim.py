import datetime


def get(cfg, default=None, *keys):
    value = cfg
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            value = default
            break
    if value is None:
        value = default
    return value


def insert_newline_per(text: str, max_len: int = 10) -> str:
    words = text.split()
    new_text = ""
    for i, word in enumerate(words):
        new_text += word + " "
        if (i + 1) % max_len == 0:
            new_text += "\n"
    return new_text


def datetime_str() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
