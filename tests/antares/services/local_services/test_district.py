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

import pytest

from pathlib import Path

from antares.craft import District, Study, read_study_local
from antares.craft.exceptions.exceptions import DistrictCreationError, DistrictDeletionError, DistrictsRetrievalError
from antares.craft.tools.serde_local.ini_reader import IniReader


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


@pytest.mark.parametrize("study_fixture", ["local_study_w_areas", "local_study_10_2"])
def test_create_districts(request: pytest.FixtureRequest, study_fixture: str) -> None:
    local_study: Study = request.getfixturevalue(study_fixture)
    sets_path = Path(local_study.path) / "input" / "areas" / "sets.ini"
    with sets_path.open("a") as stream:
        stream.write("\n[existing]\ncaption = Existing\ncustom-field = preserved\n- = it\n")
    original = IniReader(["+", "-"]).read(sets_path)
    study = read_study_local(Path(local_study.path))
    initial_districts = dict(study.get_districts())
    districts = [
        District(name="Europe", areas=["it", "fr", "fr"], comments="Test district"),
        District(name="France", output=False, areas=["fr"]),
        District(name="Empty"),
    ]

    created = study.create_districts(districts)

    assert created == [District(name="Europe", areas=["fr", "it"], comments="Test district"), *districts[1:]]
    expected = initial_districts | dict(zip(["europe", "france", "empty"], created))
    assert study.get_districts() == expected
    assert read_study_local(Path(study.path)).get_districts() == expected
    content = IniReader(["+", "-"]).read(sets_path)
    assert {key: content[key] for key in original} == original
    assert content["europe"]["apply-filter"] == "remove-all"
    assert content["europe"]["+"] == ["fr", "it"]
    for key in ["filter-synthesis", "filter-year-by-year"]:
        if study_fixture == "local_study_10_2":
            assert set(content["europe"][key].split(", ")) == {"hourly", "daily", "weekly", "monthly", "annual"}
        else:
            assert key not in content["europe"]
    before = sets_path.read_bytes()
    assert study.create_districts([]) == []
    assert sets_path.read_bytes() == before


@pytest.mark.parametrize(
    "districts, message",
    [
        ([District("France"), District("FRANCE")], "already exists"),
        ([District("Valid"), District("Missing", areas=["unknown"])], "Areas do not exist: unknown"),
        ([District("Valid"), District("Bad/name")], "name must contain"),
        ([District("Valid"), District(" padded ")], "name must contain"),
        ([District("Valid"), District("EXISTING")], "already exists"),
        ([District("Valid"), District("")], "identifier must not be empty"),
        ([District("Valid"), District("   ")], "identifier must not be empty"),
        ([District("Valid"), District("Europe", comments="Line 1\nLine 2")], "Multiline comments"),
        ([District("Valid"), District("Europe", comments="Line 1\rLine 2")], "Multiline comments"),
        ([District("Valid"), District("Europe", comments="Line 1\r\nLine 2")], "Multiline comments"),
    ],
)
def test_create_districts_rejects_invalid_batch(
    local_study_w_areas: Study, districts: list[District], message: str
) -> None:
    study = local_study_w_areas
    study.create_districts([District("Existing")])
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    before = sets_path.read_bytes()
    initial_districts = dict(study.get_districts())

    with pytest.raises(DistrictCreationError, match=message):
        study.create_districts(districts)

    assert sets_path.read_bytes() == before
    assert study.get_districts() == initial_districts


def test_create_districts_checks_existing_file(local_study_w_areas: Study) -> None:
    study = local_study_w_areas
    read_study_local(Path(study.path)).create_districts([District("Existing")])
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    before = sets_path.read_bytes()
    initial_districts = dict(study.get_districts())

    with pytest.raises(DistrictCreationError, match="already exists"):
        study.create_districts([District("Valid"), District("Existing")])

    assert sets_path.read_bytes() == before
    assert study.get_districts() == initial_districts


def test_delete_district(local_study_w_areas: Study) -> None:
    study = read_study_local(Path(local_study_w_areas.path))
    study.create_districts([District("To delete", areas=["fr"]), District("Keep", output=False, areas=["it"])])
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    expected_content = IniReader(["+", "-"]).read(sets_path)
    expected_content.pop("to delete")
    expected_districts = dict(study.get_districts())
    expected_districts.pop("to delete")

    study.delete_district("to delete")

    assert study.get_districts() == expected_districts
    assert read_study_local(Path(study.path)).get_districts() == expected_districts
    assert IniReader(["+", "-"]).read(sets_path) == expected_content


def test_delete_unknown_district(local_study_w_areas: Study) -> None:
    study = read_study_local(Path(local_study_w_areas.path))
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    before = sets_path.read_bytes()
    initial_districts = dict(study.get_districts())

    with pytest.raises(
        DistrictDeletionError, match="Could not delete the district 'unknown': The district does not exist"
    ):
        study.delete_district("unknown")

    assert sets_path.read_bytes() == before
    assert study.get_districts() == initial_districts


def test_districts_follow_area_changes(local_study_w_areas: Study) -> None:
    study = local_study_w_areas
    study.create_area("001")
    assert study.get_districts()["all areas"].areas == ["001", "fr", "it"]
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    with sets_path.open("a") as stream:
        stream.write("\n[legacy]\ncaption = 001\n+ = 001\n+ = 001\n+ = fr\n- = 001\ncomments = true\n")
    study = read_study_local(Path(study.path))

    study.create_area("de")
    assert study.get_districts()["all areas"].areas == ["001", "de", "fr", "it"]
    assert study.get_districts()["legacy"].areas == ["001", "fr"]
    study.delete_area(study.get_areas()["001"])

    assert study.get_districts()["all areas"].areas == ["de", "fr", "it"]
    assert study.get_districts()["legacy"] == District("001", comments="true", areas=["fr"])
    assert read_study_local(Path(study.path)).get_districts() == study.get_districts()
    assert "001" not in IniReader(["+", "-"]).read(sets_path)["legacy"].get("-", [])
