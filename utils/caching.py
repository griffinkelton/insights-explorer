"""Framework-neutral, thread-safe memoization keyed on DataFrame content fingerprint.

Design rules (confirmed + refined P0 + review fix, 2026-08-06):
- Key: (fingerprint(df), rest args, sorted kwargs) — content identity, not object id.
- Value: immutable computed result only — never a mutable DataFrame reference.
- Bounded: max entries (default 32) AND an OPTIONAL byte budget (default None).
- Thread-safe: RLock guards every cache mutation (FastAPI worker threads).
- cache_clear() exposed for tests; no session-state dependency; no Streamlit import.
- byte_budget is an APPROXIMATE object-overhead guard, not a guaranteed memory
  cap: sys.getsizeof measures shallow Python object size only, not arrays,
  nested lists, Pandas objects, or model internals. Sizing is injectable so a
  domain-specific sizeof_forecast_result() can be supplied later if memory
  pressure becomes real.
"""

from __future__ import annotations

import sys
from collections import OrderedDict
from threading import RLock
from typing import Any, Callable

from utils.data_context import fingerprint_frame


def memoize_fingerprint(
    maxsize: int = 32,
    byte_budget: int | None = None,
    sizeof: Callable[[Any], int] = sys.getsizeof,
):
    """Memoize a function whose first argument is a DataFrame.

    Key = (fingerprint(df), args, sorted-kwargs); rest args must be hashable.
    Defaults (review fix 2026-08-06): maxsize=32, byte_budget=None — the LRU
    count is predictable, while an uninstrumented byte budget would create
    false confidence. Pass sizeof= when you have an accurate size estimator.
    """

    def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
        cache: OrderedDict[tuple, Any] = OrderedDict()
        retained_bytes: dict[tuple, int] = {}
        lock = RLock()

        def _evict(count: int = 1) -> None:
            for _ in range(count):
                if not cache:
                    return
                oldest = next(iter(cache))
                cache.pop(oldest)
                retained_bytes.pop(oldest, None)

        def wrapper(df, *args, **kwargs):
            # None frames (e.g. forecast_metric's insufficient-data contract)
            # hash to a sentinel instead of crashing fingerprint_frame.
            frame_key = "<none>" if df is None else fingerprint_frame(df)
            key = (frame_key, args, tuple(sorted(kwargs.items())))
            with lock:
                if key in cache:
                    cache.move_to_end(key)
                    return cache[key]
            result = fn(df, *args, **kwargs)  # compute outside the lock
            with lock:
                if key in cache:  # another thread won the race
                    return cache[key]
                cache[key] = result
                cache.move_to_end(key)
                if byte_budget is not None:
                    retained_bytes[key] = sizeof(result)
                if len(cache) > maxsize:
                    _evict(len(cache) - maxsize)
                if byte_budget is not None:
                    while sum(retained_bytes.values()) > byte_budget and len(cache) > 1:
                        _evict(1)
            return result

        def clear() -> None:
            with lock:
                cache.clear()
                retained_bytes.clear()

        wrapper.cache_clear = clear  # type: ignore[attr-defined]
        return wrapper

    return decorator
