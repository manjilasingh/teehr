"""A module defining duckdb sql queries for a persistent database."""
import duckdb

from typing import Dict

from teehr.models.queries_database import (
    MetricQuery,
    # InsertJoinedTimeseriesQuery,
    JoinedTimeseriesQuery,
    TimeseriesQuery,
    TimeseriesCharQuery,
    JoinedTimeseriesFieldName
)

import teehr.queries.utils as tqu

SQL_DATETIME_STR_FORMAT = "%Y-%m-%d %H:%M:%S"


def create_get_metrics_query(mq: MetricQuery) -> str:
    """Build the query string to calculate performance metrics.

    Parameters
    ----------
    mq : MetricQuery
        Pydantic model containing query parameters.

    Returns
    -------
    str
        The query string.

    Notes
    -----
    Filter, Order By and Group By Fields:

    * reference_time
    * primary_location_id
    * secondary_location_id
    * primary_value
    * secondary_value
    * value_time
    * configuration
    * measurement_unit
    * variable_name
    * lead_time
    * [any user-added fields]

    Metrics:

    * primary_count
    * secondary_count
    * primary_minimum
    * secondary_minimum
    * primary_maximum
    * secondary_maximum
    * primary_average
    * secondary_average
    * primary_sum
    * secondary_sum
    * primary_variance
    * secondary_variance
    * max_value_delta
    * mean_error
    * mean_absolute_error
    * mean_squared_error
    * mean_absolute_relative_error
    * root_mean_squared_error
    * relative_bias
    * multiplicative_bias
    * pearson_correlation
    * r_squared
    * nash_sutcliffe_efficiency
    * nash_sutcliffe_efficiency_normalized
    * kling_gupta_efficiency
    * primary_max_value_time
    * secondary_max_value_time
    * max_value_timedelta

    Examples
    --------
    >>> order_by = ["lead_time", "primary_location_id"]

    >>> group_by = ["lead_time", "primary_location_id"]

    >>> filters = [
    >>>     {
    >>>         "column": "primary_location_id",
    >>>         "operator": "=",
    >>>         "value": "gage-A",
    >>>     },
    >>>     {
    >>>         "column": "reference_time",
    >>>         "operator": "=",
    >>>         "value": "2022-01-01 00:00:00",
    >>>     },
    >>>     {"column": "lead_time", "operator": "<=", "value": "10 hours"},
    >>> ]
    """
    query = f"""
        WITH joined as (
            SELECT
                *
            FROM joined_timeseries sf
            {tqu.filters_to_sql(mq.filters)}
        )
        {tqu._nse_cte(mq)}
        {tqu._annual_metrics_cte(mq)}
        {tqu._spearman_ranks_cte(mq)}
        , metrics AS (
            SELECT
                {",".join([f"joined.{gb}" for gb in mq.group_by])}
                {tqu._select_primary_count(mq)}
                {tqu._select_secondary_count(mq)}
                {tqu._select_primary_minimum(mq)}
                {tqu._select_secondary_minimum(mq)}
                {tqu._select_primary_maximum(mq)}
                {tqu._select_secondary_maximum(mq)}
                {tqu._select_primary_average(mq)}
                {tqu._select_secondary_average(mq)}
                {tqu._select_primary_sum(mq)}
                {tqu._select_secondary_sum(mq)}
                {tqu._select_primary_variance(mq)}
                {tqu._select_secondary_variance(mq)}
                {tqu._select_max_value_delta(mq)}
                {tqu._select_mean_error(mq)}
                {tqu._select_nash_sutcliffe_efficiency(mq)}
                {tqu._select_nash_sutcliffe_efficiency_normalized(mq)}
                {tqu._select_kling_gupta_efficiency(mq)}
                {tqu._select_kling_gupta_efficiency_mod1(mq)}
                {tqu._select_kling_gupta_efficiency_mod2(mq)}
                {tqu._select_mean_absolute_error(mq)}
                {tqu._select_mean_squared_error(mq)}
                {tqu._select_root_mean_squared_error(mq)}
                {tqu._select_primary_max_value_time(mq)}
                {tqu._select_secondary_max_value_time(mq)}
                {tqu._select_max_value_timedelta(mq)}
                {tqu._select_relative_bias(mq)}
                {tqu._select_multiplicative_bias(mq)}
                {tqu._select_mean_absolute_relative_error(mq)}
                {tqu._select_pearson_correlation(mq)}
                {tqu._select_r_squared(mq)}
                {tqu._select_spearman_correlation(mq)}
            FROM
                joined
                {tqu._join_nse_cte(mq)}
                {tqu._join_spearman_ranks_cte(mq)}
            GROUP BY
                {",".join([f"joined.{gb}" for gb in mq.group_by])}
        )
        SELECT
            {",".join([f"metrics.{ob}" for ob in mq.group_by])}
            {tqu.metrics_select_clause(mq)}
            {tqu.geometry_select_clause(mq)}
        FROM metrics
            {tqu.metric_geometry_join_clause_db(mq)}
            {tqu._join_annual_metrics_cte(mq)}
        ORDER BY
            {",".join([f"metrics.{ob}" for ob in mq.order_by])}
    ;"""

    return query


