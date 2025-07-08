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
from dataclasses import asdict
from typing import Any, Set

from pydantic import Field

from antares.craft.model.settings.general import (
    BuildingMode,
    GeneralParameters,
    GeneralParametersUpdate,
    Mode,
    Month,
    WeekDay,
)
from antares.craft.service.local_services.models.base_model import LocalBaseModel

GeneralParametersType = GeneralParameters | GeneralParametersUpdate


class GeneralSectionLocal(LocalBaseModel):
    mode: Mode = Mode.ECONOMY
    horizon: str = ""
    nb_years: int = Field(default=1, alias="nbyears")
    simulation_start: int = Field(default=1, alias="simulation.start")
    simulation_end: int = Field(default=365, alias="simulation.end")
    january_first: WeekDay = Field(default=WeekDay.MONDAY, alias="january.1st")
    first_month_in_year: Month = Field(default=Month.JANUARY, alias="first-month-in-year")
    first_week_day: WeekDay = Field(default=WeekDay.MONDAY, alias="first.weekday")
    leap_year: bool = Field(default=False, alias="leapyear")
    year_by_year: bool = Field(default=False, alias="year-by-year")
    building_mode: BuildingMode = BuildingMode.AUTOMATIC
    user_playlist: bool = Field(default=False, alias="user-playlist")
    thematic_trimming: bool = Field(default=False, alias="thematic-trimming")
    geographic_trimming: bool = Field(default=False, alias="geographic-trimming")
    generate: bool = False
    nb_timeseries_load: int = Field(default=1, alias="nbtimeseriesload")
    nb_timeseries_hydro: int = Field(default=1, alias="nbtimeserieshydro")
    nb_timeseries_wind: int = Field(default=1, alias="nbtimeserieswind")
    nb_timeseries_thermal: int = Field(default=1, alias="nbtimeseriesthermal")
    nb_timeseries_solar: int = Field(default=1, alias="nbtimeseriessolar")
    refresh_timeseries: bool = Field(default=False, alias="refreshtimeseries")
    intra_modal: bool = Field(default=False, alias="intra-modal")
    inter_modal: bool = Field(default=False, alias="inter-modal")
    refresh_interval_load: int = Field(default=100, alias="refreshintervalload")
    refresh_interval_hydro: int = Field(default=100, alias="refreshintervalhydro")
    refresh_interval_wind: int = Field(default=100, alias="refreshintervalwind")
    refresh_interval_thermal: int = Field(default=100, alias="refreshintervalthermal")
    refresh_interval_solar: int = Field(default=100, alias="refreshintervalsolar")
    read_only: bool = Field(default=False, alias="readonly")


class OutputSectionLocal(LocalBaseModel):
    synthesis: bool = True
    store_new_set: bool = Field(default=False, alias="storenewset")
    archives: Any = ""


class GeneralParametersLocal(LocalBaseModel):
    general: GeneralSectionLocal
    input: dict[str, str] = {"import": ""}
    output: OutputSectionLocal

    @staticmethod
    def from_user_model(user_class: GeneralParametersType) -> "GeneralParametersLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}

        output_dict = {}
        if user_class.store_new_set is not None:
            output_dict["store_new_set"] = user_dict.pop("store_new_set")
        if user_class.simulation_synthesis is not None:
            output_dict["synthesis"] = user_dict.pop("simulation_synthesis")

        general_dict = {"general": user_dict}
        local_dict = general_dict | {"output": output_dict}

        return GeneralParametersLocal.model_validate(local_dict)

    def to_ini_file(self, update: bool, current_content: dict[str, Any]) -> dict[str, Any]:
        content = self.model_dump(mode="json", by_alias=True, exclude_unset=update)
        if "building_mode" in content["general"]:
            general_values = content["general"]
            del general_values["building_mode"]
            building_mode = self.general.building_mode
            general_values["derated"] = building_mode == BuildingMode.DERATED
            general_values["custom-scenario"] = building_mode == BuildingMode.CUSTOM

        if update:
            for key in ["general", "output"]:
                if content[key]:
                    current_content[key].update(content[key])
        else:
            current_content.update(content)
        return current_content

    @staticmethod
    def get_excluded_fields_for_user_class() -> Set[str]:
        return {
            "generate",
            "nbtimeseriesload",
            "nbtimeserieshydro",
            "nbtimeserieswind",
            "nbtimeseriessolar",
            "refreshtimeseries",
            "intra-modal",
            "inter-modal",
            "refreshintervalload",
            "refreshintervalhydro",
            "refreshintervalwind",
            "refreshintervalthermal",
            "refreshintervalsolar",
            "readonly",
        }

    def to_user_model(self) -> GeneralParameters:
        return GeneralParameters(
            mode=self.general.mode,
            horizon=self.general.horizon,
            nb_years=self.general.nb_years,
            simulation_start=self.general.simulation_start,
            simulation_end=self.general.simulation_end,
            january_first=self.general.january_first,
            first_month_in_year=self.general.first_month_in_year,
            first_week_day=self.general.first_week_day,
            leap_year=self.general.leap_year,
            year_by_year=self.general.year_by_year,
            simulation_synthesis=self.output.synthesis,
            building_mode=self.general.building_mode,
            user_playlist=self.general.user_playlist,
            thematic_trimming=self.general.thematic_trimming,
            geographic_trimming=self.general.geographic_trimming,
            store_new_set=self.output.store_new_set,
            nb_timeseries_thermal=self.general.nb_timeseries_thermal,
        )
