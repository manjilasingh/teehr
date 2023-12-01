from enum import Enum
from typing import Optional

from pydantic import BaseModel


# GRID DATA VARIABLES ENUMS
class LandAssimVariablesEnum(str, Enum):
    ACCET = "ACCET"
    ACSNOM = "ACSNOM"
    EDIR = "EDIR"
    FSNO = "FSNO"
    ISNOW = "ISNOW"
    QRAIN = "QRAIN"
    QSNOW = "QSNOW"
    SNEQV = "SNEQV"
    SNLIQ = "SNLIQ"
    SNOWH = "SNOWH"
    SNOWT_AVG = "SNOWT_AVG"
    SOILICE = "SOILICE"
    SOILSAT_TOP = "SOILSAT_TOP"
    SOIL_M = "SOIL_M"
    SOIL_T = "SOIL_T"


class LandShortVariablesEnum(str, Enum):
    ACCET = "ACCET"
    SNOWT_AVG = "SNOWT_AVG"
    SOILSAT_TOP = "SOILSAT_TOP"
    FSNO = "FSNO"
    SNOWH = "SNOWH"
    SNEQV = "SNEQV"


class LandMediumVariablesEnum(str, Enum):
    FSA = "FSA"
    FIRA = "FIRA"
    GRDFLX = "GRDFLX"
    HFX = "HFX"
    LH = "LH"
    UGDRNOFF = "UGDRNOFF"
    ACCECAN = "ACCECAN"
    ACCEDIR = "ACCEDIR"
    ACCETRAN = "ACCETRAN"
    TRAD = "TRAD"
    SNLIQ = "SNLIQ"
    SOIL_T = "SOIL_T"
    SOIL_M = "SOIL_M"
    SNOWH = "SNOWH"
    SNEQV = "SNEQV"
    ISNOW = "ISNOW"
    FSNO = "FSNO"
    ACSNOM = "ACSNOM"
    ACCET = "ACCET"
    CANWAT = "CANWAT"
    SOILICE = "SOILICE"
    SOILSAT_TOP = "SOILSAT_TOP"
    SNOWT_AVG = "SNOWT_AVG"


class LandLongVariablesEnum(str, Enum):
    UGDRNOFF = "UGDRNOFF"
    SFCRNOFF = "SFCRNOFF"
    SNEQV = "SNEQV"
    ACSNOM = "ACSNOM"
    ACCET = "ACCET"
    CANWAT = "CANWAT"
    SOILSAT_TOP = "SOILSAT_TOP"
    SOILSAT = "SOILSAT"


class ForcingVariablesEnum(str, Enum):
    U2D = "U2D"
    V2D = "V2D"
    T2D = "T2D"
    Q2D = "Q2D"
    LWDOWN = "LWDOWN"
    SWDOWN = "SWDOWN"
    RAINRATE = "RAINRATE"
    PSFC = "PSFC"


# OUTPUT TYPE ENUMS
class ShortAndAnalysisOutputEnum(str, Enum):
    land = "land"


class MediumOutputEnum(str, Enum):
    land_1 = "land_1"
    land_2 = "land_2"
    land_3 = "land_3"
    land_4 = "land_4"
    land_5 = "land_5"
    land_6 = "land_6"
    land_7 = "land_7"


class LongOutputEnum(str, Enum):
    land_1 = "land_1"
    land_2 = "land_2"
    land_3 = "land_3"
    land_4 = "land_4"


class ForcingOutputEnum(str, Enum):
    forcing = "forcing"


# OUTPUT TYPE MODELS
class Analysis(BaseModel):
    output_type: ShortAndAnalysisOutputEnum
    land: Optional[LandAssimVariablesEnum] = None


class ShortRange(BaseModel):
    output_type: ShortAndAnalysisOutputEnum
    land: Optional[LandShortVariablesEnum] = None


class MediumRange(BaseModel):
    output_type: MediumOutputEnum
    land_1: Optional[LandMediumVariablesEnum] = None
    land_2: Optional[LandMediumVariablesEnum] = None
    land_3: Optional[LandMediumVariablesEnum] = None
    land_4: Optional[LandMediumVariablesEnum] = None
    land_5: Optional[LandMediumVariablesEnum] = None
    land_6: Optional[LandMediumVariablesEnum] = None
    land_7: Optional[LandMediumVariablesEnum] = None


class LongRange(BaseModel):
    output_type: LongOutputEnum
    land_1: Optional[LandLongVariablesEnum] = None
    land_2: Optional[LandLongVariablesEnum] = None
    land_3: Optional[LandLongVariablesEnum] = None
    land_4: Optional[LandLongVariablesEnum] = None


class Forcing(BaseModel):
    output_type: ForcingOutputEnum
    forcing: Optional[ForcingVariablesEnum] = None


