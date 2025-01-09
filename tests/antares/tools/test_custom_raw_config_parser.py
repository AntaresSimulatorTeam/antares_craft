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

from pathlib import Path

from antares.craft.tools.custom_raw_config_parser import CustomRawConfigParser


class TestCustomRawConfigParser:
    def test_write(self, tmp_path: Path) -> None:
        path = tmp_path / "test.ini"

        expected_ini_content = """[part]
key_int = 1
key_float = 2.1
key_str = value1

[partWithCapitals]
key_bool = True
key_bool2 = False
keyWithCapital = True

[partWithSameKey]
key = value1
key = value2
key = value3
key2 = 4,2
key2 = 1,3
key3 = [1, 2, 3]

"""

        json_data = {
            "part": {"key_int": 1, "key_float": 2.1, "key_str": "value1"},
            "partWithCapitals": {
                "key_bool": True,
                "key_bool2": False,
                "keyWithCapital": True,
            },
            "partWithSameKey": {
                "key": ["value1", "value2", "value3"],
                "key2": ["4,2", "1,3"],
                "key3": [1, 2, 3],
            },
        }
        writer = CustomRawConfigParser(special_keys=["key", "key2"])
        writer.read_dict(json_data)
        with path.open("w") as file:
            writer.write(file)

        actual_file_content = path.read_text()

        assert actual_file_content == expected_ini_content
