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


from pydantic import BaseModel
from pydantic.alias_generators import to_camel

from antares.tools.all_optional_meta import all_optional_model
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


class DefaultGeneralProperties(BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    mode: Mode = Mode.ECONOMY
    first_day: int = 0
    last_day: int = 365
    horizon: str = ""
    first_month: Month = Month.JANUARY
    first_week_day: WeekDay = WeekDay.MONDAY
    first_january: WeekDay = WeekDay.MONDAY
    leap_year: bool = False
    nb_years: int = 1
    building_mode: BuildingMode = BuildingMode.AUTOMATIC  # ? derated and custom-scenario
    selection_mode: bool = False  # ? user-playlist
    year_by_year: bool = False
    simulation_synthesis: bool = True  # ? output/synthesis
    mc_scenario: bool = False  # ? output/storenewset
    geographic_trimming: bool = False
    thematic_trimming: bool = False


@all_optional_model
class GeneralProperties(DefaultGeneralProperties):
    pass


class GeneralPropertiesLocal(DefaultGeneralProperties):
    def yield_properties(self) -> GeneralProperties:
        return GeneralProperties.model_validate(self.model_dump(exclude_none=True))
