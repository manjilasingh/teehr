from datetime import datetime

import pandas as pd
import pytest
import teehr.models as tm
from pydantic import ValidationError
import teehr.queries.duckdb as tqd


def test_multiple_filters():
    filter_1 = tm.Filter(
        column="secondary_location_id", 
        operator="in", 
        value=["123456", "9876543"]
    )
    filter_2 = tm.Filter(
        column="reference_time", 
        operator="=", 
        value=datetime(2023, 1, 1, 0, 0, 0)
    )
    filter_str = tqd.filters_to_sql([filter_1, filter_2])
    assert filter_str == "WHERE secondary_location_id in ('123456','9876543') AND reference_time = '2023-01-01 00:00:00'"


def test_no_filters():
    filter_str = tqd.filters_to_sql([])
    assert filter_str == "--no where clause"


if __name__ == "__main__":
    test_multiple_filters()
    test_no_filters()
    pass