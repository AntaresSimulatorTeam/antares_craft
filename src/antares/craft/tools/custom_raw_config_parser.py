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
from ast import literal_eval
from configparser import Interpolation, RawConfigParser
from typing import TYPE_CHECKING, Any, ItemsView, Optional

from typing_extensions import override

if TYPE_CHECKING:
    from _typeshed import SupportsWrite


class CustomRawConfigParser(RawConfigParser):
    def __init__(self, special_keys: Optional[list[str]] = None, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        _special_keys: list[str] = [
            "playlist_year_weight",
            "playlist_year +",
            "playlist_year -",
            "select_var -",
            "select_var +",
        ]
        self.special_keys = special_keys if special_keys is not None else _special_keys
        self._interpolation: Interpolation

    # Parent version uses optionstr.lower() and we want to preserve upper- and lower-case
    @override
    def optionxform(self, optionstr: str) -> str:
        return optionstr

    def _write_line(
        self, file_path: "SupportsWrite[str]", section_name: str, delimiter: str, key: str, value: str
    ) -> None:
        """Writes a single line of the provided section to the specified `file_path`."""
        value = self._interpolation.before_write(self, section_name, key, value)
        if value is not None or not self._allow_no_value:
            value = delimiter + str(value).replace("\n", "\n\t")
        else:
            value = ""
        file_path.write(f"{key}{value}\n")

    def _write_section(
        self, fp: "SupportsWrite[str]", section_name: str, section_items: ItemsView[str, str], delimiter: str
    ) -> None:
        """Write a single section to the specified `fp`. Overrides the function in `RawConfigParser`.

        Args:
            fp: Path to the file to write.
            section_name: The name of the section to write.
            section_items: The items to write.
            delimiter: The delimiter used to write the section.
        """
        fp.write(f"[{section_name}]\n")
        for key, value in section_items:
            if self.special_keys and key in self.special_keys and isinstance(literal_eval(value), list):
                for sub_value in literal_eval(value):
                    self._write_line(fp, section_name, delimiter, key, sub_value)
            else:
                self._write_line(fp, section_name, delimiter, key, value)
        fp.write("\n")
