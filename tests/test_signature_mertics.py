"""Test duckdb metric queries."""
import numpy as np
import teehr.queries.duckdb as tqu
import teehr.queries.pandas as tqp
from pathlib import Path


PRIMARY_FILEPATH = Path("tests/data/retro/primary_obs.parquet")
SECONDARY_FILEPATH = Path("tests/data/retro/secondary_sim.parquet")
CROSSWALK_FILEPATH = Path("tests/data/retro/xwalk.parquet")


def test_annual_peak_flow_bias():
    """Tests the newly added annual_peak_flow_bias"""

    include_metrics = ['annual_peak_relative_bias']
    group_by = [
        "primary_location_id",
        "configuration"
    ]

    pandas_df = tqp.get_metrics(
        primary_filepath=PRIMARY_FILEPATH,
        secondary_filepath=SECONDARY_FILEPATH,
        crosswalk_filepath=CROSSWALK_FILEPATH,
        include_metrics=include_metrics,
        group_by=group_by,
        order_by=group_by,
    )

    duckdb_df = tqu.get_metrics(
        primary_filepath=PRIMARY_FILEPATH,
        secondary_filepath=SECONDARY_FILEPATH,
        crosswalk_filepath=CROSSWALK_FILEPATH,
        include_metrics=include_metrics,
        group_by=group_by,
        order_by=group_by,
    )

    for m in include_metrics:
        duckdb_np = duckdb_df[m].to_numpy()
        pandas_np = pandas_df[m].to_numpy()
        assert np.allclose(duckdb_np, pandas_np)


if __name__ == "__main__":

    test_annual_peak_flow_bias()
    pass
