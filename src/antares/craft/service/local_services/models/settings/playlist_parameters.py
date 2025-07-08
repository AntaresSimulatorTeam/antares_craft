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
from typing import Any

from pydantic import Field

from antares.craft import PlaylistParameters
from antares.craft.service.local_services.models.base_model import LocalBaseModel


class PlaylistParametersLocal(LocalBaseModel):
    playlist_reset: bool
    playlist_plus: list[int] | None = Field(None, alias="playlist_year +")
    playlist_minus: list[int] | None = Field(None, alias="playlist_year -")
    playlist_year_weight: list[str] | None = None

    def to_user_model(self, nb_years: int) -> dict[int, PlaylistParameters]:
        playlist_dict: dict[int, PlaylistParameters] = {}

        # Builds the `weight` dict
        weight_dict: dict[int, float] = {}
        if self.playlist_year_weight:
            for weight_str in self.playlist_year_weight:
                year, weight = weight_str.split(",")
                weight_dict[int(year)] = float(weight)

        # Builds the `status` dict
        if self.playlist_reset:
            status_dict = dict.fromkeys(range(nb_years), True)
            if self.playlist_minus:
                for disabled_year in self.playlist_minus:
                    status_dict[disabled_year] = False
        else:
            status_dict = dict.fromkeys(range(nb_years), False)
            if self.playlist_plus:
                for enabled_year in self.playlist_plus:
                    status_dict[enabled_year] = True

        # Builds the user object
        for playlist_year in range(nb_years):
            playlist_weight = weight_dict.get(playlist_year, 1)
            # Change starting year from 0 to 1
            playlist_dict[playlist_year + 1] = PlaylistParameters(
                status=status_dict[playlist_year], weight=playlist_weight
            )

        return playlist_dict

    @staticmethod
    def create(user_class: dict[int, PlaylistParameters], nb_years: int) -> "PlaylistParametersLocal":
        playlist_year_weight = []
        playlist_plus = []
        playlist_minus = []
        # Fill the parameters
        for year, parameters in user_class.items():
            # Change starting year from 1 to 0
            local_year = year - 1
            if parameters.status:
                playlist_plus.append(local_year)
            else:
                playlist_minus.append(local_year)
            if parameters.weight != 1:
                playlist_year_weight.append(f"{local_year},{parameters.weight}")

        # Calculates what's the lighter to write
        args: dict[str, Any] = {"playlist_year_weight": playlist_year_weight}
        nb_years_activated = len(playlist_plus)
        nb_years_deactivated = len(playlist_minus)
        if nb_years_activated > nb_years_deactivated:
            playlist_reset = True
            args["playlist_plus"] = None
            if nb_years_deactivated == nb_years:
                playlist_minus = []
            args["playlist_minus"] = playlist_minus
        else:
            playlist_reset = False
            args["playlist_minus"] = None
            if nb_years_activated == nb_years:
                playlist_plus = []
            args["playlist_plus"] = playlist_plus

        args["playlist_reset"] = playlist_reset
        return PlaylistParametersLocal.model_validate(args)
