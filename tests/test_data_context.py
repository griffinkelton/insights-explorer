"""Tests for utils/data_context.py — v0.2.0 final 3-layer contract.

Covers: FilterState, DataContext, factories, transitions, no-ops,
input validation, provenance format, isolation, GA4 canonicalization,
fingerprint correctness, and multi-step chains.
"""

import hashlib

import pandas as pd
import pytest

from utils.data_context import (
    DataContext,
    FilterState,
    create_context_from_ga4,
    create_context_from_upload,
    fingerprint_frame,
    with_custom_metrics,
    with_filtered_data,
    with_filters_cleared,
)


# ── Test Data ────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_df():
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": ["x", "y", "z"]})


@pytest.fixture
def sample_bytes(sample_df):
    return sample_df.to_csv(index=False).encode("utf-8")


# ── FilterState ──────────────────────────────────────────────────────────────


class TestFilterState:
    def test_defaults(self):
        fs = FilterState()
        assert fs.descriptions == ()
        assert fs.is_active is False
        assert fs.row_count == 0

    def test_active_filter(self):
        fs = FilterState(descriptions=("a > 1", "b < 10"), is_active=True, row_count=50)
        assert fs.descriptions == ("a > 1", "b < 10")
        assert fs.is_active is True
        assert fs.row_count == 50

    def test_immutable(self):
        fs = FilterState(descriptions=("test",))
        with pytest.raises(AttributeError):
            fs.descriptions = ("changed",)  # type: ignore[misc]

    def test_equality(self):
        a = FilterState(descriptions=("x",), is_active=True, row_count=5)
        b = FilterState(descriptions=("x",), is_active=True, row_count=5)
        c = FilterState(descriptions=("y",), is_active=True, row_count=5)
        assert a == b
        assert a != c


# ── DataContext ──────────────────────────────────────────────────────────────


