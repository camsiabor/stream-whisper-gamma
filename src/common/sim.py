import datetime
import logging
import os

import yaml


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


# Reflection =============================================================================== #
class Reflector:

    @staticmethod
    def from_dict(obj: object, data: dict):
        primitive_types = (int, str, float, bool, list, tuple, set)
        for attr in dir(obj):
            if attr.startswith("__"):
                continue
            attr_value = getattr(obj, attr, None)
            if attr in data:
                if isinstance(data[attr], dict) and not isinstance(attr_value, primitive_types):
                    # If the attribute is a complex type and the corresponding data is a dictionary,
                    # recursively update or instantiate this attribute.
                    if attr_value is None:
                        # If the attribute is None, try to instantiate it if it's a class.
                        attr_type = type(attr_value)
                        new_obj = attr_type() if attr_type not in primitive_types else data[attr]
                        setattr(obj, attr, Reflector.from_dict(new_obj, data[attr]))
                    else:
                        # If the attribute already has a value, update it recursively.
                        setattr(obj, attr, Reflector.from_dict(attr_value, data[attr]))
                else:
                    # For primitive types or non-dictionary data, directly set the attribute.
                    setattr(obj, attr, data[attr])
        return obj

    @staticmethod
    def to_dict(obj: object) -> dict:
        result = {}
        primitive_types = (int, str, float, bool, list, tuple, set, dict)
        for attr in dir(obj):
            if attr.startswith("__") or callable(getattr(obj, attr)):
                continue
            value = getattr(obj, attr, None)
            if isinstance(value, primitive_types):
                result[attr] = value
            else:
                result[attr] = Reflector.to_dict(value)
        return result

    @staticmethod
    def to_yaml(obj: object, file_path: str):
        data = Reflector.to_dict(obj)
        Reflector.dict_to_yaml(data, file_path)

    @staticmethod
    def dict_to_yaml(data: dict, file_path: str):
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, mode='w', encoding='utf-8') as file:
            yaml.dump(data, file, allow_unicode=True)

    @staticmethod
    def inst(data: dict):
        return Reflector.from_dict(data.__class__(), data)

    @staticmethod
    def clone(obj):
        return Reflector.from_dict(obj.__class__(), obj.__dict__)


# ConfigLoader =============================================================================== #

class ConfigUtil:
    @staticmethod
    def load_yaml(*config_paths):
        """
        Load the first existing configuration file from the given paths.
        :param config_paths: Variable number of paths to configuration files.
        :return: The loaded configuration as a dictionary.
        """
        for config_path in config_paths:
            if os.path.exists(config_path):
                with open(config_path, mode='r', encoding='utf-8') as config_file:
                    return yaml.safe_load(config_file)
        # Optionally, return a default configuration or raise an exception if no file is found.
        raise FileNotFoundError("No configuration file found in the provided paths.")


# Logging =============================================================================== #

class LogUtil:
    @staticmethod
    def load_yaml(*config_path):
        config = ConfigUtil.load_yaml(*config_path)
        log_path = getv(config, "", "handlers", "file_handler", "filename")
        if not os.path.exists(log_path):
            log_dir_path = os.path.dirname(log_path)
            os.makedirs(log_dir_path, exist_ok=True)
        # noinspection PyUnresolvedReferences
        logging.config.dictConfig(config)
        return config


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
    def fopen(file_path, mode: str = 'rw', encoding: str = 'utf-8', mkdir=True):
        if mkdir:
            parent_directory = os.path.dirname(file_path)
            os.makedirs(parent_directory, exist_ok=True)
        file = open(file_path, mode=mode, encoding=encoding)
        return file
