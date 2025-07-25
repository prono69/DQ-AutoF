import json
from json import JSONDecodeError
from typing import Any, Union


def json_parser(
    data: Any, indent: Union[int, None] = None, ensure_ascii: bool = False
) -> Any:
    """
    Parses and formats JSON-like data.

    Args:
        data: The input data to parse and format
        indent: Number of spaces for indentation. None for compact output
        ensure_ascii: If False, non-ASCII characters are allowed (default)

    Returns:
        Parsed and formatted data
    """
    if isinstance(data, (dict, list)):
        try:
            return (
                json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
                if indent is not None
                else data
            )
        except Exception:
            return data

    if isinstance(data, str):
        try:
            parsed = json.loads(data)
            return (
                json.dumps(parsed, indent=indent, ensure_ascii=ensure_ascii)
                if indent is not None
                else parsed
            )
        except JSONDecodeError:
            return data

    return data
