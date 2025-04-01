from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class ParsedArguments:
    @staticmethod
    def execute(namespace: ParsedArguments) -> None:
        ...
