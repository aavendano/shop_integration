from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


@dataclass
class ConfigValidationIssue:
    path: str
    message: str


@dataclass
class TransformSpec:
    name: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MappingRule:
    source: str
    destination: str
    transforms: List[TransformSpec] = field(default_factory=list)
    default: Any = None


@dataclass
class ProviderConfig:
    provider_id: str
    mappings: List[MappingRule]
    error_policy: str = "continue"
    transform_params: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def load_provider_config(path: str) -> ProviderConfig:
    data = _read_json(path)
    return load_provider_config_from_dict(data, source_path=path)


def load_provider_config_from_dict(
    data: Dict[str, Any], source_path: str = "<dict>"
) -> ProviderConfig:
    issues = validate_provider_config(data)
    if issues:
        message = _format_issues(issues)
        raise ValueError(f"Invalid provider config ({source_path}): {message}")

    mappings = [
        MappingRule(
            source=rule["source"],
            destination=rule["destination"],
            transforms=_parse_transforms(rule.get("transforms", [])),
            default=rule.get("default"),
        )
        for rule in data["mappings"]
    ]

    return ProviderConfig(
        provider_id=data["provider_id"],
        mappings=mappings,
        error_policy=data.get("error_policy", "continue"),
        transform_params=data.get("transform_params", {}),
    )


def validate_provider_config(data: Any) -> List[ConfigValidationIssue]:
    issues: List[ConfigValidationIssue] = []

    if not isinstance(data, dict):
        return [ConfigValidationIssue(path="$", message="Expected object")]

    provider_id = data.get("provider_id")
    if not isinstance(provider_id, str) or not provider_id.strip():
        issues.append(ConfigValidationIssue(path="provider_id", message="Required"))

    error_policy = data.get("error_policy", "continue")
    if error_policy not in {"continue", "fail"}:
        issues.append(
            ConfigValidationIssue(
                path="error_policy",
                message="Expected 'continue' or 'fail'",
            )
        )

    mappings = data.get("mappings")
    if not isinstance(mappings, list):
        issues.append(ConfigValidationIssue(path="mappings", message="Expected list"))
        return issues

    for idx, rule in enumerate(mappings):
        issues.extend(_validate_mapping_rule(rule, idx))

    transform_params = data.get("transform_params", {})
    if not isinstance(transform_params, dict):
        issues.append(
            ConfigValidationIssue(
                path="transform_params",
                message="Expected object",
            )
        )
    else:
        for key, value in transform_params.items():
            if not isinstance(key, str):
                issues.append(
                    ConfigValidationIssue(
                        path="transform_params",
                        message="Keys must be strings",
                    )
                )
                break
            if not isinstance(value, dict):
                issues.append(
                    ConfigValidationIssue(
                        path=f"transform_params.{key}",
                        message="Expected object",
                    )
                )

    return issues


def _validate_mapping_rule(rule: Any, idx: int) -> List[ConfigValidationIssue]:
    issues: List[ConfigValidationIssue] = []
    path_prefix = f"mappings[{idx}]"

    if not isinstance(rule, dict):
        return [ConfigValidationIssue(path=path_prefix, message="Expected object")]

    source = rule.get("source")
    if not isinstance(source, str) or not source.strip():
        issues.append(
            ConfigValidationIssue(
                path=f"{path_prefix}.source",
                message="Required",
            )
        )

    destination = rule.get("destination")
    if not isinstance(destination, str) or not destination.strip():
        issues.append(
            ConfigValidationIssue(
                path=f"{path_prefix}.destination",
                message="Required",
            )
        )

    transforms = rule.get("transforms", [])
    if transforms is None:
        return issues
    if not isinstance(transforms, list):
        issues.append(
            ConfigValidationIssue(
                path=f"{path_prefix}.transforms",
                message="Expected list",
            )
        )
        return issues

    for t_idx, transform in enumerate(transforms):
        issues.extend(
            _validate_transform(transform, f"{path_prefix}.transforms[{t_idx}]")
        )

    return issues


def _validate_transform(transform: Any, path: str) -> List[ConfigValidationIssue]:
    issues: List[ConfigValidationIssue] = []

    if not isinstance(transform, dict):
        return [ConfigValidationIssue(path=path, message="Expected object")]

    name = transform.get("name")
    if not isinstance(name, str) or not name.strip():
        issues.append(ConfigValidationIssue(path=f"{path}.name", message="Required"))

    params = transform.get("params")
    if params is not None and not isinstance(params, dict):
        issues.append(
            ConfigValidationIssue(
                path=f"{path}.params",
                message="Expected object",
            )
        )

    return issues


def _parse_transforms(transforms: Sequence[Dict[str, Any]]) -> List[TransformSpec]:
    parsed: List[TransformSpec] = []
    for transform in transforms:
        params = transform.get("params") or {}
        parsed.append(TransformSpec(name=transform["name"], params=params))
    return parsed


def _read_json(path: str) -> Dict[str, Any]:
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected root object in {path}")
    return data


def _format_issues(issues: Sequence[ConfigValidationIssue]) -> str:
    return "; ".join(f"{issue.path}: {issue.message}" for issue in issues)
