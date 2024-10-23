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

from enum import Enum
from typing import Optional

from pydantic import BaseModel
from pydantic.alias_generators import to_camel

from antares.tools.all_optional_meta import all_optional_model


class SeasonCorrelation(Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class _DefaultParameters(BaseModel, alias_generator=to_camel):
    stochastic_ts_status: bool = False
    number: int = 1
    refresh: bool = False
    refresh_interval: int = 100
    season_correlation: SeasonCorrelation = SeasonCorrelation.ANNUAL
    store_in_input: bool = False
    store_in_output: bool = False
    intra_modal: bool = False
    inter_modal: bool = False


@all_optional_model
class _Parameters(_DefaultParameters):
    pass


class _ParametersLocal(_DefaultParameters):
    @property
    def ini_fields(self) -> dict:
        return {}


class DefaultTimeSeriesParameters(BaseModel, alias_generator=to_camel):
    load: _DefaultParameters = _DefaultParameters()
    hydro: _DefaultParameters = _DefaultParameters()
    thermal: _DefaultParameters = _DefaultParameters()
    wind: _DefaultParameters = _DefaultParameters()
    solar: _DefaultParameters = _DefaultParameters()
    renewables: Optional[_DefaultParameters] = None
    ntc: Optional[_DefaultParameters] = None


@all_optional_model
class TimeSeriesParameters(DefaultTimeSeriesParameters):
    pass


class TimeSeriesParametersLocal(DefaultTimeSeriesParameters):
    @property
    def ini_fields(self) -> dict:
        return {}

class TimeSeriesParameters(BaseModel, alias_generator=to_camel):
    load: Optional[_Parameters] = None
    hydro: Optional[_Parameters] = None
    thermal: Optional[_Parameters] = None
    wind: Optional[_Parameters] = None
    solar: Optional[_Parameters] = None
    renewables: Optional[_Parameters] = None
    ntc: Optional[_Parameters] = None
