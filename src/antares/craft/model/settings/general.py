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

from antares.craft.tools.contents_tool import EnumIgnoreCase


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
