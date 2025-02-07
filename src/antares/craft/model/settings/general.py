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
    store_new_set: Optional[bool] = None
    nb_timeseries_thermal: Optional[int] = None
