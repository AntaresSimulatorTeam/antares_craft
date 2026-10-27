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

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import DistrictCreationError, DistrictDeletionError
from antares.craft.model.district import District
from antares.craft.service.base_services import BaseDistrictService
from antares.craft.service.local_services.models.district import DistrictLocal
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.serde_local.ini_common import any_section_option_matcher
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.study.version import StudyVersion


class DistrictLocalService(BaseDistrictService):
    def __init__(self, config: LocalConfiguration, study_name: str, study_version: StudyVersion) -> None:
        self.config = config
        self.study_name = study_name
        self.study_version = study_version

    def read_ini(self) -> dict[str, Any]:
        """Read the raw district definitions from sets.ini."""
        reader = IniReader(
            ["+", "-"],
            value_parsers={any_section_option_matcher(key): str for key in ["caption", "comments", "+", "-"]},
        )
        return reader.read(self.config.study_path / "input" / "areas" / "sets.ini")

    def _save_ini(self, content: dict[str, Any]) -> None:
        IniWriter(["+", "-"]).write(content, self.config.study_path / "input" / "areas" / "sets.ini")

    @override
    def create_districts(self, districts: list[District]) -> list[District]:
        current_content = self.read_ini()
        created = []
        for district in districts:
            district_id = transform_name_to_id(district.name)
            if district_id in current_content:
                raise DistrictCreationError(district.name, f"District '{district_id}' already exists")
            local_model = DistrictLocal.from_user_model(district, self.study_version)
            current_content[district_id] = local_model.model_dump(mode="json", by_alias=True)
            created.append(local_model.to_user_model([]))

        self._save_ini(current_content)
        return created

    @override
    def delete_district(self, district_id: str) -> None:
        current_content = self.read_ini()
        if district_id not in current_content:
            raise DistrictDeletionError(district_id, "The district does not exist")

        current_content.pop(district_id)
        self._save_ini(current_content)