def create_join_and_save_timeseries_query(jtq: JoinedTimeseriesQuery) -> str:
    """Load joined timeseries into a duckdb persistent database.

    Parameters
    ----------
    jtq : JoinedTimeseriesQuery
        Pydantic model containing query parameters.

    Returns
    -------
    str
        The query string.
    """
    query = f"""
    WITH initial_joined as (
        SELECT
            sf.reference_time,
            sf.value_time,
            sf.location_id as secondary_location_id,
            sf.value as secondary_value,
            sf.configuration,
            sf.measurement_unit,
            pf.reference_time as primary_reference_time,
            sf.variable_name,
            pf.value as primary_value,
            pf.location_id as primary_location_id,
            sf.value_time - sf.reference_time as lead_time,
            abs(primary_value - secondary_value) as absolute_difference
        FROM read_parquet('{str(jtq.secondary_filepath)}') sf
        JOIN read_parquet('{str(jtq.crosswalk_filepath)}') cf
            on cf.secondary_location_id = sf.location_id
        JOIN read_parquet("{str(jtq.primary_filepath)}") pf
            on cf.primary_location_id = pf.location_id
            and sf.value_time = pf.value_time
            and sf.measurement_unit = pf.measurement_unit
            and sf.variable_name = pf.variable_name
    ),
    joined AS (
        SELECT
            reference_time
            , value_time
            , secondary_location_id
            , secondary_value
            , configuration
            , measurement_unit
            , variable_name
            , primary_value
            , primary_location_id
            , lead_time
            , absolute_difference
        FROM(
            SELECT *,
                row_number()
            OVER(
                PARTITION BY value_time,
                             primary_location_id,
                             configuration,
                             variable_name,
                             measurement_unit,
                             reference_time
                ORDER BY primary_reference_time desc
                ) AS rn
            FROM initial_joined
            )
        WHERE rn = 1
    )
    INSERT INTO joined_timeseries
    SELECT
        *
    FROM
        joined
    ORDER BY
        {",".join(jtq.order_by)}
    ;"""

    return query


