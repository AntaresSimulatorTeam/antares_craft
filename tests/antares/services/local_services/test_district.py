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

import pytest

from pathlib import Path

from antares.craft import District, Study, read_study_local
from antares.craft.exceptions.exceptions import DistrictsRetrievalError


def test_read_districts(local_study_w_areas: Study) -> None:
    study = local_study_w_areas
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    content = """[all areas]
caption = All areas
output = false
comments = Spatial aggregates on all areas
apply-filter = add-all

[group_one]
caption = Europe
comments = A custom district
apply-filter = remove-all
+ = it
+ = fr
+ = fr

[group_two]
caption = Europe
apply-filter = add-all
- = it

[empty]
"""
    sets_path.write_text(content, encoding="utf-8")
    original_content = sets_path.read_bytes()

    districts = read_study_local(Path(study.path)).get_districts()

    assert districts == {
        "all areas": District(
            name="All areas", output=False, comments="Spatial aggregates on all areas", areas=["fr", "it"]
        ),
        "group_one": District(name="Europe", comments="A custom district", areas=["fr", "it"]),
        "group_two": District(name="Europe", areas=["fr"]),
        "empty": District(name="empty"),
    }
    assert sets_path.read_bytes() == original_content


def test_read_no_districts(local_study_w_areas: Study) -> None:
    sets_path = Path(local_study_w_areas.path) / "input" / "areas" / "sets.ini"
    sets_path.unlink()

    assert read_study_local(Path(local_study_w_areas.path)).get_districts() == {}


def test_read_invalid_district_raises_domain_error(local_study_w_areas: Study) -> None:
    sets_path = Path(local_study_w_areas.path) / "input" / "areas" / "sets.ini"
    sets_path.write_text("[bad]\noutput = invalid\n", encoding="utf-8")

    with pytest.raises(DistrictsRetrievalError, match="Could not retrieve districts from study 'studyTest'"):
        read_study_local(Path(local_study_w_areas.path))
