"""Module defining shared functions for processing NWM point data."""
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
import re

import dask
import numpy as np
import pandas as pd
import pyarrow as pa

from teehr.loading.nwm.utils import (
    get_dataset,
    write_parquet_file,
)


@dask.delayed
def file_chunk_loop(
    row: Tuple,
    location_ids: np.array,
    variable_name: str,
    configuration: str,
    schema: pa.Schema,
    ignore_missing_file: bool,
    units_format_dict: Dict,
    nwm_version: str
):
    """Fetch NWM values and convert to tabular format for a single json."""
    ds = get_dataset(
        row.filepath,
        ignore_missing_file,
        target_options={'anon': True}
    )
    if not ds:
        return None
    ds = ds.sel(feature_id=location_ids)
    vals = ds[variable_name].astype("float32").values
    nwm22_units = ds[variable_name].units
    teehr_units = units_format_dict.get(nwm22_units, nwm22_units)
    ref_time = pd.to_datetime(row.day) \
        + pd.to_timedelta(int(row.z_hour[1:3]), unit="h")

    valid_time = ds.time.values
    feature_ids = ds.feature_id.astype("int32").values
    teehr_location_ids = \
        [f"{nwm_version}-{feat_id}" for feat_id in feature_ids]
    num_vals = vals.size

    output_table = pa.table(
        {
            "value": vals,
            "reference_time": np.full(vals.shape, ref_time),
            "location_id": teehr_location_ids,
            "value_time": np.full(vals.shape, valid_time),
            "configuration": num_vals * [configuration],
            "variable_name": num_vals * [variable_name],
            "measurement_unit": num_vals * [teehr_units],
        },
        schema=schema,
    )

    return output_table


def process_chunk_of_files(
    df: pd.DataFrame,
    location_ids: Iterable[int],
    configuration: str,
    variable_name: str,
    output_parquet_dir: str,
    process_by_z_hour: bool,
    ignore_missing_file: bool,
    units_format_dict: Dict,
    overwrite_output: bool,
    nwm_version: str
):
    """Assemble a table for a chunk of NWM files."""
    location_ids = np.array(location_ids).astype(int)

    schema = pa.schema(
        [
            ("value", pa.float32()),
            ("reference_time", pa.timestamp("ms")),
            ("location_id", pa.string()),
            ("value_time", pa.timestamp("ms")),
            ("configuration", pa.string()),
            ("variable_name", pa.string()),
            ("measurement_unit", pa.string()),
        ]
    )

    results = []
    for row in df.itertuples():
        results.append(
            file_chunk_loop(
                row,
                location_ids,
                variable_name,
                configuration,
                schema,
                ignore_missing_file,
                units_format_dict,
                nwm_version
            )
        )
    output = dask.compute(*results)

    if not any(output):
        raise FileNotFoundError("No NWM files for specified input"
                                "configuration were found in GCS!")

    output = [tbl for tbl in output if tbl is not None]
    output_table = pa.concat_tables(output)

    if process_by_z_hour:
        row = df.iloc[0]
        filename = f"{row.day}T{row.z_hour[1:3]}.parquet"
    else:
        # Use start and end dates including forecast hour
        #  for the output file name.
        filepath_list = df.filepath.sort_values().tolist()
        start_json = filepath_list[0].split("/")[-1].split(".")
        start = f"{start_json[1]}T{start_json[3][1:3]}F{start_json[6][1:]}"
        end_json = filepath_list[-1].split("/")[-1].split(".")
        end = f"{end_json[1]}T{end_json[3][1:3]}F{end_json[6][1:]}"
        filename = f"{start}_{end}.parquet"

    write_parquet_file(
        Path(output_parquet_dir, filename),
        overwrite_output,
        output_table
    )


def fetch_and_format_nwm_points(
    json_paths: List[str],
    location_ids: Iterable[int],
    configuration: str,
    variable_name: str,
    output_parquet_dir: str,
    process_by_z_hour: bool,
    stepsize: int,
    ignore_missing_file: bool,
    units_format_dict: Dict,
    overwrite_output: bool,
    nwm_version: str
):
    """Fetch NWM point data and save as parquet files.

    Read in previously generated Kerchunk reference jsons,
    subset the NWM data based on provided location IDs, and format
    and save to parquet files in the TEEHR data model using Dask.

    Parameters
    ----------
    json_paths : list
        List of the single json reference filepaths.
    location_ids : Iterable[int]
        Array specifying NWM IDs of interest.
    configuration : str
        NWM forecast category.
    variable_name : str
        Name of the NWM data variable to download.
    output_parquet_dir : str
        Path to the directory for the final parquet files.
    process_by_z_hour : bool
        A boolean flag that determines the method of grouping files
        for processing.
    stepsize : int
        The number of json files to process at one time.
    ignore_missing_file : bool
        Flag specifying whether or not to fail if a missing NWM
        file is encountered
        True = skip and continue
        False = fail.
    units_format_dict : Dict,
        Dictionary of unit formats.
    overwrite_output : bool
        Flag specifying whether or not to overwrite output files if
        they already exist.  True = overwrite; False = fail.
    nwm_version : str
        Specified NWM version.
    """
    output_parquet_dir = Path(output_parquet_dir)
    if not output_parquet_dir.exists():
        output_parquet_dir.mkdir(parents=True)

    # Format file list into a dataframe and group by specified method
    pattern = re.compile(r'[0-9]+')
    days = []
    z_hours = []
    for path in json_paths:
        filename = Path(path).name
        if path.split(":")[0] == "s3":
            # If it's a remote json day and z-hour are in the path
            res = re.findall(pattern, path)
            days.append(res[1])
            z_hours.append(f"t{res[2]}z")
        else:
            days.append(filename.split(".")[1])
            z_hours.append(filename.split(".")[3])
    df_refs = pd.DataFrame(
        {"day": days, "z_hour": z_hours, "filepath": json_paths}
    )
    if process_by_z_hour:
        # Option #1. Groupby day and z_hour
        gps = df_refs.groupby(["day", "z_hour"])
        dfs = [df for _, df in gps]
    else:
        # Option #2. Chunk by some number of files
        if stepsize > df_refs.index.size:
            num_partitions = 1
        else:
            num_partitions = int(df_refs.index.size / stepsize)
        dfs = np.array_split(df_refs, num_partitions)

    for df in dfs:
        process_chunk_of_files(
            df,
            location_ids,
            configuration,
            variable_name,
            output_parquet_dir,
            process_by_z_hour,
            ignore_missing_file,
            units_format_dict,
            overwrite_output,
            nwm_version
        )