def describe_timeseries(timeseries_filepath: str) -> Dict:
    r"""Retrieve descriptive stats for a time series.

    Parameters
    ----------
    timeseries_filepath : str
        File path to the "observed" data.  String must include path to file(s)
        and can include wildcards. For example, "/path/to/parquet/\\*.parquet".

    Returns
    -------
    Dict
        A dictionary of summary statistics for a timeseries.
    """
    # Find number of rows and unique locations
    query = f"""
        SELECT
        COUNT ( DISTINCT
            location_id
        )
        AS num_location_ids,
        COUNT(*) AS num_rows,
        MAX(value_time) as end_date,
        MIN(value_time) as start_date
        FROM read_parquet("{timeseries_filepath}")
        """
    df = duckdb.sql(query).to_df()
    num_location_ids = df["num_location_ids"][0]
    total_num_rows = df["num_rows"][0]
    start_date = df["start_date"][0]
    end_date = df["end_date"][0]

    # Find number of duplicates from all columns
    query = f"""
        SELECT
            value_time,
            location_id,
            value,
            measurement_unit,
            reference_time,
            configuration,
            variable_name,
        COUNT(*)
        FROM read_parquet("{timeseries_filepath}")
        GROUP BY
            value_time,
            location_id,
            value,
            measurement_unit,
            reference_time,
            configuration,
            variable_name,
        HAVING COUNT(*) > 1
        """
    df = duckdb.sql(query).to_df()
    num_duplicate_rows = df.index.size

    # Find number of duplicate value_times per location_id
    query = f"""
        WITH find_duplicates AS (
            SELECT
                value_time,
                location_id,
                measurement_unit,
                configuration,
                variable_name,
            COUNT(*) AS num_duplicates
            FROM read_parquet("{timeseries_filepath}")
            GROUP BY
                value_time,
                location_id,
                measurement_unit,
                configuration,
                variable_name,
            HAVING COUNT(*) > 1
        )
        SELECT
        COUNT( DISTINCT location_id)
        AS num_locations_with_duplicates
        FROM find_duplicates
        WHERE num_duplicates > 1
        """
    df = duckdb.sql(query).to_df()
    num_locations_with_duplicate_value_times = df[
        "num_locations_with_duplicates"
    ][0]

    # Check time step integrity by reference_time and location_id
    query = f"""
        WITH value_time_diff AS (
            SELECT *,
                value_time - LAG(value_time)
            OVER(PARTITION BY
                location_id,
                reference_time
            ORDER BY value_time)
            AS value_time_step
            FROM read_parquet("{timeseries_filepath}")
        ),
        missing_timesteps AS (
            SELECT
                location_id,
                reference_time,
                MAX(value_time_step) AS max_timestep,
                MIN(value_time_step) AS min_timestep,
                max_timestep = min_timestep AS none_missing
            FROM value_time_diff
            GROUP BY location_id, reference_time
        )
            SELECT
                location_id,
                reference_time,
                none_missing
            FROM missing_timesteps
            WHERE none_missing != TRUE
        """
    df = duckdb.sql(query).to_df()
    num_locations_with_missing_timesteps = df.index.size

    output_report = {
        "Number of unique location IDs": num_location_ids,
        "Total number of rows": total_num_rows,
        "Start Date": start_date,
        "End Date": end_date,
        "Number of duplicate rows": num_duplicate_rows,
        "Number of location IDs with duplicate value times":
            num_locations_with_duplicate_value_times,
        "Number of location IDs with missing time steps":
            num_locations_with_missing_timesteps,
    }

    return output_report


