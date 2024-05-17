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
