import json
from typing import List


class JsonParser:
    def parse(self, event: bytes) -> List[dict]:
        try:
            data = json.parse(event.decode())
        except Exception as e:
            raise ValueError from e

        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data

        raise ValueError


parsers = {
    'application/json': JsonParser,
}
