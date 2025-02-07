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
from configparser import DuplicateSectionError
from enum import Enum
from pathlib import Path
from typing import Any, Iterable, Optional, Union

from antares.craft.tools.custom_raw_config_parser import CustomRawConfigParser
from antares.craft.tools.model_tools import filter_out_empty_model_fields
from pydantic import BaseModel


class InitializationFilesTypes(Enum):
    """
    The different initialization files (ini or txt) in an Antares project,
    files that are created for each area require using
    format(area_id=<name>) to get the complete path
    """

    # TODO: Commented inis are not yet handled
    ANTARES = "study.antares"
    # DESKTOP = "Desktop.ini"
    GENERAL = "settings/generaldata.ini"
    # SCENARIO = "settings/scenariobuilder.dat"
    AREAS_SETS_INI = "input/areas/sets.ini"
    AREAS_LIST_TXT = "input/areas/list.txt"
    AREA_OPTIMIZATION_INI = "input/areas/{area_id}/optimization.ini"
    AREA_UI_INI = "input/areas/{area_id}/ui.ini"
    AREA_ADEQUACY_PATCH_INI = "input/areas/{area_id}/adequacy_patch.ini"
    BINDING_CONSTRAINTS_INI = "input/bindingconstraints/bindingconstraints.ini"

    HYDRO_CORRELATION_INI = "input/hydro/prepro/correlation.ini"
    HYDRO_INI = "input/hydro/hydro.ini"
    HYDRO_CAPACITY_CM_TXT = "input/hydro/common/capacity/creditmodulations_{area_id}.txt"
    HYDRO_CAPACITY_RE_TXT = "input/hydro/common/capacity/reservoir_{area_id}.txt"
    HYDRO_CAPACITY_WV_TXT = "input/hydro/common/capacity/waterValues_{area_id}.txt"
    HYDRO_CAPACITY_IP_TXT = "input/hydro/common/capacity/inflowPattern_{area_id}.txt"
    HYDRO_SERIES_ROR_TXT = "input/hydro/series/{area_id}/ror.txt"
    HYDRO_SERIES_MOD_TXT = "input/hydro/series/{area_id}/mod.txt"
    HYDRO_SERIES_MIN_GEN_TXT = "input/hydro/series/{area_id}/mingen.txt"
    HYDRO_COMMON_MAX_POWER = "input/hydro/common/capacity/maxpower_{area_id}.txt"

    LINK_PROPERTIES_INI = "input/links/{area_id}/properties.ini"
    LOAD_CORRELATION_INI = "input/load/prepro/correlation.ini"
    LOAD_SETTINGS_INI = "input/load/prepro/{area_id}/settings.ini"
    RENEWABLES_LIST_INI = "input/renewables/clusters/{area_id}/list.ini"
    SOLAR_CORRELATION_INI = "input/solar/prepro/correlation.ini"
    SOLAR_SETTINGS_INI = "input/solar/prepro/{area_id}/settings.ini"
    ST_STORAGE_LIST_INI = "input/st-storage/clusters/{area_id}/list.ini"

    THERMAL_AREAS_INI = "input/thermal/areas.ini"
    THERMAL_LIST_INI = "input/thermal/clusters/{area_id}/list.ini"
    THERMAL_MODULATION = "input/thermal/prepro/{area_id}/{cluster_id}/modulation.txt"
    THERMAL_DATA = "input/thermal/prepro/{area_id}/{cluster_id}/data.txt"
    THERMAL_SERIES = "input/thermal/series/{area_id}/{cluster_id}/series.txt"

    WIND_CORRELATION_INI = "input/wind/prepro/correlation.ini"
    WIND_SETTINGS_INI = "input/wind/prepro/{area_id}/settings.ini"
    WIND_SERIES = "input/wind/series/wind_{area_id}.txt"


