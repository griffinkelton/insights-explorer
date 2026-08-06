"""Dataset store: protocol + thread-safe in-memory implementation.

``datasets`` (the ``InMemoryDatasetStore`` instance) is the canonical store
instance for the Phase 1 slice — routes and services import it from here
(spec §7/§8). Nothing re-exports or re-instantiates a second store.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import RLock
from typing import Protocol
from uuid import uuid4

import pandas as pd

from api.schemas import DatasetContext


@dataclass
class StoredDataset:
    id: str
    dataframe: pd.DataFrame
    context: DatasetContext


class DatasetStore(Protocol):
    def put(self, dataframe: pd.DataFrame, context: DatasetContext) -> StoredDataset: ...
    def get(self, dataset_id: str) -> StoredDataset | None: ...
    def remove(self, dataset_id: str) -> None: ...


class InMemoryDatasetStore:
    """Dev implementation — memory-cache semantics (eviction-tolerant; Phase 6
    note). Thread-safe: FastAPI may run sync endpoints in worker threads, so
    even the dev store guards its dict with an RLock (mirrors
    InMemorySessionStore).

    Read-only invariant (review fix 2026-08-06): the RLock protects the *dict*
    — not the DataFrames inside. Stored DataFrames are read-only by convention:
    routes/services must derive new frames for transformations (filter,
    sample, custom metrics) rather than mutating the stored frame in place.
    A future shared store will enforce a serialization/copy model.
    """

    def __init__(self) -> None:
        self._items: dict[str, StoredDataset] = {}
        self._lock = RLock()

    def put(self, dataframe: pd.DataFrame, context: DatasetContext) -> StoredDataset:
        item = StoredDataset(id=uuid4().hex, dataframe=dataframe, context=context)
        with self._lock:
            self._items[item.id] = item
        return item

    def get(self, dataset_id: str) -> StoredDataset | None:
        with self._lock:
            return self._items.get(dataset_id)

    def remove(self, dataset_id: str) -> None:
        with self._lock:
            self._items.pop(dataset_id, None)

    # ── Public test-only helpers (review fix 2026-08-06) — contract tests must
    # not reach into ``_sessions``/``_items`` private dicts; these give a stable
    # surface that survives a future store swap. ────────────────────────────
    def clear_for_test(self) -> None:
        """Empty the store. Test-only; not part of the runtime contract."""
        with self._lock:
            self._items.clear()

    def count_for_test(self) -> int:
        """Number of live entries. Test-only; not part of the runtime contract."""
        with self._lock:
            return len(self._items)


datasets = InMemoryDatasetStore()
