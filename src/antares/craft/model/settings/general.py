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
from enum import Enum
from typing import Optional

from antares.craft.tools.contents_tool import EnumIgnoreCase


class Mode(EnumIgnoreCase):
    ECONOMY = "Economy"
    ADEQUACY = "Adequacy"


class Month(EnumIgnoreCase):
    JANUARY = "January"
    FEBRUARY = "February"
    MARCH = "March"
    APRIL = "April"
    MAY = "May"
    JUNE = "June"
    JULY = "July"
    AUGUST = "August"
    SEPTEMBER = "September"
    OCTOBER = "October"
    NOVEMBER = "November"
    DECEMBER = "December"


class WeekDay(EnumIgnoreCase):
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class BuildingMode(EnumIgnoreCase):
    AUTOMATIC = "automatic"
    CUSTOM = "custom"
    DERATED = "derated"


class OutputChoices(Enum):
    LOAD = "load"
    WIND = "wind"
    HYDRO = "hydro"
    THERMAL = "thermal"
    SOLAR = "solar"
    RENEWABLES = "renewables"
    NTC = "ntc"
    MAX_POWER = "max-power"


@dataclass(frozen=True)
class GeneralParameters:
    mode: Mode = Mode.ECONOMY
    horizon: str = ""
    nb_years: int = 1
    simulation_start: int = 1
    simulation_end: int = 365
    january_first: WeekDay = WeekDay.MONDAY
    first_month_in_year: Month = Month.JANUARY
    first_week_day: WeekDay = WeekDay.MONDAY
    leap_year: bool = False
    year_by_year: bool = False
    simulation_synthesis: bool = True
    building_mode: BuildingMode = BuildingMode.AUTOMATIC
    user_playlist: bool = False
    thematic_trimming: bool = False
    geographic_trimming: bool = False
    store_new_set: bool = False
    nb_timeseries_thermal: int = 1


@dataclass
class GeneralParametersUpdate:
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
    store_new_set: Optional[bool] = None
    nb_timeseries_thermal: Optional[int] = None
