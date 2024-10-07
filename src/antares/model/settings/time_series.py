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


class SeasonCorrelation(Enum):
    MONTHLY = "monthly"
    ANNUAL = "annual"


class _Parameters(BaseModel, alias_generator=to_camel):
    stochastic_ts_status: Optional[bool] = None
    number: Optional[int] = None
    refresh: Optional[bool] = None
    refresh_interval: Optional[int] = None
    season_correlation: Optional[SeasonCorrelation] = None
    store_in_input: Optional[bool] = None
    store_in_output: Optional[bool] = None
    intra_modal: Optional[bool] = None
    inter_modal: Optional[bool] = None


class TimeSeriesParameters(BaseModel, alias_generator=to_camel):
    load: Optional[_Parameters] = None
    hydro: Optional[_Parameters] = None
    thermal: Optional[_Parameters] = None
    wind: Optional[_Parameters] = None
    solar: Optional[_Parameters] = None
    renewables: Optional[_Parameters] = None
    ntc: Optional[_Parameters] = None
