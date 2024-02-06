from pathlib import Path

from teehr.database.teehr_dataset import TEEHRDatasetAPI
from teehr.models.queries_database import (
    MetricQuery,
    JoinedTimeseriesFieldName,
    JoinedTimeseriesQuery
)

# Test data
TEST_STUDY_DIR = Path("tests", "data", "test_study")
PRIMARY_FILEPATH = Path(TEST_STUDY_DIR, "timeseries", "*short_obs.parquet")
SECONDARY_FILEPATH = Path(TEST_STUDY_DIR, "timeseries", "*_fcast.parquet")
CROSSWALK_FILEPATH = Path(TEST_STUDY_DIR, "geo", "crosswalk.parquet")
GEOMETRY_FILEPATH = Path(TEST_STUDY_DIR, "geo", "gages.parquet")
ATTRIBUTES_FILEPATH = Path(TEST_STUDY_DIR, "geo", "test_attr.parquet")
DATABASE_FILEPATH = Path("tests", "data", "test_study", "temp_test_api.db")


def test_unique_field_values():
    tds = TEEHRDatasetAPI(DATABASE_FILEPATH)

    jtn = JoinedTimeseriesFieldName.model_validate(
        {"field_name": "primary_location_id"}
    )

    df = tds.get_unique_field_values(jtn)
    assert sorted(df["unique_primary_location_id_values"].tolist()) == [
        "gage-A",
        "gage-B",
        "gage-C",
    ]


def test_metrics_query():
    tds = TEEHRDatasetAPI(DATABASE_FILEPATH)

    # Get metrics
    order_by = ["lead_time", "primary_location_id"]
    group_by = ["lead_time", "primary_location_id"]
    filters = [
        {
            "column": "primary_location_id",
            "operator": "=",
            "value": "gage-A",
        },
        {
            "column": "reference_time",
            "operator": "=",
            "value": "2022-01-01 00:00:00",
        },
        {"column": "lead_time", "operator": "<=", "value": "10 hours"},
    ]

    mq = MetricQuery.model_validate(
        {
            "group_by": group_by,
            "order_by": order_by,
            "include_metrics": "all",
            "filters": filters,
            "include_geometry": True,
        },
    )
    df = tds.get_metrics(mq)
    assert df.index.size == 11


def test_describe_inputs():
    tds = TEEHRDatasetAPI(DATABASE_FILEPATH)
    df = tds.describe_inputs(PRIMARY_FILEPATH, SECONDARY_FILEPATH)
    assert df.index.size == 7


def test_get_joined_timeseries():
    tds = TEEHRDatasetAPI(DATABASE_FILEPATH)
    order_by = ["primary_location_id"]
    filters = [
        {
            "column": "primary_location_id",
            "operator": "=",
            "value": "gage-A",
        },
        {
            "column": "reference_time",
            "operator": "=",
            "value": "2022-01-01 00:00:00",
        },
        {"column": "lead_time", "operator": "<=", "value": "10 hours"},
    ]

    jtq = JoinedTimeseriesQuery.model_validate(
        {
            "order_by": order_by,
            "filters": filters,
            "include_geometry": False,
        },
    )

    df = tds.get_joined_timeseries(jtq)

    assert df.index.size == 11


if __name__ == "__main__":
    test_unique_field_values()
    test_describe_inputs()
    test_metrics_query()
    test_get_joined_timeseries()
