import datetime
import os


# get / set / clone =============================================================================== #

def getv(cfg: dict, default=None, *keys):
    value = cfg
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return default
    if value is None:
        return default
    return value


def setv(target: dict, value, *keys):
    current = target
    paths = keys[:-1]
    for key in paths:
        if key in current and isinstance(current[key], dict):
            current = current[key]
        else:
            current[key] = {}
            current = current[key]
    last = keys[-1]
    current[last] = value
    return current


def clonev(src: dict, des: dict, default=None, *keys):
    if not keys:
        return

    current_src = src
    current_des = des

    paths = keys[:-1]
    for key in paths:
        if key in current_src and isinstance(current_src[key], dict):
            current_src = current_src[key]
            if key not in current_des:
                current_des[key] = {}
            current_des = current_des[key]
        else:
            return setv(current_des, default, *keys)

    last_key = keys[-1]
    if last_key in current_src:
        value = current_src[last_key]
        if value is not None:
            current_des[last_key] = value
        else:
            current_des[last_key] = default

    return current_des


# Text =============================================================================== #

class Text:

    @staticmethod
    def insert_newline_per(text: str, max_len: int = 10) -> str:
        words = text.split()
        new_text = ""
        for i, word in enumerate(words):
            new_text += word + " "
            if (i + 1) % max_len == 0:
                new_text += "\n"
        return new_text


# Time =============================================================================== #

class Time:
    @staticmethod
    def datetime_str() -> str:
        return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]


# Collection =============================================================================== #
class Collection:
    @staticmethod
    def insort_ex(container, unit, low=0, high=None, right=True, key=lambda item: item):
        if high is None:
            high = len(container)
        value_unit = key(unit)
        while low < high:
            mid = (low + high) // 2
            unit_mid = container[mid]
            value_mid = key(unit_mid)
            if (value_mid < value_unit) if right else (value_mid > value_unit):
                low = mid + 1
            else:
                high = mid
        container.insert(low, unit)


# FileIO =============================================================================== #
class FileIO:

    @staticmethod
    def open(file_path, encoding='utf-8', mkdir=True):
        if mkdir:
            parent_directory = os.path.dirname(file_path)
            os.makedirs(parent_directory, exist_ok=True)
        file = open(file_path, 'a', encoding=encoding)
        return file
