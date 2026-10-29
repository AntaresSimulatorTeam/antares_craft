# Copyright (c) 2024-2026, RTE (https://www.rte-france.com)
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

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import DistrictCreationError, DistrictDeletionError, DistrictsRetrievalError
from antares.craft.model.district import District, DistrictProperties
from antares.craft.service.base_services import BaseDistrictService
from antares.craft.service.local_services.models.district import parse_district_local, serialize_district_local
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.serde_local.ini_common import any_section_option_matcher
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.study.version import StudyVersion


class DistrictLocalService(BaseDistrictService):
    def __init__(self, config: LocalConfiguration, study_name: str, study_version: StudyVersion) -> None:
        super().__init__()
        self.config = config
        self.study_name = study_name
        self.study_version = study_version

    def read_ini(self) -> dict[str, Any]:
        """Read the raw district definitions from sets.ini."""
        reader = IniReader(
            ["+", "-"],
            value_parsers={any_section_option_matcher(key): str for key in ["caption", "comments", "+", "-"]},
        )
        path = self.config.study_path / "input" / "areas" / "sets.ini"
        return reader.read(path)

    def _save_ini(self, content: dict[str, Any]) -> None:
        path = self.config.study_path / "input" / "areas" / "sets.ini"
        IniWriter(special_keys=["+", "-"]).write(content, path)

    def read_districts(self, all_areas: list[str]) -> dict[str, District]:
        try:
            districts = {}
            for district_id, values in self.read_ini().items():
                name = values.pop("caption", district_id)
                properties = parse_district_local(self.study_version, values, all_areas)
                districts[district_id] = District(name, self, properties, district_id=district_id)
            return districts
        except (OSError, ValueError) as e:
            raise DistrictsRetrievalError(self.study_name, str(e)) from e

    @override
    def create_districts(self, districts: dict[str, DistrictProperties]) -> list[District]:
        current_content = self.read_ini()
        areas_path = self.config.study_path / "input" / "areas"
        existing_area_ids = {path.name for path in areas_path.iterdir() if path.is_dir()}
        created = []
        for name, properties in districts.items():
            district_id = transform_name_to_id(name)
            if not district_id:
                raise DistrictCreationError(name, "The district identifier must not be empty")
            if district_id in current_content:
                raise DistrictCreationError(name, f"District '{district_id}' already exists")
            missing_areas = sorted(set(properties.areas).difference(existing_area_ids))
            if missing_areas:
                raise DistrictCreationError(name, f"Areas do not exist: {', '.join(missing_areas)}")
            values = serialize_district_local(self.study_version, properties)
            current_content[district_id] = {"caption": name, **values}
            created.append(District(name, self, parse_district_local(self.study_version, values, [])))

        self._save_ini(current_content)
        return created

    @override
    def delete_district(self, district_id: str) -> None:
        current_content = self.read_ini()
        if district_id not in current_content:
            raise DistrictDeletionError(district_id, "The district does not exist")

        current_content.pop(district_id)
        self._save_ini(current_content)

    def remove_area(self, area_id: str) -> None:
        """Remove every reference to a deleted area, preserving selection rules."""
        current_content = self.read_ini()
        for district in current_content.values():
            for key in ["+", "-"]:
                if key in district:
                    district[key] = [area for area in district[key] if area != area_id]
        self._save_ini(current_content)
