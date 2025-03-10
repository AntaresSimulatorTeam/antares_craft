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
import copy
import logging
import shutil
import tempfile

from pathlib import Path, PurePath
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import ConstraintDoesNotExistError
from antares.craft.model.area import Area
from antares.craft.model.binding_constraint import (
    BindingConstraint,
)
from antares.craft.model.output import Output
from antares.craft.model.thermal import LocalTSGenerationBehavior
from antares.craft.service.base_services import BaseOutputService, BaseStudyService
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.tsgen.duration_generator import ProbabilityLaw
from antares.tsgen.random_generator import MersenneTwisterRNG
from antares.tsgen.ts_generator import OutageGenerationParameters, ThermalCluster, TimeseriesGenerator
from typing_extensions import override

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from antares.craft.model.study import Study


def _replace_safely_original_files(study_path: Path, tmp_path: Path) -> None:
    original_path = study_path / "input" / "thermal" / "series"
    shutil.rmtree(original_path)
    tmp_path.rename(original_path)


def _build_timeseries(number_of_years: int, areas_dict: dict[str, Area], seed: int, tmp_path: Path) -> None:
    # 1- Get the seed and nb_years to generate
    # 2 - Build the generator
    rng = MersenneTwisterRNG(seed=seed)
    generator = TimeseriesGenerator(rng=rng, days=365)
    # 3- Do a first loop to know how many operations will be performed
    total_generations = sum(len(area.get_thermals()) for area in areas_dict.values())
    # 4- Loop through areas in alphabetical order
    generation_performed = 0
    areas = list(areas_dict.values())
    areas.sort(key=lambda area: area.id)
    for area in areas:
        area_id = area.id
        # 5- Loop through thermal clusters in alphabetical order
        thermals = list(area.get_thermals().values())
        thermals.sort(key=lambda thermal: thermal.id)
        for thermal in thermals:
            try:
                # 6 - Filters out clusters with no generation
                if thermal.properties.gen_ts == LocalTSGenerationBehavior.FORCE_NO_GENERATION:
                    generation_performed += 1
                    continue
                # 7- Build the cluster
                modulation_matrix = thermal.get_prepro_modulation_matrix()
                modulation_capacity = modulation_matrix[2].to_numpy()
                data_matrix = thermal.get_prepro_data_matrix()
                fo_duration = np.array(data_matrix[0], dtype=int)
                po_duration = np.array(data_matrix[1], dtype=int)
                fo_rate = np.array(data_matrix[2], dtype=float)
                po_rate = np.array(data_matrix[3], dtype=float)
                npo_min = np.array(data_matrix[4], dtype=int)
                npo_max = np.array(data_matrix[5], dtype=int)
                generation_params = OutageGenerationParameters(
                    unit_count=thermal.properties.unit_count,
                    fo_law=ProbabilityLaw(thermal.properties.law_forced.value.upper()),
                    fo_volatility=thermal.properties.volatility_forced,
                    po_law=ProbabilityLaw(thermal.properties.law_planned.value.upper()),
                    po_volatility=thermal.properties.volatility_planned,
                    fo_duration=fo_duration,
                    fo_rate=fo_rate,
                    po_duration=po_duration,
                    po_rate=po_rate,
                    npo_min=npo_min,
                    npo_max=npo_max,
                )
                cluster = ThermalCluster(
                    outage_gen_params=generation_params,
                    nominal_power=thermal.properties.nominal_capacity,
                    modulation=modulation_capacity,
                )
                # 8- Generate the time-series
                results = generator.generate_time_series_for_clusters(cluster, number_of_years)
                generated_matrix = results.available_power
                # 9- Write the matrix inside the input folder.
                df = pd.DataFrame(data=generated_matrix)
                df = df[list(df.columns)].astype(int)
                target_path = tmp_path / area_id / thermal.id / "series.txt"
                df.to_csv(target_path, sep="\t", header=False, index=False, float_format="%.6f")
                # 10- Notify the progress
                generation_performed += 1
                logger.info(
                    f"Thermal cluster ts-generation advancement {round(generation_performed * 100 / total_generations, 1)} %"
                )
            except Exception as e:
                e.args = tuple([f"Area {area_id}, cluster {thermal.id}: {e.args[0]}"])
                raise


class StudyLocalService(BaseStudyService):
    def __init__(self, config: LocalConfiguration, study_name: str, output_service: BaseOutputService) -> None:
        self._config = config
        self._study_name = study_name
        self._output_service: BaseOutputService = output_service
        self._output_path = self.config.study_path / "output"

    @property
    @override
    def study_id(self) -> str:
        return self._study_name

    @property
    @override
    def config(self) -> LocalConfiguration:
        return self._config

    @property
    def output_service(self) -> BaseOutputService:
        return self._output_service

    @override
    def delete_binding_constraint(self, constraint: BindingConstraint) -> None:
        study_path = self.config.study_path
        ini_file = IniFile(study_path, InitializationFilesTypes.BINDING_CONSTRAINTS_INI)
        current_content = ini_file.ini_dict
        copied_content = copy.deepcopy(current_content)
        for index, bc in current_content.items():
            if bc["id"] == constraint.id:
                copied_content.pop(index)
                new_dict = {str(i): v for i, (k, v) in enumerate(copied_content.items())}
                ini_file.ini_dict = new_dict
                ini_file.write_ini_file()
                return
        raise ConstraintDoesNotExistError(constraint.name, self._study_name)

    @override
    def delete(self, children: bool) -> None:
        shutil.rmtree(self.config.study_path, ignore_errors=True)

    @override
    def create_variant(self, variant_name: str) -> "Study":
        raise ValueError("The variant creation should only be used for API studies not for local ones")

    @override
    def read_outputs(self) -> list[Output]:
        outputs = []
        for folder in self._output_path.iterdir():
            output_name = folder.name
            archived = True if output_name.endswith(".zip") else False
            output = Output(name=output_name, archived=archived, output_service=self.output_service)
            outputs.append(output)
        outputs.sort(key=lambda o: o.name)
        return outputs

    @override
    def delete_outputs(self) -> None:
        for resource in self._output_path.iterdir():
            if resource.is_file():
                resource.unlink()
            else:
                shutil.rmtree(resource, ignore_errors=True)

    @override
    def delete_output(self, output_name: str) -> None:
        output_path = self._output_path / output_name
        if output_path.is_file():
            output_path.unlink()
        else:
            shutil.rmtree(output_path, ignore_errors=True)

    @override
    def move_study(self, new_parent_path: Path) -> PurePath:
        raise NotImplementedError

    @override
    def generate_thermal_timeseries(self, number_of_years: int, areas: dict[str, Area], seed: int) -> None:
        study_path = self.config.study_path
        with tempfile.TemporaryDirectory(suffix=".thermal_ts_gen.tmp", prefix="~", dir=study_path.parent) as path:
            tmp_dir = Path(path)
        try:
            shutil.copytree(study_path / "input" / "thermal" / "series", tmp_dir, dirs_exist_ok=True)
            _build_timeseries(number_of_years, areas, seed, tmp_dir)
        except Exception as e:
            logger.error(f"Unhandled exception when trying to generate thermal timeseries: {e}", exc_info=True)
            raise
        else:
            _replace_safely_original_files(study_path, tmp_dir)
