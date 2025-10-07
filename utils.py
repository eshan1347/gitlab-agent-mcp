from copy import deepcopy
from typing import Any, Dict, Set
import json

def resolve_json_pointer(root: Dict[str, Any], pointer: str) -> Any:
    """Resolve a JSON Pointer (RFC 6901). pointer must start with '#' or '' (root)."""
    if pointer == "#" or pointer == "":
        return root
    if pointer.startswith("#"):
        pointer = pointer[1:]
    if pointer.startswith("/"):
        pointer = pointer[1:]
    if not pointer:
        return root
    parts = pointer.split("/")
    current = root
    for part in parts:
        # unescape ~1 -> / and ~0 -> ~
        part = part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            # array index
            try:
                idx = int(part)
            except Exception as e:
                raise KeyError(f"Invalid array index '{part}' in pointer '{pointer}'") from e
            current = current[idx]
        elif isinstance(current, dict):
            if part not in current:
                raise KeyError(f"Pointer segment '{part}' not found in {list(current.keys())}")
            current = current[part]
        else:
            raise KeyError(f"Can't navigate into {type(current)} with segment '{part}'")
    return current


def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dicts. Values in override win.
    For keys where both sides are dicts, merge recursively.
    Lists and scalars are replaced by override entirely.
    """
    out = deepcopy(base)
    for k, v in override.items():
        if k in out and isinstance(out[k], dict) and isinstance(v, dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = deepcopy(v)
    return out


def fix_schema(schema: Dict[str, Any], allow_external: bool = False) -> Dict[str, Any]:
    """
    Return a copy of `schema` with internal $ref resolved and removed.
    - Only supports internal refs (JSON Pointer starting with '#') by default.
    - detect cycles and raise ValueError if cycical $ref encountered.
    - `allow_external=True` would allow non-# refs, but it is not implemented here.
    """
    root = deepcopy(schema)
    seen: Set[str] = set()  # stack of pointers currently being resolved to detect cycles

    def _resolve(node: Any) -> Any:
        if isinstance(node, dict):
            # If this dict is a $ref wrapper
            if "$ref" in node:
                ref = node["$ref"]
                if not isinstance(ref, str):
                    raise TypeError("$ref value must be a string")
                if not ref.startswith("#"):
                    if allow_external:
                        raise NotImplementedError("External $ref resolution is not implemented in this helper.")
                    else:
                        # leave external refs untouched or raise — we choose to raise to avoid silent mistakes
                        raise NotImplementedError(f"External $ref '{ref}' not supported by this function.")
                # cycle detection
                if ref in seen:
                    raise ValueError(f"Circular $ref detected for pointer '{ref}' (stack: {list(seen)})")
                seen.add(ref)
                try:
                    target = resolve_json_pointer(root, ref)
                except KeyError as e:
                    raise KeyError(f"Failed to resolve pointer '{ref}': {e}") from e
                # copied and resolved target (itself may contain $ref)
                target_copy = deepcopy(target)
                resolved_target = _resolve(target_copy)
                # local overrides (other keys in node) override target
                overrides = {k: v for k, v in node.items() if k != "$ref"}
                merged = deep_merge(resolved_target if isinstance(resolved_target, dict) else {}, overrides)
                seen.remove(ref)
                return _resolve(merged)
            # otherwise traverse each key
            out = {}
            for k, v in node.items():
                out[k] = _resolve(v)
            return out
        elif isinstance(node, list):
            return [_resolve(item) for item in node]
        else:
            return node

    return _resolve(root)

if __name__=='__main__':
    print(fix_schema(test_json))