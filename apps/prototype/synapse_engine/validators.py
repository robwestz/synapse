from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import json
import jsonschema


class SchemaValidator:
    def __init__(self, schema_dir: Path):
        self.schema_dir = schema_dir
        self.store: Dict[str, Any] = {}
        self.schemas: Dict[str, Any] = {}
        self._load_all()

    def _load_all(self) -> None:
        for p in self.schema_dir.glob("*.schema.json"):
            schema = json.loads(p.read_text(encoding="utf-8"))
            name = p.name
            self.schemas[name] = schema
            # store by $id (if present) and by file name to satisfy relative refs
            sid = schema.get("$id")
            if sid:
                self.store[sid] = schema
            self.store[name] = schema

    def validate(self, doc: Dict[str, Any], schema_name: str) -> None:
        if schema_name not in self.schemas:
            raise KeyError(f"Schema not found: {schema_name}")
        schema = self.schemas[schema_name]
        resolver = jsonschema.RefResolver.from_schema(schema, store=self.store)
        validator = jsonschema.Draft202012Validator(schema, resolver=resolver)
        errors = sorted(validator.iter_errors(doc), key=lambda e: e.path)
        if errors:
            msg = "\n".join([f"{list(e.path)}: {e.message}" for e in errors[:25]])
            raise jsonschema.ValidationError(f"{schema_name} validation failed:\n{msg}")
