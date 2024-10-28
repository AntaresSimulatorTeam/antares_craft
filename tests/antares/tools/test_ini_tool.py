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
from pydantic import BaseModel

from antares.tools.ini_tool import get_ini_fields_for_ini, merge_dicts_for_ini


class TestExtraFunctions:
    def test_merging_two_simple_dicts(self):
        # Given
        expected_merged_dict = {"test": [123, 456], "test_a": "abc", "test_b": "def"}
        dict_a = {"test": 123, "test_a": "abc"}
        dict_b = {"test": 456, "test_b": "def"}

        # When
        actual_merged_dict = merge_dicts_for_ini(dict_a, dict_b)

        # Then
        assert actual_merged_dict == expected_merged_dict

    def test_merging_three_simple_dicts(self):
        # Given
        expected_merged_dict = {"test": [123, 456, 789], "test_a": "abc", "test_b": "def", "test_c": "ghi"}
        dict_a = {"test": 123, "test_a": "abc"}
        dict_b = {"test": 456, "test_b": "def"}
        dict_c = {"test": 789, "test_c": "ghi"}

        # When
        first_two_dicts_merged = merge_dicts_for_ini(dict_a, dict_b)
        actual_merged_dict = merge_dicts_for_ini(first_two_dicts_merged, dict_c)

        # Then
        assert actual_merged_dict == expected_merged_dict

    def test_get_ini_fields(self):
        # Given
        class ChildObjectOne(BaseModel):
            general: str = "test one"
            test_a: str = "abc"

            @property
            def ini_fields(self):
                return {"general": {"test": self.general, "test_a": self.test_a}}

        class ChildObjectTwo(BaseModel):
            general: str = "test two"
            test_b: str = "def"

            @property
            def ini_fields(self):
                return {"general": {"test": self.general, "test_b": self.test_b}}

        class ParentObject(BaseModel):
            child_one: ChildObjectOne = ChildObjectOne()
            child_two: ChildObjectTwo = ChildObjectTwo()

        expected_ini_fields = {"general": {"test": ["test one", "test two"], "test_a": "abc", "test_b": "def"}}

        # When
        test_model = ParentObject()
        actual_ini_fields = get_ini_fields_for_ini(test_model)

        # Then
        assert actual_ini_fields == expected_ini_fields
