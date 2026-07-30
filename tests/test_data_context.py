"""Tests for utils/data_context.py — DataContext, FilterState, factories, transitions."""

import pandas as pd
import pytest

from utils.data_context import (
    DataContext,
    FilterState,
    create_context_from_upload,
    create_context_from_ga4,
    with_filtered_data,
    with_custom_metrics,
    with_filters_cleared,
)


# ── Test Data ────────────────────────────────────────────────────────────────


@pytest.fixture
def sample_df():
    return pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6], "c": ["x", "y", "z"]})


@pytest.fixture
def small_df():
    return pd.DataFrame({"x": [10, 20]})


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


# ── DataContext ──────────────────────────────────────────────────────────────


class TestDataContext:
    def test_creation(self, sample_df):
        ctx = DataContext(
            source_id="test:1",
            version=0,
            raw_df=sample_df,
            active_df=sample_df,
            provenance=("created",),
        )
        assert ctx.source_id == "test:1"
        assert ctx.version == 0
        assert ctx.filters == FilterState()
        assert ctx.provenance == ("created",)
        assert ctx.truncated is False

    def test_cache_key(self, sample_df):
        ctx = DataContext(
            source_id="file:report.csv",
            version=3,
            raw_df=sample_df,
            active_df=sample_df,
        )
        assert ctx.cache_key == "file:report.csv:v3"

    def test_frozen_prevents_attribute_mutation(self, sample_df):
        ctx = DataContext(
            source_id="test:1",
            version=0,
            raw_df=sample_df,
            active_df=sample_df,
        )
        with pytest.raises(AttributeError):
            ctx.version = 5  # type: ignore[misc]

    def test_truncated_flag(self, sample_df):
        ctx = DataContext(
            source_id="ga4:123",
            version=0,
            raw_df=sample_df,
            active_df=sample_df,
            truncated=True,
        )
        assert ctx.truncated is True


# ── create_context_from_upload ───────────────────────────────────────────────


