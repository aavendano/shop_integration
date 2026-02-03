import csv
import itertools
import json
from pathlib import Path
from typing import Iterable, Tuple

from products_parsing.adapters import PersistOptions, PersistSummary, persist_records
from products_parsing.config.loader import ProviderConfig, load_provider_config
from products_parsing.parser import ParseReport, parse_records


def run_pipeline(
    records: Iterable[dict],
    config_path: str,
    session,
    unique_identifier: str | None = None,
    report: ParseReport | None = None,
) -> Tuple[PersistSummary, ParseReport]:
    config = load_provider_config(config_path)
    active_report = report or ParseReport()

    options = PersistOptions(
        session=session,
        unique_identifier=unique_identifier or _default_identifier(config),
    )

    canonical_records = parse_records(records, config, report=active_report)
    summary = persist_records(canonical_records, options)
    return summary, active_report


def _default_identifier(config: ProviderConfig) -> str:
    if config.schema_version == "v2":
        return "variants.supplier_sku"
    return "identifiers.sku"


def load_records_from_json(path: str) -> Iterable[dict]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".csv":
        with file_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.reader(handle)
            try:
                headers = next(reader)
            except StopIteration:
                return []
            headers = _dedupe_headers(headers)
            rows = []
            for row in reader:
                if not row:
                    continue
                rows.append(
                    {
                        key: value
                        for key, value in itertools.zip_longest(
                            headers, row, fillvalue=""
                        )
                    }
                )
            return rows

    content = file_path.read_text(encoding="utf-8").strip()
    if not content:
        return []

    if content.startswith("["):
        data = json.loads(content)
        if not isinstance(data, list):
            raise ValueError("JSON array expected for records")
        return data

    records = []
    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def _dedupe_headers(headers: list[str]) -> list[str]:
    counts = {}
    deduped = []
    for header in headers:
        if header.startswith("\ufeff"):
            header = header.lstrip("\ufeff")
        if header in counts:
            counts[header] += 1
            deduped.append(f"{header}__{counts[header]}")
        else:
            counts[header] = 1
            deduped.append(header)
    return deduped
