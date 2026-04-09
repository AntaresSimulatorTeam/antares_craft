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
    """Modes to run the simulation.

    Attributes:
        ECONOMY: Antares simulator will try to ensure balance between load and generation,
            while minimizing the economical cost of the grid's operation (more on this here).
            Economy simulations make a full use of Antares optimization capabilities.
            They require economic as well as technical input data and may demand a lot of computer resources.
        ADEQUACY: All power plant operational costs are considered zero.
            Antares only objective is to ensure balance between load and generation.
            Adequacy simulations are faster and require only technical input data.
            Their results are limited to adequacy indicators.
        EXPANSION: Antares simulator will optimize the investments on the grid, minimizing both investments and operational costs.
    """

    ECONOMY = "Economy"
    ADEQUACY = "Adequacy"
    EXPANSION = "Expansion"


class Month(EnumIgnoreCase):
    """Months of the year."""

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
    """Week days."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class BuildingMode(EnumIgnoreCase):
    """Building modes.

    Attributes:
        AUTOMATIC: Time-series are randomly drawn.
        CUSTOM: The simulation will be carried out on a mix of deterministic and probabilistic conditions,
            with some time-series randomly drawn and others set to user-defined values.
            This option allows setting up detailed "what if" simulations that may help to understand the phenomena at work and quantify various kinds of risk indicators.
            To set up the simulation profile, use the scenario builder.
        DERATED: All time-series will be replaced by their general average and the number of MC years set to 1.
            If the TS are ready-made or Antares-generated but are not to be stored in the INPUT folder,
            no time-series will be written over the original ones (if any).
            If the time-series are built by Antares and if it is specified that they should be stored in the INPUT,
            a single average-out time series will be stored instead of the whole set.
    """

    AUTOMATIC = "automatic"
    CUSTOM = "custom"
    DERATED = "derated"


class OutputChoices(Enum):
    """Output choices.

    Attributes:
        LOAD:
        WIND:
        HYDRO:
        THERMAL:
        SOLAR:
        RENEWABLES:
        NTC:
        MAX_POWER:
    """

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
    """General parameters for the simulation.

    Attributes:
        mode: Choice of the simulation mode (economy, adequacy or expansion).
        horizon: Horizon of the study (static tag, not used in the calculations).
        nb_years: Number of Monte-Carlo scenarios/years.
        simulation_start: First day of the simulation in 1, 2, ..., 366.
        simulation_end: Last day of the simulation in 1, 2, ..., 366.
        january_first: Choice of the weekday of the year.
        first_month_in_year: Choice of the first month in the year depending on the type of study.
        first_week_day: Choice of the first day of the week.
        leap_year: Whether to decide that the year is a leap year.
        year_by_year: Whether to enable year-by-year the output profile.
        simulation_synthesis: Whether there is a simulation synthesis in the output profile.
        building_mode: Choice of the building mode (`AUTOMATIC`, `CUSTOM` or `DERATED`).
        user_playlist:
        thematic_trimming: Whether to enable thematic trimming.
        geographic_trimming: Whether to enable geographic trimming.
        store_new_set:
        nb_timeseries_thermal: Number of time-series to be generated stochastically.
    """

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
    """Update general parameters.

    See field details in [`GeneralParameters`][antares.craft.model.settings.general.GeneralParameters].
    """

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
