def flatten_dict(d: dict) -> list:
    """
    Flatten a nested dictionary into a list of values.
    """
    def _flatten(d, result):
        for key, value in d.items():
            if isinstance(value, dict):
                _flatten(value, result)
            else:
                result.append(value)
        return result

    return _flatten(d, [])
