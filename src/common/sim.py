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


def text_with_return(text: str, splitter=" ", max_len: int = 10) -> str:
    if text is None or len(text) <= 0:
        return ""
    words = text.split(splitter)
    if len(words) <= max_len:
        return text
    new_string = ""
    for i, word in enumerate(words, 1):
        new_string += word + splitter
        if i % max_len == 0:
            new_string += "\n"
    return new_string


def datetime_str() -> str:
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
