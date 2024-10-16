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

from configparser import ConfigParser
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union, overload


class IniFileTypes(Enum):
    """
    The different ini files in an Antares project, files that are created for each area require using
    format(area_name=<name>) to get the complete path
    """

    # TODO: Commented inis are not yet handled
    # ANTARES = "study.antares"
    # DESKTOP = "Desktop.ini"
    # GENERAL = "settings/generaldata.ini"
    # SCENARIO = "settings/scenariobuilder.dat"
    AREAS_SETS_INI = "input/areas/sets.ini"
    AREAS_LIST_TXT = "input/areas/list.txt"
    AREA_OPTIMIZATION_INI = "input/areas/{area_name}/optimization.ini"
    AREA_UI_INI = "input/areas/{area_name}/ui.ini"
    AREA_ADEQUACY_PATCH_INI = "input/areas/{area_name}/adequacy_patch.ini"
    BINDING_CONSTRAINTS_INI = "input/bindingconstraints/bindingconstraints.ini"
    HYDRO_INI = "input/hydro/hydro.ini"
    LINK_PROPERTIES_INI = "input/links/{area_name}/properties.ini"
    LOAD_CORRELATION_INI = "input/load/prepro/correlation.ini"
    LOAD_SETTINGS_INI = "input/load/prepro/{area_name}/settings.ini"
    RENEWABLES_LIST_INI = "input/renewables/clusters/{area_name}/list.ini"
    SOLAR_CORRELATION_INI = "input/solar/prepro/correlation.ini"
    SOLAR_SETTINGS_INI = "input/solar/prepro/{area_name}/settings.ini"
    ST_STORAGE_LIST_INI = "input/st-storage/clusters/{area_name}/list.ini"
    THERMAL_AREAS_INI = "input/thermal/areas.ini"
    THERMAL_LIST_INI = "input/thermal/clusters/{area_name}/list.ini"
    WIND_CORRELATION_INI = "input/wind/prepro/correlation.ini"
    WIND_SETTINGS_INI = "input/wind/prepro/{area_name}/settings.ini"


class IniFile:
    def __init__(
        self,
        study_path: Path,
        ini_file_type: IniFileTypes,
        area_name: Optional[str] = None,
        ini_contents: Union[ConfigParser, dict[str, dict[str, str]], None] = None,
    ) -> None:
        if "{area_name}" in ini_file_type.value and not area_name:
            raise ValueError(f"Area name not provided, ini type {ini_file_type.name} requires 'area_name'")
        self._full_path = study_path / (
            ini_file_type.value.format(area_name=area_name)
            if ("{area_name}" in ini_file_type.value and area_name)
            else ini_file_type.value
        )
        self._file_name = self._full_path.name
        self._file_path = self._full_path.parent
        if isinstance(ini_contents, dict):
            self.ini_dict = ini_contents
        elif isinstance(ini_contents, ConfigParser):
            self._ini_contents = ini_contents
        else:
            self._ini_contents = ConfigParser(interpolation=None)
        if self._full_path.is_file():
            self.update_from_ini_file()
        else:
            self.write_ini_file()

    @property
    def ini_dict(self) -> dict:
        """Ini contents as a python dictionary"""
        return {section: dict(self._ini_contents[section]) for section in self._ini_contents.sections()}

    @ini_dict.setter
    def ini_dict(self, new_ini_dict: dict[str, dict[str, str]]) -> None:
        self._ini_contents = ConfigParser(interpolation=None)
        self._ini_contents.read_dict(new_ini_dict)

    @property
    def parsed_ini(self) -> ConfigParser:
        """Ini contents as a ConfigParser"""
        return self._ini_contents

    @parsed_ini.setter
    def parsed_ini(self, new_ini_contents: ConfigParser) -> None:
        self._ini_contents = new_ini_contents

    @property
    def ini_path(self) -> Path:
        """Ini path"""
        return self._full_path

    @overload
    def add_section(self, section: Path) -> None: ...

    @overload
    def add_section(self, section: dict[str, dict[str, str]]) -> None: ...

    def add_section(self, section: Any) -> None:
        if isinstance(section, dict):
            self._ini_contents.read_dict(section)
        elif isinstance(section, Path):
            with section.open() as ini_file:
                self._ini_contents.read_file(ini_file)
        else:
            raise TypeError("Only dict or Path are allowed")

    def update_from_ini_file(self) -> None:
        if not self._full_path.is_file():
            raise FileNotFoundError(f"No such file: {self._full_path}")

        parsed_ini = ConfigParser(interpolation=None)
        with self._full_path.open() as file:
            parsed_ini.read_file(file)

        self._ini_contents = parsed_ini

    def write_ini_file(
        self,
        sort_sections: bool = False,
        sort_section_content: bool = False,
    ) -> None:
        if not self._file_path.is_dir():
            self._file_path.mkdir(parents=True)
        ini_to_write = self._ini_contents if not sort_sections else self._sort_ini_sections(self._ini_contents)
        ini_to_write = ini_to_write if not sort_section_content else self._sort_ini_section_content(ini_to_write)

        with self._full_path.open("w") as file:
            ini_to_write.write(file)

    @staticmethod
    def _sort_ini_sections(ini_to_sort: ConfigParser) -> ConfigParser:
        sorted_ini = ConfigParser(interpolation=None)
        for section in sorted(ini_to_sort.sections()):
            sorted_ini[section] = ini_to_sort[section]
        return sorted_ini

    @staticmethod
    def _sort_ini_section_content(ini_to_sort: ConfigParser) -> ConfigParser:
        sorted_ini = ConfigParser(interpolation=None)
        for section in ini_to_sort.sections():
            sorted_ini[section] = {key: value for (key, value) in sorted(list(ini_to_sort[section].items()))}
        return sorted_ini
