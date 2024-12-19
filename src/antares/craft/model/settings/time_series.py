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

from antares.craft.tools.all_optional_meta import all_optional_model
from antares.craft.tools.model_tools import filter_out_empty_model_fields
from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


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


class _ParametersLocal(_DefaultParameters, populate_by_name=True):
    field_name: str = Field(exclude=True)


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
    load: _ParametersLocal = _ParametersLocal(field_name="load")
    hydro: _ParametersLocal = _ParametersLocal(field_name="hydro")
    thermal: _ParametersLocal = _ParametersLocal(field_name="thermal")
    wind: _ParametersLocal = _ParametersLocal(field_name="wind")
    solar: _ParametersLocal = _ParametersLocal(field_name="solar")
    renewables: Optional[_ParametersLocal] = None
    ntc: Optional[_ParametersLocal] = None

    @property
    def ini_fields(self) -> dict:
        fields_to_check = filter_out_empty_model_fields(self)
        general_dict = {}
        general_dict["generate"] = ", ".join(self._make_list_from_fields("stochastic_ts_status"))
        general_dict |= {
            "nbtimeseries" + field_to_add: str(getattr(self, field_to_add).number) for field_to_add in fields_to_check
        }
        general_dict["refreshtimeseries"] = ", ".join(self._make_list_from_fields("refresh"))
        general_dict["intra-modal"] = ", ".join(self._make_list_from_fields("intra_modal"))
        general_dict["inter-modal"] = ", ".join(self._make_list_from_fields("inter_modal"))
        general_dict |= {
            "refreshinterval" + field_to_add: str(getattr(self, field_to_add).refresh_interval)
            for field_to_add in fields_to_check
        }
        input_dict = {"import": ", ".join(self._make_list_from_fields("store_in_input"))}
        output_dict = {"archives": ", ".join(self._make_list_from_fields("store_in_output"))}
        return {"general": general_dict, "input": input_dict, "output": output_dict}

    def _make_list_from_fields(self, field_to_check: str) -> list:
        fields_to_check = filter_out_empty_model_fields(self)
        return [
            field_to_add for field_to_add in fields_to_check if getattr(getattr(self, field_to_add), field_to_check)
        ]


def correlation_defaults(season_correlation: SeasonCorrelation) -> dict[str, dict[str, str]]:
    general_section = {"general": {"mode": season_correlation.value}}
    annual_section: dict[str, dict] = {"annual": {}} if season_correlation.value == "annual" else {}
    extra_sections: dict[str, dict] = (
        {f"{num}": {} for num in range(12)} if season_correlation.value == "annual" else {}
    )
    return general_section | annual_section | extra_sections
