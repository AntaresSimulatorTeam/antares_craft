# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

from enum import Enum


class TimeSeriesFileType(Enum):
    """
    DTO for storing the paths to Antares time series files.

    This DTO contains the relative paths to different timeseries files used in the generation of an Antares study,
    starting from the base folder of the study.

    Files where the path contains {area_id} or {constraint_id} have to be used with `.format` to access the correct path.

    Example:
        TimeSeriesFileType.SOLAR.value.format(area_id="test_area")
    """

    BINDING_CONSTRAINT_EQUAL = "input/bindingconstraints/{constraint_id}_eq.txt"
    BINDING_CONSTRAINT_GREATER = "input/bindingconstraints/{constraint_id}_gt.txt"
    BINDING_CONSTRAINT_LESS = "input/bindingconstraints/{constraint_id}_lt.txt"
    HYDRO_MAX_POWER = "input/hydro/common/capacity/maxpower_{area_id}.txt"
    HYDRO_RESERVOIR = "input/hydro/common/capacity/reservoir_{area_id}.txt"
    HYDRO_INFLOW_PATTERN = "input/hydro/common/capacity/inflowPattern_{area_id}.txt"
    HYDRO_CREDITS_MODULATION = "input/hydro/common/capacity/creditmodulations_{area_id}.txt"
    HYDRO_WATER_VALUES = "input/hydro/common/capacity/waterValues_{area_id}.txt"
    HYDRO_ROR = "input/hydro/series/{area_id}/ror.txt"
    HYDRO_MOD = "input/hydro/series/{area_id}/mod.txt"
    HYDRO_MINGEN = "input/hydro/series/{area_id}/mingen.txt"
    HYDRO_ENERGY = "input/hydro/prepro/{area_id}/energy.txt"
    LINKS_CAPACITIES_DIRECT = "input/links/{area_id}/capacities/{second_area_id}_direct.txt"
    LINKS_CAPACITIES_INDIRECT = "input/links/{area_id}/capacities/{second_area_id}_indirect.txt"
    LINKS_PARAMETERS = "input/links/{area_id}/{second_area_id}_parameters.txt"
    LOAD = "input/load/series/load_{area_id}.txt"
    LOAD_CONVERSION = "input/load/prepro/{area_id}/conversion.txt"
    LOAD_DATA = "input/load/prepro/{area_id}/data.txt"
    LOAD_K = "input/load/prepro/{area_id}/k.txt"
    LOAD_TRANSLATION = "input/load/prepro/{area_id}/translation.txt"
    MISC_GEN = "input/misc-gen/miscgen-{area_id}.txt"
    RENEWABLE_SERIES = "input/renewables/series/{area_id}/{cluster_id}/series.txt"
    ST_STORAGE_PMAX_INJECTION = "input/st-storage/series/{area_id}/{cluster_id}/PMAX-injection.txt"
    ST_STORAGE_PMAX_WITHDRAWAL = "input/st-storage/series/{area_id}/{cluster_id}/PMAX-withdrawal.txt"
    ST_STORAGE_INFLOWS = "input/st-storage/series/{area_id}/{cluster_id}/inflows.txt"
    ST_STORAGE_LOWER_RULE_CURVE = "input/st-storage/series/{area_id}/{cluster_id}/lower-rule-curve.txt"
    ST_STORAGE_UPPER_RULE_CURVE = "input/st-storage/series/{area_id}/{cluster_id}/upper-rule-curve.txt"
    ST_STORAGE_COST_INJECTION = "input/st-storage/series/{area_id}/{cluster_id}/cost-injection.txt"
    ST_STORAGE_COST_WITHDRAWAL = "input/st-storage/series/{area_id}/{cluster_id}/cost-withdrawal.txt"
    ST_STORAGE_COST_LEVEL = "input/st-storage/series/{area_id}/{cluster_id}/cost-level.txt"
    ST_STORAGE_COST_VARIATION_INJECTION = "input/st-storage/series/{area_id}/{cluster_id}/cost-variation-injection.txt"
    ST_STORAGE_COST_VARIATION_WITHDRAWAL = (
        "input/st-storage/series/{area_id}/{cluster_id}/cost-variation-withdrawal.txt"
    )
    RESERVES = "input/reserves/{area_id}.txt"
    SOLAR = "input/solar/series/solar_{area_id}.txt"
    SOLAR_CONVERSION = "input/solar/prepro/{area_id}/conversion.txt"
    SOLAR_DATA = "input/solar/prepro/{area_id}/data.txt"
    SOLAR_K = "input/solar/prepro/{area_id}/k.txt"
    SOLAR_TRANSLATION = "input/solar/prepro/{area_id}/translation.txt"
    THERMAL_SERIES = "input/thermal/series/{area_id}/{cluster_id}/series.txt"
    THERMAL_DATA = "input/thermal/prepro/{area_id}/{cluster_id}/data.txt"
    THERMAL_MODULATION = "input/thermal/prepro/{area_id}/{cluster_id}/modulation.txt"
    THERMAL_CO2 = "input/thermal/series/{area_id}/{cluster_id}/CO2Cost.txt"
    THERMAL_FUEL = "input/thermal/series/{area_id}/{cluster_id}/fuelCost.txt"
    WIND = "input/wind/series/wind_{area_id}.txt"
    WIND_CONVERSION = "input/wind/prepro/{area_id}/conversion.txt"
    WIND_DATA = "input/wind/prepro/{area_id}/data.txt"
    WIND_K = "input/wind/prepro/{area_id}/k.txt"
    WIND_TRANSLATION = "input/wind/prepro/{area_id}/translation.txt"
