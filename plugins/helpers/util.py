import json
import ast
from typing import Any, Union
from json import JSONDecodeError

def json_parser(data: Any, indent: Union[int, None] = None, ensure_ascii: bool = False) -> Any:
    """
    Parses and formats JSON-like or Python-like data structures.

    Args:
        data: The input data to parse and format
        indent: Number of spaces for indentation. None for compact output
        ensure_ascii: If False, non-ASCII characters are allowed (default)

    Returns:
        Formatted JSON-like string or original data
    """
    if isinstance(data, (dict, list)):
        try:
            return json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
        except Exception:
            return str(data)

    if isinstance(data, str):
        # Try parsing with ast.literal_eval (handles Python-style dicts/lists)
        try:
            parsed = ast.literal_eval(data)
            if isinstance(parsed, (dict, list)):
                return json.dumps(parsed, indent=indent, ensure_ascii=ensure_ascii)
        except Exception:
            pass

        # Try parsing with json.loads (handles actual JSON)
        try:
            parsed = json.loads(data)
            return json.dumps(parsed, indent=indent, ensure_ascii=ensure_ascii)
        except JSONDecodeError:
            return data

    return str(data)