class IniFile:
    def __init__(
        self,
        study_path: Path,
        ini_file_type: InitializationFilesTypes,
        area_id: Optional[str] = None,
        cluster_id: Optional[str] = None,
        ini_contents: Union[CustomRawConfigParser, dict[str, dict[str, str]], None] = None,
    ) -> None:
        if "{area_id}" in ini_file_type.value and not area_id:
            raise ValueError(f"Area name not provided, ini type {ini_file_type.name} requires 'area_id'")
        self._full_path = study_path / (
            ini_file_type.value.format(area_id=area_id, cluster_id=cluster_id)
            if ("{area_id}" in ini_file_type.value and area_id)
            else ini_file_type.value
        )
        self._file_name = self._full_path.name
        self._file_path = self._full_path.parent
        if isinstance(ini_contents, dict):
            self.ini_dict = ini_contents
        elif isinstance(ini_contents, CustomRawConfigParser):
            self._ini_contents = ini_contents
        else:
            self._ini_contents = CustomRawConfigParser()
        if self._full_path.is_file():
            self.update_from_ini_file()
        else:
            self.write_ini_file()

    @property
    def ini_dict(self) -> dict[str, Any]:
        """Ini contents as a python dictionary"""
        return {section: dict(self._ini_contents[section]) for section in self._ini_contents.sections()}

    @ini_dict.setter
    def ini_dict(self, new_ini_dict: dict[str, dict[str, str]]) -> None:
        self._ini_contents = CustomRawConfigParser()
        self._ini_contents.read_dict(new_ini_dict)

    @property
    def ini_dict_binding_constraints(self) -> dict[str, dict[str, str]]:
        return {section: dict(self._ini_contents[section]) for section in self._ini_contents.sections()}

    @ini_dict_binding_constraints.setter
    def ini_dict_binding_constraints(self, new_ini_dict: dict[str, dict[str, str]]) -> None:
        """Set INI file contents for binding constraints."""
        self._ini_contents = CustomRawConfigParser()
        for index, values in enumerate(new_ini_dict.values()):
            self._ini_contents.add_section(str(index))
            for key, value in values.items():
                self._ini_contents.set(str(index), key, value)

    @property
    def parsed_ini(self) -> CustomRawConfigParser:
        """Ini contents as a CustomRawConfigParser"""
        return self._ini_contents

    @parsed_ini.setter
    def parsed_ini(self, new_ini_contents: CustomRawConfigParser) -> None:
        self._ini_contents = new_ini_contents

    @property
    def ini_path(self) -> Path:
        """Ini path"""
        return self._full_path

    def add_section(self, section: Any, append: bool = False) -> None:
        if isinstance(section, dict):
            self._check_if_duplicated_section_names(section.keys(), append)
            self._ini_contents.read_dict(section)
        elif isinstance(section, Path):
            with section.open() as ini_file:
                temp_parser = CustomRawConfigParser()
                temp_parser.read_file(ini_file)
                self._check_if_duplicated_section_names(temp_parser.sections(), append)
                self._ini_contents.read_file(ini_file)
        else:
            raise TypeError(f"Only dict or Path are allowed, received {type(section)}")

    def _check_if_duplicated_section_names(self, sections: Iterable[str], append: bool = False) -> None:
        for section in sections:
            if section in self.ini_dict and not append:
                raise DuplicateSectionError(section)

    def update_from_ini_file(self) -> None:
        if not self._full_path.is_file():
            raise FileNotFoundError(f"No such file: {self._full_path}")

        parsed_ini = CustomRawConfigParser()
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
    def _sort_ini_sections(ini_to_sort: CustomRawConfigParser) -> CustomRawConfigParser:
        sorted_ini = CustomRawConfigParser()
        for section in sorted(ini_to_sort.sections()):
            sorted_ini[section] = ini_to_sort[section]
        return sorted_ini

    @staticmethod
    def _sort_ini_section_content(ini_to_sort: CustomRawConfigParser) -> CustomRawConfigParser:
        sorted_ini = CustomRawConfigParser()
        for section in ini_to_sort.sections():
            sorted_ini[section] = {key: value for (key, value) in sorted(list(ini_to_sort[section].items()))}
        return sorted_ini

    @classmethod
    def create_hydro_initialization_files_for_area(cls, study_path: Path, area_id: str) -> None:
        """
        Creates IniFile instances for HYDRO_CAPACITY files

        Args:
            study_path (Path): The base path for the study.
            area_id (str): The area ID.

        Returns:
            list[IniFile]: A list of IniFile instances for the capacity files.
        """
        capacity_files = [
            InitializationFilesTypes.HYDRO_CAPACITY_CM_TXT,
            InitializationFilesTypes.HYDRO_CAPACITY_RE_TXT,
            InitializationFilesTypes.HYDRO_CAPACITY_WV_TXT,
            InitializationFilesTypes.HYDRO_CAPACITY_IP_TXT,
            InitializationFilesTypes.HYDRO_SERIES_ROR_TXT,
            InitializationFilesTypes.HYDRO_SERIES_MOD_TXT,
            InitializationFilesTypes.HYDRO_SERIES_MIN_GEN_TXT,
            InitializationFilesTypes.HYDRO_COMMON_MAX_POWER,
        ]

        for file_type in capacity_files:
            cls(study_path=study_path, ini_file_type=file_type, area_id=area_id)

    @classmethod
    def create_link_ini_for_area(cls, study_path: Path, area_id: str) -> None:
        property_file = InitializationFilesTypes.LINK_PROPERTIES_INI

        cls(study_path=study_path, ini_file_type=property_file, area_id=area_id)

    @classmethod
    def create_list_ini_for_area(cls, study_path: Path, area_id: str) -> None:
        property_file = InitializationFilesTypes.THERMAL_LIST_INI

        cls(study_path=study_path, ini_file_type=property_file, area_id=area_id)


