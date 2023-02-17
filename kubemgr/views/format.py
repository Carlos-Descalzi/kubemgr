from typing import Any, Dict, Optional


class Field:
    def __init__(self, field_string: str):
        self._field_string = field_string

    @property
    def width(self) -> Optional[int]:
        width = self._field_string.split(":")[1].replace("<", "").replace(">", "")

        return int(width) if width != "MAX" else None

    def format(self, item, width: int) -> str:
        field_string = self._field_string.replace("MAX", str(int(width)))
        format_string = "{" + field_string + "}"
        return format_string.format(item=item)


class DictWrapper:
    def __init__(self, dict_data: Dict):
        self.dict_data = dict_data

    def __getattr__(self, key: Any) -> Any:
        if key in self.dict_data:
            v = self.dict_data[key]
            if isinstance(v, dict):
                return DictWrapper(v)
            return v
        raise AttributeError(key)


class Formatter:
    def __init__(self, format_string: str):
        self._format_string = format_string
        self._fields = [Field(f) for f in format_string.split(",")]

    def format(self, item, width: int) -> str:
        fixed_width = sum([field.width for field in self._fields if field.width])

        variable_width = [field for field in self._fields if not field.width]

        available = int((width - fixed_width) / len(variable_width))

        string = ""

        item = DictWrapper(item)

        for field in self._fields:
            string += field.format(item, available)

        return string
