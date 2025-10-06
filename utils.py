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

def fix_schema2(schema):
    """
    Convert JSON Schema to Gemini-compatible format:
    1. Resolve $ref
    2. Handle type arrays like ['string', 'null'] -> 'STRING'
    3. Remove unsupported fields
    """
    schema = fix_schema(schema)  # Resolve $ref first
    
    if not isinstance(schema, dict):
        return schema

    UNSUPPORTED_FIELDS = {
        'additionalProperties', 
        'additional_properties',
        '$schema',
        '$id',
        'definitions',
        'anyOf',  # Remove this - Gemini doesn't support anyOf
        'not'     # Remove this too
    }

    converted = {}
    
    for key, value in schema.items():
        if key in UNSUPPORTED_FIELDS or key == "$ref":
            continue
            
        if key == "type":
            # Handle type arrays like ['string', 'null']
            if isinstance(value, list):
                non_null_types = [t for t in value if t != "null"]
                if non_null_types:
                    # Map JSON Schema types to Gemini types
                    json_type = non_null_types[0]
                    type_mapping = {
                        'string': 'STRING',
                        'number': 'NUMBER',
                        'integer': 'INTEGER',
                        'boolean': 'BOOLEAN',
                        'array': 'ARRAY',
                        'object': 'OBJECT'
                    }
                    converted[key] = type_mapping.get(json_type, 'STRING')
                else:
                    converted[key] = 'NULL'
            else:
                # Single type - convert to uppercase
                type_mapping = {
                    'string': 'STRING',
                    'number': 'NUMBER',
                    'integer': 'INTEGER',
                    'boolean': 'BOOLEAN',
                    'array': 'ARRAY',
                    'object': 'OBJECT',
                    'null': 'NULL'
                }
                converted[key] = type_mapping.get(value.lower(), 'STRING')
        
        elif key == "properties":
            # Recursively convert nested properties
            converted[key] = {
                prop_key: fix_schema2(prop_value)
                for prop_key, prop_value in value.items()
            }
        
        elif key == "items":
            # Handle array items
            converted[key] = fix_schema2(value) if isinstance(value, dict) else value
        
        elif isinstance(value, dict):
            # Recursively convert nested objects
            converted[key] = fix_schema2(value)
        
        elif isinstance(value, list):
            # Recursively convert lists
            converted[key] = [
                fix_schema2(item) if isinstance(item, dict) else item
                for item in value
            ]
        
        else:
            # Copy primitives as-is
            converted[key] = value
    
    return converted

# def fix_schema2(schema):
#     """
#     Convert OpenAPI-style schema to Gemini-compatible format.
#     Handles type arrays like ['string', 'null'] -> 'STRING' with optional flag.
#     """
#     schema = fix_schema(schema)
#     if not isinstance(schema, dict):
#         return schema

#     UNSUPPORTED_FIELDS = {
#         'additionalProperties', 
#         'additional_properties',
#         '$schema',
#         '$id',
#         'definitions'
#     }

#     converted = {}
    
#     for key, value in schema.items():
#         if key in UNSUPPORTED_FIELDS or key == "$ref":
#             continue
#         if key == "type":
#             # Handle type conversion
#             if isinstance(value, list):
#                 # Extract non-null type from array like ['string', 'null']
#                 non_null_types = [t for t in value if t != "null"]
#                 if non_null_types:
#                     converted[key] = non_null_types[0].upper()
#                 else:
#                     converted[key] = "STRING"  # fallback
#             else:
#                 # Single type string
#                 converted[key] = value.upper()
        
#         elif key == "anyOf":
#             # Handle anyOf by extracting the primary type
#             if isinstance(value, list):
#                 for option in value:
#                     if isinstance(option, dict) and "type" in option:
#                         if option["type"] != "null":
#                             converted["type"] = option["type"].upper()
#                             if "enum" in option:
#                                 converted["enum"] = option["enum"]
#                             break
        
#         elif key == "properties":
#             # Recursively convert nested properties
#             converted[key] = {
#                 prop_key: fix_schema2(prop_value)
#                 for prop_key, prop_value in value.items()
#             }
        
#         elif isinstance(value, dict):
#             # Recursively convert nested objects
#             converted[key] = fix_schema2(value)
        
#         elif isinstance(value, list):
#             # Recursively convert lists of objects
#             converted[key] = [
#                 fix_schema2(item) if isinstance(item, dict) else item
#                 for item in value
#             ]
        
#         else:
#             # Copy other values as-is
#             converted[key] = value
    
#     return converted


