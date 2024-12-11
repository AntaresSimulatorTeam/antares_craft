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

from pydantic import BaseModel, Field, ValidationError, field_validator, model_serializer, model_validator


class PlaylistData(BaseModel):
    status: bool = True
    weight: float = 1.0


class PlaylistParameters(BaseModel):
    """
    Parameters for playlists.

    Attributes:
        playlist (list[PlaylistData]): A list of years (in **PlaylistData** format) in the playlist
    """

    class Config:
        validate_assignment = True

    playlist: list[PlaylistData] = Field(default=[], exclude=True)

    _playlist_dict_error_msg = "Not a valid playlist dictionary."

    @field_validator("playlist", mode="before")
    @classmethod
    def playlist_is_list(cls, value: Any) -> list[PlaylistData]:
        if isinstance(value, PlaylistParameters):
            ret_val = [PlaylistData.model_validate(year) for year in value.mc_years.values()]
        elif isinstance(value, list):
            ret_val = [PlaylistData.model_validate(year) for year in value]
        else:
            raise ValueError("Not a valid playlist.")
        return ret_val

    @model_validator(mode="before")
    @classmethod
    def handle_dict_validation(cls, data: Any) -> Any:
        return_value = data
        if isinstance(data, dict):
            if "playlist" in data.keys() and isinstance(data["playlist"], dict):
                try:
                    playlist = [PlaylistData.model_validate(year) for year in data["playlist"]["mc_years"].values()]
                except KeyError:
                    try:
                        playlist = [PlaylistData.model_validate(year) for year in data["playlist"].values()]
                    except ValidationError:
                        raise ValueError(cls._playlist_dict_error_msg)
                return_value = {"playlist": playlist}
            elif "mc_years" in data.keys():
                playlist = [PlaylistData.model_validate(year) for year in data["mc_years"].values()]
                return_value = {"playlist": playlist}
        return return_value

    # Custom serializer is necessary to preserve compatibility with AntaREST
    @model_serializer
    def ser_mod(self) -> dict[int, PlaylistData]:
        return self.mc_years

    @property
    def playlist_reset(self) -> bool:
        return sum([year.status for year in self.playlist]) > (len(self.playlist) / 2)

    @property
    def mc_years(self) -> dict[int, PlaylistData]:
        return {year + 1: self.playlist[year] for year in range(len(self.playlist))}

    @property
    def ini_fields(self) -> dict:
        playlist_years = repr(
            [str(year) for year, year_obj in enumerate(self.playlist) if year_obj.status ^ self.playlist_reset]
        )

        playlist_year_dict = {"playlist_year " + ("-" if self.playlist_reset else "+"): playlist_years}

        return {
            "playlist": {
                "playlist_reset": str(self.playlist_reset).lower(),
            }
            | playlist_year_dict
        }
