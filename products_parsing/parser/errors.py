from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ParseError:
    provider_id: str
    record_index: int
    source: Optional[str]
    destination: Optional[str]
    transform: Optional[str]
    message: str


class ParseFailure(Exception):
    def __init__(self, error: ParseError, cause: Exception) -> None:
        super().__init__(str(cause))
        self.error = error
        self.cause = cause


@dataclass
class ParseReport:
    errors: List[ParseError] = field(default_factory=list)

    def record(self, error: ParseError) -> None:
        self.errors.append(error)

    @property
    def error_count(self) -> int:
        return len(self.errors)
