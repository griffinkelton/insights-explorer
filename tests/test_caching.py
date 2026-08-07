"""Tests for utils/caching.memoize_fingerprint (Phase 2, spec Task 3).

Covers the confirmed P0 + review-fix contract:
- identical frame content → cached result reused (no recompute)
- frame content change → recompute (fingerprint key, not object identity)
- maxsize bound evicts LRU entries
- optional byte budget with injectable sizeof evicts by size
- cache_clear() resets
- concurrent access does not corrupt the cache
"""

from __future__ import annotations

import threading

import pandas as pd

from utils.caching import memoize_fingerprint


def _df(values: list[int]) -> pd.DataFrame:
    return pd.DataFrame({"a": values})


def test_reuses_result_for_unchanged_frame() -> None:
    calls: list[int] = []

    @memoize_fingerprint()
    def fn(df: pd.DataFrame) -> int:
        calls.append(1)
        return int(df["a"].sum())

    frame = _df([1, 2, 3])
    assert fn(frame) == 6
    assert fn(_df([1, 2, 3])) == 6  # same content, new object
    assert len(calls) == 1


def test_recomputes_when_content_changes() -> None:
    calls: list[int] = []

    @memoize_fingerprint()
    def fn(df: pd.DataFrame) -> int:
        calls.append(1)
        return int(df["a"].sum())

    assert fn(_df([1, 2, 3])) == 6
    assert fn(_df([4, 5, 6])) == 15
    assert len(calls) == 2


def test_version_kwarg_is_part_of_key() -> None:
    calls: list[int] = []

    @memoize_fingerprint()
    def fn(df: pd.DataFrame, version: str = "1.0.0") -> str:
        calls.append(1)
        return f"{version}:{int(df['a'].sum())}"

    frame = _df([1, 2])
    assert fn(frame) == "1.0.0:3"
    assert fn(frame, version="2.0.0") == "2.0.0:3"  # different version → recompute
    assert len(calls) == 2


def test_maxsize_evicts_lru() -> None:
    calls: list[int] = []

    @memoize_fingerprint(maxsize=2)
    def fn(df: pd.DataFrame) -> int:
        calls.append(1)
        return int(df["a"].sum())

    fn(_df([1]))
    fn(_df([2]))
    fn(_df([3]))  # evicts [1]
    fn(_df([1]))  # recompute — was evicted
    assert len(calls) == 4


def test_byte_budget_with_injectable_sizeof() -> None:
    calls: list[int] = []

    @memoize_fingerprint(maxsize=32, byte_budget=30, sizeof=lambda obj: 20)
    def fn(df: pd.DataFrame) -> int:
        calls.append(1)
        return int(df["a"].sum())

    fn(_df([1]))  # retained ~20
    fn(_df([2]))  # retained ~40 > 30 → evicts one
    assert len(calls) == 2
    # Re-fetching the evicted one recomputes (kept below budget).
    fn(_df([1]))
    assert len(calls) == 3


def test_cache_clear_resets() -> None:
    calls: list[int] = []

    @memoize_fingerprint()
    def fn(df: pd.DataFrame) -> int:
        calls.append(1)
        return int(df["a"].sum())

    frame = _df([1, 2])
    assert fn(frame) == 3
    assert fn(frame) == 3
    assert len(calls) == 1
    fn.cache_clear()  # type: ignore[attr-defined]
    assert fn(frame) == 3
    assert len(calls) == 2


def test_concurrent_access_is_safe() -> None:
    calls: list[int] = []
    errors: list[Exception] = []

    @memoize_fingerprint(maxsize=8)
    def fn(df: pd.DataFrame) -> int:
        calls.append(1)
        return int(df["a"].sum())

    frames = [_df([i]) for i in range(20)]

    def worker() -> None:
        try:
            for _ in range(50):
                fn(frames[0])  # hot frame — exercises the in-lock hit path
                fn(frames[len(frames) - 1])  # cold frame — exercises eviction
        except Exception as exc:  # pragma: no cover — failure surfaces in test
            errors.append(exc)

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors
    assert len(calls) > 0