def create_get_joined_timeseries_query(
    jtq: JoinedTimeseriesQuery
) -> str:
    """Retrieve joined timeseries using database query.

    Parameters
    ----------
    jtq : JoinedTimeseriesQuery
        Pydantic model containing query parameters.

    Returns
    -------
    str
        The query string.

    Notes
    -----
    Filter By Fields:

    * reference_time
    * primary_location_id
    * secondary_location_id
    * primary_value
    * secondary_value
    * value_time
    * configuration
    * measurement_unit
    * variable_name
    * lead_time
    * absolute_difference
    * [any user-added fields]

    Order By Fields:

    * reference_time
    * primary_location_id
    * secondary_location_id
    * primary_value
    * secondary_value
    * value_time
    * configuration
    * measurement_unit
    * variable_name

    Examples
    --------
    >>> order_by = ["lead_time", "primary_location_id"]

    >>> group_by = ["lead_time", "primary_location_id"]

    >>> filters = [
    >>>     {
    >>>         "column": "primary_location_id",
    >>>         "operator": "=",
    >>>         "value": "gage-A",
    >>>     },
    >>>     {
    >>>         "column": "reference_time",
    >>>         "operator": "=",
    >>>         "value": "2022-01-01 00:00:00",
    >>>     },
    >>>     {"column": "lead_time", "operator": "<=", "value": "10 hours"},
    >>> ]
    """
    query = f"""
        SELECT
            sf.*
        {tqu.geometry_select_clause(jtq)}
        FROM
            joined_timeseries sf
        {tqu.metric_geometry_join_clause_db(jtq)}
        {tqu.filters_to_sql(jtq.filters)}
        ORDER BY
            {",".join(jtq.order_by)}
    ;"""

    return query


def create_get_timeseries_query(
    tq: TimeseriesQuery
) -> str:
    """Retrieve joined timeseries using database query.

    Parameters
    ----------
    tq : TimeseriesQuery
        Pydantic model containing query parameters.

    Returns
    -------
    str
        The query string.

    Notes
    -----
    Filter By Fields:

    * reference_time
    * primary_location_id
    * secondary_location_id
    * primary_value
    * secondary_value
    * value_time
    * configuration
    * measurement_unit
    * variable_name
    * lead_time
    * absolute_difference
    * [any user-added fields]

    Order By Fields:

    * reference_time
    * primary_location_id
    * secondary_location_id
    * primary_value
    * secondary_value
    * value_time
    * configuration
    * measurement_unit
    * variable_name

    Examples
    --------
    >>> order_by = ["lead_time", "primary_location_id"]

    >>> group_by = ["lead_time", "primary_location_id"]

    >>> filters = [
    >>>     {
    >>>         "column": "primary_location_id",
    >>>         "operator": "=",
    >>>         "value": "gage-A",
    >>>     },
    >>>     {
    >>>         "column": "reference_time",
    >>>         "operator": "=",
    >>>         "value": "2022-01-01 00:00:00",
    >>>     },
    >>>     {"column": "lead_time", "operator": "<=", "value": "10 hours"},
    >>> ]
    """
    if tq.timeseries_name == "primary":
        query = f"""
            SELECT
                ANY_VALUE(reference_time) AS reference_time,
                ANY_VALUE(primary_value) AS value,
                value_time,
                primary_location_id AS location_id,
                'primary' as configuration,
                measurement_unit,
                variable_name,
            FROM
                joined_timeseries sf
            {tqu.filters_to_sql(tq.filters)}
            GROUP BY
                value_time,
                primary_location_id,
                --configuration,
                measurement_unit,
                variable_name,
            ORDER BY
                {",".join(tq.order_by)}
        ;"""
    else:
        query = f"""
            SELECT
                reference_time,
                value_time,
                secondary_location_id AS location_id,
                secondary_value AS value,
                configuration,
                measurement_unit,
                variable_name,
            FROM
                joined_timeseries sf
            {tqu.filters_to_sql(tq.filters)}
            ORDER BY
                {",".join(tq.order_by)}
        ;"""

    return query


