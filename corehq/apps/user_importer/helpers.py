from dimagi.utils.parsing import string_to_boolean


def spec_value_to_boolean_or_none(user_spec_dict, key):
    value = user_spec_dict.get(key) or None
    if value and isinstance(value, str):
        return string_to_boolean(value)
    return value