def merge_dicts_for_ini(dict_a: dict[str, Any], dict_b: dict[str, Any]) -> dict[str, Any]:
    """
    Merges two dictionaries, combining fields with the same name into a list of the values in the fields.

    Args:
        dict_a: The first dictionary.
        dict_b: The second dictionary.

    Returns:
          dict: The merged dictionary.
    """

    def _ensure_list(item: Any) -> list[Any]:
        return item if isinstance(item, list) else [item]

    def _filter_out_empty_list_entries(list_of_entries: list[Any]) -> list[Any]:
        return [entry for entry in list_of_entries if entry]

    output_dict = dict_a | dict_b
    for key, value in output_dict.items():
        if key in dict_a and key in dict_b:
            if isinstance(dict_a[key], dict):
                output_dict[key] = merge_dicts_for_ini(dict_a[key], dict_b[key])
            else:
                flat_list = _ensure_list(dict_a[key]) + _ensure_list(dict_b[key])
                output_dict[key] = _filter_out_empty_list_entries(flat_list)
    return output_dict


def get_ini_fields_for_ini(model: BaseModel) -> dict[str, Any]:
    """
    Creates a dictionary of the property `ini_fields` from a `BaseModel` object that contains the merged dictionaries
    of all the `ini_fields` properties.

    Args:
        model (BaseModel): A `BaseModel` object containing other objects.

    Returns:
        dict[str, Any]: A dictionary of the property `ini_fields` from the contained objects.
    """
    list_of_model_fields = filter_out_empty_model_fields(model)
    list_of_ini_fields = [getattr(model, field).ini_fields for field in list_of_model_fields]
    output_dict: dict[str, Any] = {}
    # output_dict is annotated because of the complexity of understanding the output of the function, see:
    # https://mypy.readthedocs.io/en/stable/common_issues.html#types-of-empty-collections
    for dict_item in list_of_ini_fields:
        output_dict = merge_dicts_for_ini(output_dict, dict_item)
    return output_dict
