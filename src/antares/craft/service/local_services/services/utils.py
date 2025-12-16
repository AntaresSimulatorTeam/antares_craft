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
from pathlib import Path
from typing import Any, Callable

import pandas as pd

from typing_extensions import override

from antares.craft.exceptions.exceptions import MatrixFormatError
from antares.craft.model.st_storage import STStorageMatrixName
from antares.craft.model.thermal import ThermalClusterMatrixName
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter


class AlwaysEqual:
    @override
    def __eq__(self, other: Any) -> bool:
        return True

    @override
    def __str__(self) -> str:
        return "Any"

    @override
    def __format__(self, format_spec: str) -> str:
        return self.__str__()


EXPECTED_SHAPE_MAPPING = {
    ThermalClusterMatrixName.PREPRO_DATA.value: (365, 6),
    ThermalClusterMatrixName.PREPRO_MODULATION.value: (8760, 4),
    ThermalClusterMatrixName.SERIES.value: (8760, AlwaysEqual()),
    ThermalClusterMatrixName.SERIES_CO2_COST.value: (8760, AlwaysEqual()),
    ThermalClusterMatrixName.SERIES_FUEL_COST.value: (8760, AlwaysEqual()),
    STStorageMatrixName.PMAX_INJECTION.value: (8760, 1),
    STStorageMatrixName.PMAX_WITHDRAWAL.value: (8760, 1),
    STStorageMatrixName.LOWER_CURVE_RULE.value: (8760, 1),
    STStorageMatrixName.UPPER_RULE_CURVE.value: (8760, 1),
    STStorageMatrixName.INFLOWS.value: (8760, 1),
    STStorageMatrixName.COST_INJECTION.value: (8760, 1),
    STStorageMatrixName.COST_WITHDRAWAL.value: (8760, 1),
    STStorageMatrixName.COST_LEVEL.value: (8760, 1),
    STStorageMatrixName.COST_VARIATION_INJECTION.value: (8760, 1),
    STStorageMatrixName.COST_VARIATION_WITHDRAWAL.value: (8760, 1),
    "series": (8760, AlwaysEqual()),
    "links_parameters": (8760, 6),
    "bc_hourly": (8784, AlwaysEqual()),
    "bc_daily": (366, AlwaysEqual()),
    "bc_weekly": (366, AlwaysEqual()),
}


def checks_matrix_dimensions(matrix: pd.DataFrame, matrix_path: str, ts_name: str) -> None:
    if not matrix.empty:
        expected_shape = EXPECTED_SHAPE_MAPPING[ts_name]
        matrix_shape = matrix.shape
        if matrix_shape != expected_shape:
            matrix_name = f"{matrix_path}/{ts_name}"
            raise MatrixFormatError(matrix_name, expected_shape, matrix_shape)


def _read_scenario_builder(study_path: Path) -> dict[str, Any]:
    scenario_builder_path = study_path / "settings" / "scenariobuilder.dat"
    return IniReader().read(scenario_builder_path)


def remove_object_from_scenario_builder(study_path: Path, pattern: Callable[[str, list[str]], bool]) -> None:
    rulesets = _read_scenario_builder(study_path)
    for ruleset in rulesets.values():
        for key in list(ruleset):
            symbol, *parts = key.split(",")
            if pattern(symbol, parts):
                del ruleset[key]

    IniWriter().write(rulesets, study_path / "settings" / "scenariobuilder.dat")
