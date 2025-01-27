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

from antares.craft.tools.all_optional_meta import all_optional_model
from antares.craft.tools.contents_tool import EnumIgnoreCase
from pydantic import BaseModel, ConfigDict, Field
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


class DefaultGeneralParameters(BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    model_config = ConfigDict(use_enum_values=True)

    mode: Mode = Field(default=Mode.ECONOMY, validate_default=True)
    horizon: str = ""
    # Calendar parameters
    nb_years: int = 1
    first_day: int = 1
    last_day: int = 365
    first_january: WeekDay = Field(default=WeekDay.MONDAY, validate_default=True)
    first_month: Month = Field(default=Month.JANUARY, validate_default=True)
    first_week_day: WeekDay = Field(default=WeekDay.MONDAY, validate_default=True)
    leap_year: bool = False
    # Additional parameters
    year_by_year: bool = False
    building_mode: BuildingMode = Field(
        default=BuildingMode.AUTOMATIC, validate_default=True
    )  # ? derated and custom-scenario
    selection_mode: bool = False  # ? user-playlist
    thematic_trimming: bool = False
    geographic_trimming: bool = False
    active_rules_scenario: str = "default ruleset"  # only one option available currently
    read_only: bool = False
    # Output parameters
    simulation_synthesis: bool = True  # ? output/synthesis
    mc_scenario: bool = False  # ? output/storenewset
    result_format: OutputFormat = Field(default=OutputFormat.TXT, exclude=True)


@all_optional_model
class GeneralParameters(DefaultGeneralParameters):
    pass


class GeneralParametersLocal(DefaultGeneralParameters):
    @property
    def ini_fields(self) -> dict:
        return {
            "general": {
                "mode": str(self.mode).title(),
                "horizon": self.horizon,
                "nbyears": str(self.nb_years),
                "simulation.start": str(self.first_day),
                "simulation.end": str(self.last_day),
                "january.1st": str(self.first_january).title(),
                "first-month-in-year": str(self.first_month).title(),
                "first.weekday": str(self.first_week_day).title(),
                "leapyear": str(self.leap_year).lower(),
                "year-by-year": str(self.year_by_year).lower(),
                "derated": str(self.building_mode == BuildingMode.DERATED).lower(),
                "custom-scenario": str(self.building_mode == BuildingMode.CUSTOM).lower(),
                "user-playlist": str(self.selection_mode).lower(),
                "thematic-trimming": str(self.thematic_trimming).lower(),
                "geographic-trimming": str(self.geographic_trimming).lower(),
                "readonly": str(self.read_only).lower(),
            },
            "input": {},
            "output": {
                "synthesis": str(self.simulation_synthesis).lower(),
                "storenewset": str(self.mc_scenario).lower(),
                "result-format": self.result_format.value,
            },
        }

    def yield_properties(self) -> GeneralParameters:
        return GeneralParameters.model_validate(self.model_dump(exclude_none=True))