def create_get_timeseries_char_query(tcq: TimeseriesCharQuery) -> str:
    """Retrieve joined timeseries using database query.

    Parameters
    ----------
    tcq : TimeseriesCharQuery
        Pydantic model containing query parameters.

    Returns
    -------
    str
        The query string.

    Notes
    -----
    Filter, Order By and Group By Fields

    * reference_time
    * primary_location_id
    * secondary_location_id
    * primary_value
    * secondary_value
    * value_time
    * configuration
    * measurement_unit
    * variable_name
    * lead_time
    * [any user-added fields]

    Examples
    --------
    >>> order_by = ["lead_time", "primary_location_id"]

    >>> group_by = ["lead_time", "primary_location_id"]

    >>> filters = [
    >>>     {
    >>>         "column": "primary_location_id",
    >>>         "operator": "=",
    >>>         "value": "gage-A",
    >>>     },
    >>>     {
    >>>         "column": "reference_time",
    >>>         "operator": "=",
    >>>         "value": "2022-01-01 00:00:00",
    >>>     },
    >>>     {"column": "lead_time", "operator": "<=", "value": "10 hours"},
    >>> ]
    """
    join_max_time_on = tqu._join_time_on(
        join="mxt", join_to="chars", join_on=tcq.group_by
    )

    order_by = [f"chars.{val}" for val in tcq.order_by]

    # Create the fts_clause to remove duplicates if primary time series
    # has been specified
    if tcq.timeseries_name == "primary":

        selected_primary_fields = ["reference_time",
                                   "primary_value",
                                   "value_time",
                                   "primary_location_id",
                                   "configuration",
                                   "measurement_unit",
                                   "variable_name"]
        # Format any group by fields that are not selected
        # by default
        gb_fields = ""
        for gb_fld in tcq.group_by:
            if gb_fld not in selected_primary_fields:
                gb_fields += f"ANY_VALUE({gb_fld}) as {gb_fld}, "

        fts_clause = f"""
                     SELECT
                        ANY_VALUE(reference_time) AS reference_time,
                        ANY_VALUE(primary_value) AS primary_value,
                        value_time,
                        primary_location_id,
                        'primary' as configuration,
                        measurement_unit,
                        variable_name,
                        {gb_fields}
                     FROM
                         joined_timeseries sf
                     {tqu.filters_to_sql(tcq.filters)}
                     GROUP BY
                        value_time,
                        primary_location_id,
                        --configuration,
                        measurement_unit,
                        variable_name,
                    """
    else:
        fts_clause = f"""
                      SELECT
                        *
                      FROM
                          joined_timeseries sf
                      {tqu.filters_to_sql(tcq.filters)}
                      """

    query = f"""
        WITH fts AS (
            {fts_clause}
        ),
        mxt AS (
            SELECT
                {",".join(tcq.group_by)}
                , {tcq.timeseries_name}_value
                , value_time
                , ROW_NUMBER() OVER(
                    PARTITION BY {",".join(tcq.group_by)}
                    ORDER BY {tcq.timeseries_name}_value DESC, value_time
                ) as n
            FROM fts
        ),
        chars AS (
            SELECT
                {",".join(tcq.group_by)}
                ,count(fts.{tcq.timeseries_name}_value) as count
                ,min(fts.{tcq.timeseries_name}_value) as min
                ,max(fts.{tcq.timeseries_name}_value) as max
                ,avg(fts.{tcq.timeseries_name}_value) as average
                ,sum(fts.{tcq.timeseries_name}_value) as sum
                ,var_pop(fts.{tcq.timeseries_name}_value) as variance
            FROM
                fts
            GROUP BY
                {",".join(tcq.group_by)}
        )
        SELECT
            chars.{tcq.timeseries_name}_location_id as location_id,
            chars.count,
            chars.min,
            chars.max,
            chars.average,
            chars.sum,
            chars.variance,
            mxt.value_time as max_value_time
        FROM chars
            {join_max_time_on}
        ORDER BY
            {",".join(order_by)}
    ;"""

    return query


def create_unique_field_values_query(fn: JoinedTimeseriesFieldName) -> str:
    """Create a query for identifying unique values in a field.

    Parameters
    ----------
    fn : JoinedTimeseriesFieldName
        Name of the field to query for unique values.

    Returns
    -------
    str
        The query string.
    """
    query = f"""
        SELECT
        DISTINCT
            {fn.field_name}
        AS unique_{fn.field_name}_values,
        FROM
            joined_timeseries
        ORDER BY
            {fn.field_name}
        """

    return query