class TestDataContext:
    def test_creation(self, sample_df):
        ctx = DataContext(
            source_id="test:1",
            version=0,
            raw_df=sample_df,
            base_df=sample_df,
            active_df=sample_df,
            provenance=("created",),
        )
        assert ctx.source_id == "test:1"
        assert ctx.version == 0
        assert ctx.filters == FilterState()
        assert ctx.provenance == ("created",)
        assert ctx.truncated is False

    def test_three_layer_structure(self, sample_df):
        """base_df and active_df are present as distinct fields."""
        ctx = create_context_from_upload(sample_df, sample_df.to_csv(index=False).encode())
        assert hasattr(ctx, "raw_df")
        assert hasattr(ctx, "base_df")
        assert hasattr(ctx, "active_df")
        pd.testing.assert_frame_equal(ctx.raw_df, ctx.base_df)
        pd.testing.assert_frame_equal(ctx.base_df, ctx.active_df)

    def test_cache_key(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        assert ctx.cache_key.startswith("file:")
        assert f":v{ctx.version}" in ctx.cache_key

    def test_cache_key_includes_source_and_version(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        assert ctx.cache_key == f"{ctx.source_id}:v{ctx.version}"

    def test_frozen_prevents_attribute_mutation(self, sample_df):
        ctx = DataContext(
            source_id="test:1",
            version=0,
            raw_df=sample_df,
            base_df=sample_df,
            active_df=sample_df,
        )
        with pytest.raises(AttributeError):
            ctx.version = 5  # type: ignore[misc]

    def test_truncated_flag(self, sample_df):
        ctx = DataContext(
            source_id="ga4:abc123",
            version=0,
            raw_df=sample_df,
            base_df=sample_df,
            active_df=sample_df,
            truncated=True,
        )
        assert ctx.truncated is True


# ── Fingerprint ──────────────────────────────────────────────────────────────


class TestFingerprint:
    def test_identical_frames_same_fingerprint(self, sample_df):
        assert fingerprint_frame(sample_df) == fingerprint_frame(sample_df.copy())

    def test_different_values_different_fingerprint(self, sample_df):
        modified = sample_df.copy()
        modified["a"] = [99, 100, 101]
        assert fingerprint_frame(sample_df) != fingerprint_frame(modified)

    def test_different_column_order_same_fingerprint(self, sample_df):
        """Column order changes SHOULD produce different fingerprints."""
        reordered = sample_df[["c", "b", "a"]]
        assert fingerprint_frame(sample_df) != fingerprint_frame(reordered)

    def test_returns_24_char_hex(self, sample_df):
        fp = fingerprint_frame(sample_df)
        assert len(fp) == 24
        assert all(c in "0123456789abcdef" for c in fp)


# ── create_context_from_upload ───────────────────────────────────────────────


class TestCreateContextFromUpload:
    def test_source_id_is_content_hash(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        expected_hash = hashlib.sha256(sample_bytes).hexdigest()[:24]
        assert ctx.source_id == f"file:{expected_hash}"

    def test_same_bytes_same_id(self, sample_df):
        """Identical content produces identical source_id."""
        b = sample_df.to_csv(index=False).encode()
        ctx1 = create_context_from_upload(sample_df, b)
        ctx2 = create_context_from_upload(sample_df.copy(), b)
        assert ctx1.source_id == ctx2.source_id

    def test_different_bytes_different_id(self, sample_df):
        """Different content produces different source_id."""
        b1 = sample_df.to_csv(index=False).encode()
        b2 = sample_df.assign(a=[9, 9, 9]).to_csv(index=False).encode()
        ctx1 = create_context_from_upload(sample_df, b1)
        ctx2 = create_context_from_upload(sample_df, b2)
        assert ctx1.source_id != ctx2.source_id

    def test_version_starts_at_zero(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        assert ctx.version == 0

    def test_all_frames_are_deep_copies(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        assert ctx.raw_df is not sample_df
        assert ctx.base_df is not sample_df
        assert ctx.active_df is not sample_df
        assert ctx.raw_df is not ctx.base_df
        assert ctx.base_df is not ctx.active_df

    def test_aliasing_isolation(self, sample_df):
        """Mutating original input after creation does not affect context."""
        b = sample_df.to_csv(index=False).encode()
        ctx = create_context_from_upload(sample_df, b)
        # Mutate original
        sample_df["a"] = [999, 999, 999]
        # Context frames are unchanged
        assert ctx.raw_df["a"].tolist() == [1, 2, 3]
        assert ctx.base_df["a"].tolist() == [1, 2, 3]
        assert ctx.active_df["a"].tolist() == [1, 2, 3]

    def test_provenance_with_display_name(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes, "Q3_report.xlsx")
        assert ctx.provenance == ("upload:Q3_report.xlsx",)

    def test_provenance_without_display_name(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        assert ctx.provenance == ("upload",)

    def test_truncated_defaults_false(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        assert ctx.truncated is False


# ── create_context_from_ga4 ──────────────────────────────────────────────────


class TestCreateContextFromGA4:
    def test_source_id_is_request_hash(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "123456", date_range=("7daysAgo", "today"))
        assert ctx.source_id.startswith("ga4:")
        assert len(ctx.source_id) == len("ga4:") + 24  # "ga4:" + 24 hex chars

    def test_same_params_same_id(self, sample_df):
        """Identical request parameters produce identical source_id."""
        ctx1 = create_context_from_ga4(
            sample_df,
            "123",
            date_range=("7daysAgo", "today"),
            dimensions=["country"],
            metrics=["sessions"],
        )
        ctx2 = create_context_from_ga4(
            sample_df.copy(),
            "123",
            date_range=("7daysAgo", "today"),
            dimensions=["country"],
            metrics=["sessions"],
        )
        assert ctx1.source_id == ctx2.source_id

    def test_different_date_range_different_id(self, sample_df):
        ctx1 = create_context_from_ga4(sample_df, "123", date_range=("7daysAgo", "today"))
        ctx2 = create_context_from_ga4(sample_df, "123", date_range=("30daysAgo", "today"))
        assert ctx1.source_id != ctx2.source_id

    def test_different_metrics_different_id(self, sample_df):
        ctx1 = create_context_from_ga4(sample_df, "123", metrics=["sessions"])
        ctx2 = create_context_from_ga4(sample_df, "123", metrics=["sessions", "users"])
        assert ctx1.source_id != ctx2.source_id

    def test_different_dimensions_different_id(self, sample_df):
        ctx1 = create_context_from_ga4(sample_df, "123", dimensions=["country"])
        ctx2 = create_context_from_ga4(sample_df, "123", dimensions=["country", "device"])
        assert ctx1.source_id != ctx2.source_id

    def test_ga4_normalization_dimension_order(self, sample_df):
        """Semantically identical dimensions in different order produce same ID."""
        ctx1 = create_context_from_ga4(
            sample_df,
            "123",
            dimensions=["country", "device"],
        )
        ctx2 = create_context_from_ga4(
            sample_df,
            "123",
            dimensions=["device", "country"],
        )
        assert ctx1.source_id == ctx2.source_id

    def test_version_starts_at_zero(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "456")
        assert ctx.version == 0

    def test_provenance(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "789")
        assert ctx.provenance == ("ga4_pull:789",)

    def test_truncated_true(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "p1", truncated=True)
        assert ctx.truncated is True

    def test_truncated_defaults_false(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "p1")
        assert ctx.truncated is False

    def test_all_frames_are_deep_copies(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "123")
        assert ctx.raw_df is not sample_df
        assert ctx.base_df is not sample_df
        assert ctx.active_df is not sample_df


# ── with_filtered_data ───────────────────────────────────────────────────────


class TestWithFilteredData:
    def test_version_increments(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        new_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        assert new_ctx.version == ctx.version + 1

    def test_active_df_is_filtered(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        new_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        pd.testing.assert_frame_equal(new_ctx.active_df, filtered)

    def test_base_df_unchanged(self, sample_df, sample_bytes):
        """Filtering modifies active_df but not base_df."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        new_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        pd.testing.assert_frame_equal(new_ctx.base_df, ctx.base_df)

    def test_raw_df_unchanged(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        new_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        pd.testing.assert_frame_equal(new_ctx.raw_df, ctx.raw_df)

    def test_source_id_unchanged(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        new_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        assert new_ctx.source_id == ctx.source_id

    def test_filters_recorded(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        new_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        assert new_ctx.filters.is_active is True
        assert new_ctx.filters.descriptions == ("a > 1",)
        assert new_ctx.filters.row_count == 2

    def test_provenance_format(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        new_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        assert new_ctx.provenance[-1] == "filters:a > 1"

    def test_multi_description_provenance(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        new_ctx = with_filtered_data(ctx, filtered, ("a > 1", "b < 10"))
        assert new_ctx.provenance[-1] == "filters:a > 1|b < 10"

    def test_zero_row_filter_preserved(self, sample_df, sample_bytes):
        """Zero-row filter result is valid empty active_df, not None."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        empty_df = pd.DataFrame(columns=sample_df.columns)
        new_ctx = with_filtered_data(ctx, empty_df, ("a > 999",))
        assert new_ctx.active_df is not None
        assert len(new_ctx.active_df) == 0
        assert new_ctx.filters.is_active is True
        assert new_ctx.filters.row_count == 0

    def test_filtered_df_is_deep_copy(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        new_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        assert new_ctx.active_df is not filtered

    def test_transition_isolation(self, sample_df, sample_bytes):
        """Mutating filtered_df after transition does not affect context."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1].copy()
        new_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        # Mutate the original filtered DataFrame
        filtered["a"] = [999, 999]
        # Context is unchanged
        assert new_ctx.active_df["a"].tolist() == [2, 3]

    # ── No-op tests ──────────────────────────────────────────────────────

    def test_noop_same_filter_returns_original(self, sample_df, sample_bytes):
        """Applying the same filter twice returns the original context (is check)."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        ctx1 = with_filtered_data(ctx, filtered, ("a > 1",))
        ctx2 = with_filtered_data(ctx1, filtered, ("a > 1",))
        assert ctx2 is ctx1  # identity, not just equality

    def test_different_filter_creates_new_context(self, sample_df, sample_bytes):
        """Different filter is NOT a no-op."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        f1 = sample_df[sample_df["a"] > 1]
        f2 = sample_df[sample_df["a"] > 2]
        ctx1 = with_filtered_data(ctx, f1, ("a > 1",))
        ctx2 = with_filtered_data(ctx1, f2, ("a > 2",))
        assert ctx2 is not ctx1
        assert ctx2.version == ctx1.version + 1

    # ── Validation tests ─────────────────────────────────────────────────

    def test_raises_valueerror_on_none(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        with pytest.raises(ValueError, match="must be a DataFrame"):
            with_filtered_data(ctx, None, ("desc",))  # type: ignore[arg-type]

    def test_raises_typeerror_on_non_dataframe(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            with_filtered_data(ctx, "not a dataframe", ("desc",))  # type: ignore[arg-type]

    def test_raises_valueerror_on_empty_descriptions(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        with pytest.raises(ValueError, match="at least one description"):
            with_filtered_data(ctx, sample_df, ())


# ── with_custom_metrics ──────────────────────────────────────────────────────


class TestWithCustomMetrics:
    def test_version_increments(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(ctx, metrics_df)
        assert new_ctx.version == ctx.version + 1

    def test_base_df_is_updated(self, sample_df, sample_bytes):
        """Custom metrics update base_df, not just active_df."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(ctx, metrics_df)
        pd.testing.assert_frame_equal(new_ctx.base_df, metrics_df)
        assert "total" in new_ctx.base_df.columns

    def test_active_df_equals_new_base(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(ctx, metrics_df)
        pd.testing.assert_frame_equal(new_ctx.active_df, new_ctx.base_df)

    def test_filters_cleared(self, sample_df, sample_bytes):
        """Custom metrics clear any active filters."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        # Apply filters first
        filtered = sample_df[sample_df["a"] > 1]
        filtered_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        assert filtered_ctx.filters.is_active is True
        # Apply custom metrics
        metrics_df = filtered_ctx.active_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(filtered_ctx, metrics_df)
        assert new_ctx.filters == FilterState()

    def test_raw_df_unchanged(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(ctx, metrics_df)
        pd.testing.assert_frame_equal(new_ctx.raw_df, sample_df)

    def test_source_id_unchanged(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        metrics_df = sample_df.copy()
        new_ctx = with_custom_metrics(ctx, metrics_df)
        assert new_ctx.source_id == ctx.source_id

    def test_provenance_format(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(ctx, metrics_df)
        assert new_ctx.provenance[-1] == "custom_metrics:applied"

    def test_metrics_df_is_deep_copy(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        metrics_df = sample_df.copy()
        new_ctx = with_custom_metrics(ctx, metrics_df)
        assert new_ctx.active_df is not metrics_df
        assert new_ctx.base_df is not metrics_df

    def test_transition_isolation(self, sample_df, sample_bytes):
        """Mutating metrics_df after transition does not affect context."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(ctx, metrics_df)
        # Mutate the original metrics_df
        metrics_df["total"] = [999, 999, 999]
        assert new_ctx.active_df["total"].tolist() == [5, 7, 9]

    # ── No-op tests ──────────────────────────────────────────────────────

    def test_noop_identical_metrics_returns_original(self, sample_df, sample_bytes):
        """Applying identical metrics returns the original context."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        ctx1 = with_custom_metrics(ctx, sample_df.copy())
        # apply again with identical DataFrame
        ctx2 = with_custom_metrics(ctx1, sample_df.copy())
        assert ctx2 is ctx1

    # ── Validation tests ─────────────────────────────────────────────────

    def test_raises_valueerror_on_none(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        with pytest.raises(ValueError, match="must be a DataFrame"):
            with_custom_metrics(ctx, None)  # type: ignore[arg-type]

    def test_raises_typeerror_on_non_dataframe(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        with pytest.raises(TypeError, match="must be a pandas DataFrame"):
            with_custom_metrics(ctx, {"a": 1})  # type: ignore[arg-type]


# ── with_filters_cleared ─────────────────────────────────────────────────────


class TestWithFiltersCleared:
    def test_restores_from_base_df_not_raw_df(self, sample_df, sample_bytes):
        """Clearing filters restores base_df, preserving custom metrics."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        # First apply custom metrics (modifies base_df)
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        ctx = with_custom_metrics(ctx, metrics_df)
        # Then filter
        filtered = ctx.active_df[ctx.active_df["a"] > 1]
        filtered_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        # Clear filters
        cleared = with_filters_cleared(filtered_ctx)
        # Must restore base_df (which has "total"), not raw_df
        assert "total" in cleared.active_df.columns
        pd.testing.assert_frame_equal(cleared.active_df, ctx.base_df)

    def test_filters_reset_to_default(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        filtered_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        cleared = with_filters_cleared(filtered_ctx)
        assert cleared.filters == FilterState()

    def test_provenance_format(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        # Apply filter first so clear is not a no-op
        filtered = sample_df[sample_df["a"] > 1]
        filtered_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        cleared = with_filters_cleared(filtered_ctx)
        assert cleared.provenance[-1] == "filters:cleared"

    def test_raw_df_unchanged(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        filtered_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        cleared = with_filters_cleared(filtered_ctx)
        pd.testing.assert_frame_equal(cleared.raw_df, sample_df)

    def test_source_id_unchanged(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        filtered_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        cleared = with_filters_cleared(filtered_ctx)
        assert cleared.source_id == ctx.source_id

    def test_truncated_unchanged(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "p1", truncated=True)
        cleared = with_filters_cleared(ctx)
        assert cleared.truncated is True

    # ── No-op tests ──────────────────────────────────────────────────────

    def test_noop_no_filters_active(self, sample_df, sample_bytes):
        """Clearing when no filters are active returns the original context."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        result = with_filters_cleared(ctx)
        assert result is ctx

    def test_noop_after_clear(self, sample_df, sample_bytes):
        """Clearing twice: second call is a no-op."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        filtered_ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        cleared = with_filters_cleared(filtered_ctx)
        cleared_again = with_filters_cleared(cleared)
        assert cleared_again is cleared


# ── Integration: Multi-step Transitions ──────────────────────────────────────


class TestMultiStepTransitions:
    def test_full_lifecycle(self, sample_df, sample_bytes):
        """Upload → filter → clear → custom metrics → filter → clear (preserves metrics)."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        assert ctx.version == 0
        assert ctx.provenance[-1].startswith("upload")

        # Filter
        filtered = sample_df[sample_df["a"] > 1]
        ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        assert ctx.version == 1
        assert ctx.filters.is_active is True
        assert ctx.provenance[-1] == "filters:a > 1"

        # Clear filters (should be no-op on custom metrics since none applied)
        ctx2 = with_filters_cleared(ctx)
        assert ctx2.version == 2
        # base_df still equals raw_df at this point
        pd.testing.assert_frame_equal(ctx2.active_df, ctx2.raw_df)

        # Custom metrics
        metrics_df = ctx2.active_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        ctx = with_custom_metrics(ctx2, metrics_df)
        assert ctx.version == 3
        assert "total" in ctx.base_df.columns
        assert ctx.provenance[-1] == "custom_metrics:applied"

        # Filter again on custom-metrics data
        filtered = ctx.active_df[ctx.active_df["total"] > 6]
        ctx = with_filtered_data(ctx, filtered, ("total > 6",))
        assert ctx.version == 4

        # Clear filters — must restore base_df (with "total"), not raw_df
        ctx = with_filters_cleared(ctx)
        assert ctx.version == 5
        assert "total" in ctx.active_df.columns
        assert ctx.filters == FilterState()

    def test_version_monotonic(self, sample_df, sample_bytes):
        """Version never decreases across transitions, even with no-ops."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        versions = [ctx.version]  # 0

        filtered = sample_df[sample_df["a"] > 1]
        ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        versions.append(ctx.version)  # 1

        ctx = with_filters_cleared(ctx)
        versions.append(ctx.version)  # 2

        # Add an actual new column — a plain copy would be a no-op
        metrics_df = ctx.active_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        ctx = with_custom_metrics(ctx, metrics_df)
        versions.append(ctx.version)  # 3 (not a no-op — new column)

        for i in range(1, len(versions)):
            assert versions[i] > versions[i - 1]

    def test_cache_keys_are_unique(self, sample_df, sample_bytes):
        """Each transition produces a unique cache_key."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        keys = {ctx.cache_key}

        filtered = sample_df[sample_df["a"] > 1]
        ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        keys.add(ctx.cache_key)

        ctx = with_filters_cleared(ctx)
        keys.add(ctx.cache_key)

        assert len(keys) == 3

    def test_noop_preserves_cache_key(self, sample_df, sample_bytes):
        """No-ops return same context, so cache_key is identical."""
        ctx = create_context_from_upload(sample_df, sample_bytes)
        result = with_filters_cleared(ctx)
        assert result.cache_key == ctx.cache_key
        assert result is ctx


# ── Provenance Contract ──────────────────────────────────────────────────────


class TestProvenanceContract:
    """All provenance entries must match category:detail or category format."""

    PROVENANCE_RE = r"^[a-z0-9_]+(:.+)?$"

    def _check_provenance(self, *entries: str) -> None:
        import re

        pattern = re.compile(self.PROVENANCE_RE)
        for entry in entries:
            assert pattern.match(entry), f"Provenance entry '{entry}' does not match format"

    def test_upload_provenance(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes, "test.csv")
        self._check_provenance(*ctx.provenance)

    def test_ga4_provenance(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "123")
        self._check_provenance(*ctx.provenance)

    def test_transition_provenance(self, sample_df, sample_bytes):
        ctx = create_context_from_upload(sample_df, sample_bytes)
        filtered = sample_df[sample_df["a"] > 1]
        ctx = with_filtered_data(ctx, filtered, ("a > 1",))
        ctx = with_filters_cleared(ctx)
        metrics = ctx.active_df.copy()
        ctx = with_custom_metrics(ctx, metrics)
        self._check_provenance(*ctx.provenance)
