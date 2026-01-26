from typing import Any, Callable, Dict, Optional


TransformFunc = Callable[[Any, Optional[Dict[str, Any]]], Any]


class TransformRegistry:
    def __init__(self) -> None:
        self._registry: Dict[str, TransformFunc] = {}

    def register(self, name: str, func: TransformFunc) -> None:
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Transform name must be a non-empty string")
        if name in self._registry:
            raise ValueError(f"Transform already registered: {name}")
        self._registry[name] = func

    def get(self, name: str) -> TransformFunc:
        if name not in self._registry:
            raise KeyError(f"Unknown transform: {name}")
        return self._registry[name]

    def apply(self, name: str, value: Any, params: Optional[Dict[str, Any]] = None) -> Any:
        func = self.get(name)
        return func(value, params)


registry = TransformRegistry()


def register_transform(name: str) -> Callable[[TransformFunc], TransformFunc]:
    def decorator(func: TransformFunc) -> TransformFunc:
        registry.register(name, func)
        return func

    return decorator


def apply_transform(name: str, value: Any, params: Optional[Dict[str, Any]] = None) -> Any:
    return registry.apply(name, value, params=params)