class TestCreateContextFromUpload:
    def test_source_id_format(self, sample_df):
        ctx = create_context_from_upload(sample_df, "Q3_report.xlsx")
        assert ctx.source_id == "file:Q3_report.xlsx"

    def test_version_starts_at_zero(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        assert ctx.version == 0

    def test_raw_and_active_are_copies(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        # DataFrames should be equal but not the same object
        pd.testing.assert_frame_equal(ctx.raw_df, sample_df)
        pd.testing.assert_frame_equal(ctx.active_df, sample_df)
        assert ctx.raw_df is not sample_df  # defensive copy

    def test_provenance(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        assert ctx.provenance == ("uploaded",)

    def test_truncated_defaults_false(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        assert ctx.truncated is False


# ── create_context_from_ga4 ──────────────────────────────────────────────────


class TestCreateContextFromGA4:
    def test_source_id_format(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "properties/123")
        assert ctx.source_id == "ga4:properties/123"

    def test_version_starts_at_zero(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "properties/456")
        assert ctx.version == 0

    def test_provenance(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "properties/789")
        assert ctx.provenance == ("ga4-pull",)

    def test_truncated_true(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "p1", truncated=True)
        assert ctx.truncated is True

    def test_truncated_defaults_false(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "p1")
        assert ctx.truncated is False


# ── with_filtered_data ───────────────────────────────────────────────────────


class TestWithFilteredData:
    def test_version_increments(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        new_ctx = with_filtered_data(ctx, filtered, fs)
        assert new_ctx.version == ctx.version + 1

    def test_active_df_is_filtered(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        new_ctx = with_filtered_data(ctx, filtered, fs)
        pd.testing.assert_frame_equal(new_ctx.active_df, filtered)

    def test_raw_df_unchanged(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        new_ctx = with_filtered_data(ctx, filtered, fs)
        pd.testing.assert_frame_equal(new_ctx.raw_df, ctx.raw_df)

    def test_source_id_unchanged(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        new_ctx = with_filtered_data(ctx, filtered, fs)
        assert new_ctx.source_id == ctx.source_id

    def test_provenance_appended(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        new_ctx = with_filtered_data(ctx, filtered, fs)
        assert "filters-applied" in new_ctx.provenance
        assert new_ctx.provenance[-1] == "filters-applied"

    def test_zero_row_filter_preserved(self, sample_df):
        """Zero-row filter result is preserved as empty active_df, not None."""
        ctx = create_context_from_upload(sample_df, "data.csv")
        empty_df = pd.DataFrame(columns=sample_df.columns)
        fs = FilterState(descriptions=("a > 999",), is_active=True, row_count=0)
        new_ctx = with_filtered_data(ctx, empty_df, fs)
        assert new_ctx.active_df is not None
        assert len(new_ctx.active_df) == 0
        assert new_ctx.filters.is_active is True
        assert new_ctx.filters.row_count == 0

    def test_filtered_df_is_defensive_copy(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        new_ctx = with_filtered_data(ctx, filtered, fs)
        assert new_ctx.active_df is not filtered  # defensive copy


# ── with_custom_metrics ──────────────────────────────────────────────────────


class TestWithCustomMetrics:
    def test_version_increments(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(ctx, metrics_df)
        assert new_ctx.version == ctx.version + 1

    def test_active_df_is_metrics_df(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(ctx, metrics_df)
        pd.testing.assert_frame_equal(new_ctx.active_df, metrics_df)

    def test_raw_df_unchanged(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(ctx, metrics_df)
        pd.testing.assert_frame_equal(new_ctx.raw_df, sample_df)

    def test_provenance_appended(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        metrics_df = sample_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        new_ctx = with_custom_metrics(ctx, metrics_df)
        assert new_ctx.provenance[-1] == "custom-metrics-applied"

    def test_source_id_unchanged(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        metrics_df = sample_df.copy()
        new_ctx = with_custom_metrics(ctx, metrics_df)
        assert new_ctx.source_id == ctx.source_id

    def test_filters_unchanged(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        metrics_df = sample_df.copy()
        new_ctx = with_custom_metrics(ctx, metrics_df)
        assert new_ctx.filters == ctx.filters

    def test_metrics_df_is_defensive_copy(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        metrics_df = sample_df.copy()
        new_ctx = with_custom_metrics(ctx, metrics_df)
        assert new_ctx.active_df is not metrics_df  # defensive copy


# ── with_filters_cleared ─────────────────────────────────────────────────────


class TestWithFiltersCleared:
    def test_version_increments(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        # Apply filters first
        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        filtered_ctx = with_filtered_data(ctx, filtered, fs)
        # Then clear
        cleared_ctx = with_filters_cleared(filtered_ctx)
        assert cleared_ctx.version == filtered_ctx.version + 1

    def test_active_df_reset_to_raw_df(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        filtered_ctx = with_filtered_data(ctx, filtered, fs)
        cleared_ctx = with_filters_cleared(filtered_ctx)
        pd.testing.assert_frame_equal(cleared_ctx.active_df, ctx.raw_df)

    def test_filters_reset_to_default(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        filtered_ctx = with_filtered_data(ctx, filtered, fs)
        cleared_ctx = with_filters_cleared(filtered_ctx)
        assert cleared_ctx.filters == FilterState()

    def test_provenance_appended(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        cleared_ctx = with_filters_cleared(ctx)
        assert cleared_ctx.provenance[-1] == "filters-cleared"

    def test_raw_df_unchanged(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        cleared_ctx = with_filters_cleared(ctx)
        pd.testing.assert_frame_equal(cleared_ctx.raw_df, sample_df)

    def test_source_id_unchanged(self, sample_df):
        ctx = create_context_from_upload(sample_df, "data.csv")
        cleared_ctx = with_filters_cleared(ctx)
        assert cleared_ctx.source_id == ctx.source_id

    def test_truncated_unchanged(self, sample_df):
        ctx = create_context_from_ga4(sample_df, "p1", truncated=True)
        cleared_ctx = with_filters_cleared(ctx)
        assert cleared_ctx.truncated is True


# ── Integration: Multi-step Transitions ──────────────────────────────────────


class TestMultiStepTransitions:
    def test_upload_filter_clear_chain(self, sample_df):
        """Full lifecycle: upload → filter → clear → custom metrics."""
        # Upload
        ctx = create_context_from_upload(sample_df, "report.csv")
        assert ctx.version == 0

        # Filter
        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        ctx = with_filtered_data(ctx, filtered, fs)
        assert ctx.version == 1
        assert ctx.filters.is_active is True

        # Clear filters
        ctx = with_filters_cleared(ctx)
        assert ctx.version == 2
        assert ctx.filters == FilterState()

        # Custom metrics
        metrics_df = ctx.active_df.copy()
        metrics_df["total"] = metrics_df["a"] + metrics_df["b"]
        ctx = with_custom_metrics(ctx, metrics_df)
        assert ctx.version == 3
        assert "total" in ctx.active_df.columns

    def test_version_monotonic(self, sample_df):
        """Version never decreases across transitions."""
        ctx = create_context_from_upload(sample_df, "data.csv")
        versions = [ctx.version]

        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        ctx = with_filtered_data(ctx, filtered, fs)
        versions.append(ctx.version)

        ctx = with_filters_cleared(ctx)
        versions.append(ctx.version)

        metrics_df = ctx.active_df.copy()
        ctx = with_custom_metrics(ctx, metrics_df)
        versions.append(ctx.version)

        # Version must be strictly increasing
        for i in range(1, len(versions)):
            assert versions[i] > versions[i - 1]

    def test_cache_key_changes_with_version(self, sample_df):
        """Each transition produces a unique cache_key."""
        ctx = create_context_from_upload(sample_df, "data.csv")
        keys = {ctx.cache_key}

        filtered = sample_df[sample_df["a"] > 1]
        fs = FilterState(descriptions=("a > 1",), is_active=True, row_count=2)
        ctx = with_filtered_data(ctx, filtered, fs)
        keys.add(ctx.cache_key)

        ctx = with_filters_cleared(ctx)
        keys.add(ctx.cache_key)

        # All keys should be unique
        assert len(keys) == 3
