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

from typing import Optional

from pydantic import BaseModel
from pydantic.alias_generators import to_camel

from antares.tools.contents_tool import EnumIgnoreCase


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


class GeneralProperties(BaseModel, alias_generator=to_camel):
    mode: Optional[Mode] = None
    first_day: Optional[int] = None
    last_day: Optional[int] = None
    horizon: Optional[str] = None
    first_month: Optional[Month] = None
    first_week_day: Optional[WeekDay] = None
    first_january: Optional[WeekDay] = None
    leap_year: Optional[bool] = None
    nb_years: Optional[int] = None
    building_mode: Optional[BuildingMode] = None
    selection_mode: Optional[bool] = None
    year_by_year: Optional[bool] = None
    simulation_synthesis: Optional[bool] = None
    mc_scenario: Optional[bool] = None
    geographic_trimming: Optional[bool] = None
    thematic_trimming: Optional[bool] = None