# CONFIGURATIONS ENUM
class ConfigurationsEnum(str, Enum):
    analysis_assim = "analysis_assim"
    analysis_assim_no_da = "analysis_assim_no_da"
    analysis_assim_extend = "analysis_assim_extend"
    analysis_assim_extend_no_da = "analysis_assim_extend_no_da"
    analysis_assim_long = "analysis_assim_long"
    analysis_assim_long_no_da = "analysis_assim_long_no_da"
    analysis_assim_hawaii = "analysis_assim_hawaii"
    analysis_assim_hawaii_no_da = "analysis_assim_hawaii_no_da"
    analysis_assim_puertorico = "analysis_assim_puertorico"
    analysis_assim_puertorico_no_da = "analysis_assim_puertorico_no_da"
    short_range = "short_range"
    short_range_hawaii = "short_range_hawaii"
    short_range_puertorico = "short_range_puertorico"
    short_range_hawaii_no_da = "short_range_hawaii_no_da"
    short_range_puertorico_no_da = "short_range_puertorico_no_da"
    medium_range_mem1 = "medium_range_mem1"
    medium_range_mem2 = "medium_range_mem2"
    medium_range_mem3 = "medium_range_mem3"
    medium_range_mem4 = "medium_range_mem4"
    medium_range_mem5 = "medium_range_mem5"
    medium_range_mem6 = "medium_range_mem6"
    medium_range_mem7 = "medium_range_mem7"
    long_range_mem1 = "long_range_mem1"
    long_range_mem2 = "long_range_mem2"
    long_range_mem3 = "long_range_mem3"
    long_range_mem4 = "long_range_mem4"
    forcing_medium_range = "forcing_medium_range"
    forcing_short_range = "forcing_short_range"
    forcing_short_range_hawaii = "forcing_short_range_hawaii"
    forcing_short_range_puertorico = "forcing_short_range_puertorico"
    forcing_analysis_assim = "forcing_analysis_assim"
    forcing_analysis_assim_extend = "forcing_analysis_assim_extend"
    forcing_analysis_assim_hawaii = "forcing_analysis_assim_hawaii"
    forcing_analysis_assim_puertorico = "forcing_analysis_assim_puertorico"


# CONFIGURATION MODEL
class GridConfigurationModel(BaseModel):
    configuration: ConfigurationsEnum
    analysis_assim: Optional[Analysis] = None
    analysis_assim_no_da: Optional[Analysis] = None
    analysis_assim_extend: Optional[Analysis] = None
    analysis_assim_extend_no_da: Optional[Analysis] = None
    analysis_assim_long: Optional[Analysis] = None
    analysis_assim_long_no_da: Optional[Analysis] = None
    analysis_assim_hawaii: Optional[Analysis] = None
    analysis_assim_hawaii_no_da: Optional[Analysis] = None
    analysis_assim_puertorico: Optional[Analysis] = None
    analysis_assim_puertorico_no_da: Optional[Analysis] = None
    short_range: Optional[ShortRange] = None
    short_range_hawaii: Optional[ShortRange] = None
    short_range_puertorico: Optional[ShortRange] = None
    short_range_hawaii_no_da: Optional[ShortRange] = None
    short_range_puertorico_no_da: Optional[ShortRange] = None
    medium_range_mem1: Optional[MediumRange] = None
    medium_range_mem2: Optional[MediumRange] = None
    medium_range_mem3: Optional[MediumRange] = None
    medium_range_mem4: Optional[MediumRange] = None
    medium_range_mem5: Optional[MediumRange] = None
    medium_range_mem6: Optional[MediumRange] = None
    medium_range_mem7: Optional[MediumRange] = None
    medium_range_no_da: Optional[MediumRange] = None
    long_range_mem1: Optional[LongRange] = None
    long_range_mem2: Optional[LongRange] = None
    long_range_mem3: Optional[LongRange] = None
    long_range_mem4: Optional[LongRange] = None
    forcing_medium_range: Optional[Forcing] = None
    forcing_short_range: Optional[Forcing] = None
    forcing_short_range_hawaii: Optional[Forcing] = None
    forcing_short_range_puertorico: Optional[Forcing] = None
    forcing_analysis_assim: Optional[Forcing] = None
    forcing_analysis_assim_extend: Optional[Forcing] = None
    forcing_analysis_assim_hawaii: Optional[Forcing] = None
    forcing_analysis_assim_puertorico: Optional[Forcing] = None


if __name__ == "__main__":
    # So for example:
    configuration = "forcing_medium_range"
    output_type = "forcing"
    variable_name = "RAINRATE"

    # Assemble input parameters
    vars = {
        "configuration": configuration,
        configuration: {
            "output_type": output_type,
            output_type: variable_name,
        },
    }

    # import sys
    # Check input parameters
    # try:
    cm = GridConfigurationModel.model_validate(vars)
    # except ValidationError as e:
    #     print(e.errors()[0]["msg"])
    #     sys.exit()

    config = cm.configuration.name
    forecast_obj = getattr(cm, config)
    out_type = forecast_obj.output_type.name
    var_name = getattr(forecast_obj, out_type).name

    pass