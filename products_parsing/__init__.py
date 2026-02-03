from __future__ import annotations

"""Product parsing and canonical schema utilities."""

from typing import Iterable, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from products_parsing.adapters import PersistSummary
    from products_parsing.parser import ParseReport

__all__ = ["load_records_from_json", "run_pipeline"]


def run_pipeline(
    records: Iterable[dict],
    config_path: str,
    session,
    unique_identifier: str | None = None,
    report: ParseReport | None = None,
) -> "Tuple[PersistSummary, ParseReport]":
    from .pipeline import run_pipeline as _run_pipeline

    return _run_pipeline(
        records=records,
        config_path=config_path,
        session=session,
        unique_identifier=unique_identifier,
        report=report,
    )


def load_records_from_json(path: str) -> Iterable[dict]:
    from .pipeline import load_records_from_json as _load_records_from_json

    return _load_records_from_json(path)
