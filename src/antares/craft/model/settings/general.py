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
from dataclasses import dataclass
from typing import Optional

from antares.craft.tools.all_optional_meta import all_optional_model
from antares.craft.tools.contents_tool import EnumIgnoreCase
from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


class Mode(EnumIgnoreCase):
    ECONOMY = "economy"
    ADEQUACY = "adequacy"
    DRAFT = "draft"


class Month(EnumIgnoreCase):
    JANUARY = "january"
    FEBRUARY = "february"
    MARCH = "march"
    APRIL = "april"
    MAY = "may"
    JUNE = "june"
    JULY = "july"
    AUGUST = "august"
    SEPTEMBER = "september"
    OCTOBER = "october"
    NOVEMBER = "november"
    DECEMBER = "december"


class WeekDay(EnumIgnoreCase):
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class BuildingMode(EnumIgnoreCase):
    AUTOMATIC = "automatic"
    CUSTOM = "custom"
    DERATED = "derated"


class OutputChoices(EnumIgnoreCase):
    LOAD = "load"
    WIND = "wind"
    HYDRO = "hydro"
    THERMAL = "thermal"
    SOLAR = "solar"
    RENEWABLES = "renewables"
    NTC = "ntc"
    MAX_POWER = "max-power"


class OutputFormat(EnumIgnoreCase):
    TXT = "txt-files"
    ZIP = "zip-files"


@dataclass
class GeneralParameters:
    mode: Optional[Mode] = None
    horizon: Optional[str] = None
    nb_years: Optional[int] = None
    simulation_start: Optional[int] = None
    simulation_end: Optional[int] = None
    january_first: Optional[WeekDay] = None
    first_month_in_year: Optional[Month] = None
    first_week_day: Optional[WeekDay] = None
    leap_year: Optional[bool] = None
    year_by_year: Optional[bool] = None
    simulation_synthesis: Optional[bool] = None
    building_mode: Optional[BuildingMode] = None
    user_playlist: Optional[bool] = None
    thematic_trimming: Optional[bool] = None
    geographic_trimming: Optional[bool] = None
    nb_timeseries_thermal: Optional[int] = None


@all_optional_model
class GeneralParametersAPI(BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    mode: Mode = Field(default=Mode.ECONOMY, validate_default=True)
    horizon: str
    nb_years: int
    first_day: int
    last_day: int
    first_january: WeekDay
    first_month: Month
    first_week_day: WeekDay
    leap_year: bool
    year_by_year: bool
    building_mode: BuildingMode
    selection_mode: bool
    thematic_trimming: bool
    geographic_trimming: bool
    active_rules_scenario: str
    read_only: bool
    simulation_synthesis: bool
    mc_scenario: bool
    result_format: OutputFormat


class GeneralSectionLocal(BaseModel):
    mode: Mode = Field(default=Mode.ECONOMY, validate_default=True)
    horizon: str = ""
    nb_years: int = Field(default=1, alias="nb.years")
    simulation_start: int = Field(default=1, alias="simulation.start")
    simulation_end: int = Field(default=365, alias="simulation.end")
    first_january: WeekDay = Field(default=WeekDay.MONDAY, alias="january.1st")
    first_month: Month = Field(default=Month.JANUARY, alias="first-month-in-year")
    first_week_day: WeekDay = Field(default=WeekDay.MONDAY, alias="first.weekday")
    leap_year: bool = Field(default=False, alias="leapyear")
    year_by_year: bool = Field(default=False, alias="year-by-year")
    derated: bool = False
    custom_scenario: bool = Field(default=False, alias="custom-scenario")
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
    intra_model: bool = Field(default=False, alias="intra-model")
    inter_model: bool = Field(default=False, alias="inter-model")
    refresh_interval_load: int = Field(default=100, alias="refreshintervalload")
    refresh_interval_hydro: int = Field(default=100, alias="refreshintervalhydro")
    refresh_interval_wind: int = Field(default=100, alias="refreshintervalwind")
    refresh_interval_thermal: int = Field(default=100, alias="refreshintervalthermal")
    refresh_interval_solar: int = Field(default=100, alias="refreshintervalsolar")
    read_only: bool = Field(default=False, alias="readonly")


class OutputSectionLocal(BaseModel):
    synthesis: bool = True
    store_new_set: bool = Field(default=True, alias="storenewset")
    archives: set[OutputChoices] = set()


class GeneralParametersLocalCreation(BaseModel):
    general: GeneralSectionLocal
    input: dict = {"input": ""}
    output: OutputSectionLocal


@all_optional_model
class GeneralParametersLocalEdition(GeneralParametersLocalCreation):
    pass