test_json = {
    "type": "object",
    "properties": {
        "project_id": {
            "type": "string",
            "description": "Project ID or complete URL-encoded path to project"
        },
        "merge_request_iid": {
            "type": "string",
            "description": "The IID of a merge request"
        },
        "body": {
            "type": "string",
            "description": "The content of the thread"
        },
        "position": {
            "type": "object",
            "properties": {
                "base_sha": {
                    "type": "string",
                    "description": "REQUIRED: Base commit SHA in the source branch. Get this from merge request diff_refs.base_sha."
                },
                "head_sha": {
                    "type": "string",
                    "description": "REQUIRED: SHA referencing HEAD of the source branch. Get this from merge request diff_refs.head_sha."
                },
                "start_sha": {
                    "type": "string",
                    "description": "REQUIRED: SHA referencing the start commit of the source branch. Get this from merge request diff_refs.start_sha."
                },
                "position_type": {
                    "type": "string",
                    "enum": [
                        "text",
                        "image",
                        "file"
                    ],
                    "description": "REQUIRED: Position type. Use 'text' for code diffs, 'image' for image diffs, 'file' for file-level comments."
                },
                "new_path": {
                    "type": [
                        "string",
                        "null"
                    ],
                    "description": "File path after changes. REQUIRED for most diff comments. Use same as old_path if file wasn't renamed."}, "old_path": {"type": ["string", "null"], "description": "File path before changes. REQUIRED for most diff comments. Use same as new_path if file wasn't renamed."
                },
                "new_line": {
                    "type": [
                        "number",
                        "null"
                    ],
                    "description": "Line number in modified file (after changes). Use for added lines or context lines. NULL for deleted lines. For single-line comments on new lines."
                },
                "old_line": {
                    "type": [
                        "number",
                        "null"
                    ],
                    "description": "Line number in original file (before changes). Use for deleted lines or context lines. NULL for added lines. For single-line comments on old lines."
                },
                "line_range": {
                    "type": "object",
                    "properties": {
                        "start": {
                            "type": "object",
                            "properties": {
                                "line_code": {
                                    "type": [
                                        "string",
                                        "null"
                                    ],
                                    "description": "CRITICAL: Line identifier in format '{file_path_sha1_hash}_{old_line_number}_{new_line_number}'. USUALLY REQUIRED for GitLab diff comments despite being optional in schema. Example: 'a1b2c3d4e5f6_10_15'. Get this from GitLab diff API response, never fabricate."
                                },
                                "type": {
                                    "anyOf": [
                                        {
                                            "type": "string",
                                            "enum": [
                                                "new",
                                                "old",
                                                "expanded"
                                            ]
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "description": "Line type: 'old' = deleted/original line, 'new' = added/modified line, null = unchanged context. MUST match the line_code format and old_line/new_line values."
                                },
                                "old_line": {
                                    "type": [
                                        "number",
                                        "null"
                                    ],
                                    "description": "Line number in original file (before changes). REQUIRED when type='old', NULL when type='new' (for purely added lines), can be present for context lines."
                                },
                                "new_line": {
                                    "type": [
                                        "number",
                                        "null"
                                    ],
                                    "description": "Line number in modified file (after changes). REQUIRED when type='new', NULL when type='old' (for purely deleted lines), can be present for context lines."
                                }
                            },
                            "additionalProperties": False,
                            "description": "Start line position for multiline comment range. MUST specify either old_line OR new_line (or both for context), never neither."
                        },
                        "end": {
                            "type": "object",
                            "properties": {
                                "line_code": {
                                    "type": [
                                        "string",
                                        "null"
                                    ],
                                    "description": "CRITICAL: Line identifier in format '{file_path_sha1_hash}_{old_line_number}_{new_line_number}'. USUALLY REQUIRED for GitLab diff comments despite being optional in schema. Example: 'a1b2c3d4e5f6_12_17'. Must be from same file as start.line_code."
                                },
                                "type": {
                                    "anyOf": [
                                        {
                                            "type": "string",
                                            "enum": [
                                                "new",
                                                "old",
                                                "expanded"
                                            ]
                                        },
                                        {
                                            "type": "null"
                                        }
                                    ],
                                    "description": "Line type: 'old' = deleted/original line, 'new' = added/modified line, null = unchanged context. SHOULD MATCH start.type for consistent ranges (don't mix old/new types)."}, "old_line": {"type": ["number", "null"], "description": "Line number in original file (before changes). REQUIRED when type='old', NULL when type='new' (for purely added lines), can be present for context lines. MUST be >= start.old_line if both specified."}, "new_line": {"type": ["number", "null"], "description": "Line number in modified file (after changes). REQUIRED when type='new', NULL when type='old' (for purely deleted lines), can be present for context lines. MUST be >= start.new_line if both specified."}}, "additionalProperties": False, "description": "End line position for multiline comment range. MUST specify either old_line OR new_line (or both for context), never neither. Range must be valid (end >= start)."}}, "required": ["start", "end"], "additionalProperties": False, "description": "MULTILINE COMMENTS: Specify start/end line positions for commenting on multiple lines. Alternative to single old_line/new_line."}, "width": {"type": "number", "description": "IMAGE DIFFS ONLY: Width of the image (for position_type='image')."}, "height": {"type": "number", "description": "IMAGE DIFFS ONLY: Height of the image (for position_type='image')."}, "x": {"type": "number", "description": "IMAGE DIFFS ONLY: X coordinate on the image (for position_type='image')."}, "y": {"type": "number", "description": "IMAGE DIFFS ONLY: Y coordinate on the image (for position_type='image')."}}, "required": ["base_sha", "head_sha", "start_sha", "position_type"], "additionalProperties": False, "description": "Position when creating a diff note"}, "created_at": {"type": "string", "description": "Date the thread was created at (ISO 8601 format)"}}, "required": ["body"], "additionalProperties": False}

if __name__=='__main__':
    print(fix_schema(test_json))