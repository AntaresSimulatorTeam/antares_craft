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

from io import StringIO
from typing import Any

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import DistrictCreationError, DistrictDeletionError, DistrictsRetrievalError
from antares.craft.model.district import District
from antares.craft.service.base_services import BaseDistrictService
from antares.craft.service.local_services.models.district import DistrictLocal
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.serde_local.ini_common import any_section_option_matcher
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniConfigParser
from antares.study.version import StudyVersion


class DistrictLocalService(BaseDistrictService):
    def __init__(self, config: LocalConfiguration, study_name: str, study_version: StudyVersion) -> None:
        super().__init__()
        self.config = config
        self.study_name = study_name
        self.study_version = study_version

    def _read_ini_text(self) -> str:
        path = self.config.study_path / "input" / "areas" / "sets.ini"
        raw_content = path.read_bytes() if path.exists() else b""
        try:
            return raw_content.decode("utf-8")
        except UnicodeDecodeError:
            return raw_content.decode("cp1252")

    def read_ini(self, text: str | None = None) -> dict[str, Any]:
        """Read the raw district definitions from sets.ini."""
        reader = IniReader(
            ["+", "-"],
            value_parsers={any_section_option_matcher(key): str for key in ["caption", "comments", "+", "-"]},
        )
        return reader.read(StringIO(self._read_ini_text() if text is None else text, newline=None))

    def _save_ini(self, content: dict[str, Any]) -> None:
        # Keep existing rules in order: regrouping repeated +, - or apply-filter keys changes their meaning.
        path = self.config.study_path / "input" / "areas" / "sets.ini"
        text = self._read_ini_text()

        existing_sections = set()
        section = ""
        lines = []
        for line in text.splitlines(keepends=True):
            stripped = line.strip()
            if stripped.startswith("["):
                section = stripped[1:-1]
                existing_sections.add(section)
            if section:
                if section not in content:
                    continue
                key, separator, value = stripped.partition("=")
                if separator and key.strip() in {"+", "-"}:
                    if value.strip() not in content[section].get(key.strip(), []):
                        continue
            lines.append(line)

        new_sections = {key: value for key, value in content.items() if key not in existing_sections}
        writer = IniConfigParser(special_keys=["+", "-"])
        writer.read_dict(new_sections)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as stream:
            stream.writelines(lines)
            if new_sections and lines and not lines[-1].endswith(("\n", "\r")):
                stream.write("\n")
            writer.write(stream)

    @override
    def read_districts(self, all_areas: list[str]) -> dict[str, District]:
        try:
            text = self._read_ini_text()
            content = self.read_ini(text)
            selected_areas: dict[str, set[str]] = {district_id: set() for district_id in content}
            section = "settings"
            for line in StringIO(text, newline=None):
                stripped = line.strip()
                if not stripped or stripped.startswith((";", "#")):
                    continue
                if stripped.startswith("["):
                    section = stripped[1:-1]
                    continue
                key, value = map(str.strip, stripped.split("=", 1))
                areas = selected_areas[section]
                if key == "+":
                    areas.add(value)
                elif key == "-":
                    areas.discard(value)
                elif key == "apply-filter":
                    if value == "add-all":
                        areas.update(all_areas)
                    elif value in {"remove-all", ""}:
                        areas.clear()
                    else:
                        raise ValueError(f"Invalid district filter: {value!r}")

            return {
                district_id: DistrictLocal.model_validate({"caption": district_id, **values}).to_user_model(
                    list(selected_areas[district_id])
                )
                for district_id, values in content.items()
            }
        except (OSError, ValueError) as e:
            raise DistrictsRetrievalError(self.study_name, str(e)) from e

    @override
    def create_districts(self, districts: list[District]) -> list[District]:
        current_content = self.read_ini()
        created = []
        for district in districts:
            if "\n" in district.comments or "\r" in district.comments:
                raise DistrictCreationError(district.name, "Multiline comments are not supported in local studies")
            district_id = transform_name_to_id(district.name)
            if district_id in current_content:
                raise DistrictCreationError(district.name, f"District '{district_id}' already exists")
            local_model = DistrictLocal.from_user_model(district, self.study_version)
            current_content[district_id] = local_model.model_dump(mode="json", by_alias=True)
            created.append(local_model.to_user_model(local_model.add_areas))

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
