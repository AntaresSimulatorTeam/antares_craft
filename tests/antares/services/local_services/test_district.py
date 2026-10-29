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

from dataclasses import replace
from pathlib import Path

from antares.craft import DistrictProperties, Study, read_study_local
from antares.craft.exceptions.exceptions import (
    DistrictCreationError,
    DistrictDeletionError,
    DistrictsRetrievalError,
    InvalidFieldForVersionError,
)
from antares.craft.model.commons import FilterOption
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

    assert {key: district.properties for key, district in districts.items()} == {
        "all areas": DistrictProperties(output=False, comments="Spatial aggregates on all areas", areas=["fr", "it"]),
        "group_one": DistrictProperties(comments="A custom district", areas=["fr", "it"]),
        "group_two": DistrictProperties(areas=["fr"]),
        "empty": DistrictProperties(),
    }
    assert {key: district.id for key, district in districts.items()} == {key: key for key in districts}
    assert districts["group_one"].name == "Europe"
    assert sets_path.read_bytes() == original_content


@pytest.mark.parametrize(
    "rules, expected_areas",
    [
        ("apply-filter = remove-all\n+ = fr\n+ = it\n- = it\n", ["fr", "it"]),
        ("+ = fr\n- = fr\n", ["fr"]),
        ("+ = fr\r- = fr\r", ["fr"]),
        ("+ = fr\n- = fr\n+ = fr\n", ["fr"]),
        ("apply-filter = add-all\n- = it\n+ = it\n", ["fr"]),
        ("+ = fr\napply-filter = remove-all\n+ = it\n", ["fr", "it"]),
        ("apply-filter = add-all\n- = fr\napply-filter = add-all\n- = it\n", []),
        ("apply-filter = add-all\napply-filter = remove-all\n+ = fr\n", ["fr"]),
        ("+ = fr\n; - = fr\n# apply-filter = remove-all\n- = it\n", ["fr"]),
        ("+ = fr\n[legacy]\n- = fr\n+ = it\n", ["fr", "it"]),
    ],
)
def test_read_district_filters(local_study_w_areas: Study, rules: str, expected_areas: list[str]) -> None:
    study = local_study_w_areas
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    sets_path.write_text("[legacy]\n" + rules, encoding="utf-8")
    original_content = sets_path.read_bytes()

    districts = read_study_local(Path(study.path)).get_districts()

    assert districts["legacy"].properties.areas == expected_areas
    assert sets_path.read_bytes() == original_content


def test_read_no_districts(local_study_w_areas: Study) -> None:
    sets_path = Path(local_study_w_areas.path) / "input" / "areas" / "sets.ini"
    sets_path.unlink()

    assert read_study_local(Path(local_study_w_areas.path)).get_districts() == {}


@pytest.mark.parametrize(
    "rules",
    ["output = invalid\n", "apply-filter = invalid\n", "custom-field = invalid\n"],
)
def test_read_invalid_district_raises_domain_error(local_study_w_areas: Study, rules: str) -> None:
    sets_path = Path(local_study_w_areas.path) / "input" / "areas" / "sets.ini"
    sets_path.write_text("[bad]\n" + rules, encoding="utf-8")

    with pytest.raises(DistrictsRetrievalError, match="Could not retrieve districts from study 'studyTest'"):
        read_study_local(Path(local_study_w_areas.path))


@pytest.mark.parametrize("study_fixture", ["local_study_w_areas", "local_study_10_2"])
def test_create_districts(request: pytest.FixtureRequest, study_fixture: str) -> None:
    local_study: Study = request.getfixturevalue(study_fixture)
    sets_path = Path(local_study.path) / "input" / "areas" / "sets.ini"
    with sets_path.open("a") as stream:
        stream.write("\n[existing]\ncaption = Existing\n- = it\n")
    original = IniReader(["+", "-"]).read(sets_path)
    study = read_study_local(Path(local_study.path))
    initial_districts = {key: district.properties for key, district in study.get_districts().items()}
    districts = {
        "Europe": DistrictProperties(areas=["it", "fr", "fr"], comments="  Test district  "),
        "France": DistrictProperties(output=False, areas=["fr"]),
        "Empty": DistrictProperties(),
        "Bad/name": DistrictProperties(),
    }

    created = study.create_districts(districts)

    expected_created = [DistrictProperties(areas=["fr", "it"], comments="Test district"), *list(districts.values())[1:]]
    if study_fixture == "local_study_10_2":
        expected_created = [
            replace(district, filter_synthesis=set(FilterOption), filter_year_by_year=set(FilterOption))
            for district in expected_created
        ]
    assert [district.properties for district in created] == expected_created
    assert [district.name for district in created] == list(districts)
    assert [district.id for district in created] == ["europe", "france", "empty", "bad name"]
    expected = initial_districts | dict(zip(["europe", "france", "empty", "bad name"], expected_created))
    assert {key: district.properties for key, district in study.get_districts().items()} == expected
    assert {
        key: district.properties for key, district in read_study_local(Path(study.path)).get_districts().items()
    } == expected
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
    assert study.create_districts({}) == []
    assert sets_path.read_bytes() == before

    padded = study.create_districts({" padded ": DistrictProperties()})[0]
    assert study.get_districts()["padded"] == padded

    filtered = DistrictProperties(filter_synthesis={FilterOption.DAILY}, filter_year_by_year=set())
    if study_fixture == "local_study_10_2":
        assert study.create_districts({"Filtered": filtered})[0].properties == filtered
        assert read_study_local(Path(study.path)).get_districts()["filtered"].properties == filtered
    else:
        with pytest.raises(InvalidFieldForVersionError):
            study.create_districts({"Filtered": filtered})


@pytest.mark.parametrize(
    "districts, message",
    [
        ({"France": DistrictProperties(), "FRANCE": DistrictProperties()}, "already exists"),
        (
            {"Valid": DistrictProperties(), "Missing": DistrictProperties(areas=["unknown"])},
            "Areas do not exist: unknown",
        ),
        ({"Valid": DistrictProperties(), "EXISTING": DistrictProperties()}, "already exists"),
        ({"Valid": DistrictProperties(), "": DistrictProperties()}, "identifier must not be empty"),
        ({"Valid": DistrictProperties(), "   ": DistrictProperties()}, "identifier must not be empty"),
    ],
)
def test_create_districts_rejects_invalid_batch(
    local_study_w_areas: Study, districts: dict[str, DistrictProperties], message: str
) -> None:
    study = local_study_w_areas
    study.create_districts({"Existing": DistrictProperties()})
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    before = sets_path.read_bytes()
    initial_districts = {key: district.properties for key, district in study.get_districts().items()}

    with pytest.raises(DistrictCreationError, match=message):
        study.create_districts(districts)

    assert sets_path.read_bytes() == before
    assert {key: district.properties for key, district in study.get_districts().items()} == initial_districts


def test_create_districts_checks_existing_file(local_study_w_areas: Study) -> None:
    study = local_study_w_areas
    read_study_local(Path(study.path)).create_districts({"Existing": DistrictProperties()})
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    before = sets_path.read_bytes()
    initial_districts = {key: district.properties for key, district in study.get_districts().items()}

    with pytest.raises(DistrictCreationError, match="already exists"):
        study.create_districts({"Valid": DistrictProperties(), "Existing": DistrictProperties()})

    assert sets_path.read_bytes() == before
    assert {key: district.properties for key, district in study.get_districts().items()} == initial_districts


def test_delete_district(local_study_w_areas: Study) -> None:
    study = read_study_local(Path(local_study_w_areas.path))
    study.create_districts(
        {"To delete": DistrictProperties(areas=["fr"]), "Keep": DistrictProperties(output=False, areas=["it"])}
    )
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    expected_content = IniReader(["+", "-"]).read(sets_path)
    expected_content.pop("to delete")
    expected_districts = {key: district.properties for key, district in study.get_districts().items()}
    expected_districts.pop("to delete")

    study.delete_district("to delete")

    assert {key: district.properties for key, district in study.get_districts().items()} == expected_districts
    assert {
        key: district.properties for key, district in read_study_local(Path(study.path)).get_districts().items()
    } == expected_districts
    assert IniReader(["+", "-"]).read(sets_path) == expected_content


def test_delete_unknown_district(local_study_w_areas: Study) -> None:
    study = read_study_local(Path(local_study_w_areas.path))
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    before = sets_path.read_bytes()
    initial_districts = {key: district.properties for key, district in study.get_districts().items()}

    with pytest.raises(
        DistrictDeletionError, match="Could not delete the district 'unknown': The district does not exist"
    ):
        study.delete_district("unknown")

    assert sets_path.read_bytes() == before
    assert {key: district.properties for key, district in study.get_districts().items()} == initial_districts


@pytest.mark.parametrize("operation", ["create", "delete", "delete_area"])
@pytest.mark.parametrize("encoding", ["utf-8", "cp1252"])
def test_district_changes_write_grouped_rules(local_study_w_areas: Study, operation: str, encoding: str) -> None:
    study = local_study_w_areas
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    legacy = "[legacy]\r\n; Région française\r\napply-filter = remove-all\r\n+ = fr\r\n- = fr\r\n+ = fr"
    to_delete = "[to delete]\r\n+ = it\r\n\r\n"
    sets_path.write_bytes((to_delete + legacy).encode(encoding))
    study = read_study_local(Path(study.path))

    if operation == "create":
        study.create_districts({"New": DistrictProperties(areas=["it"])})
    elif operation == "delete":
        study.delete_district("to delete")
    else:
        study.delete_area(study.get_areas()["it"])

    saved = IniReader(["+", "-"]).read(sets_path)
    assert saved["legacy"] == {"apply-filter": "remove-all", "+": ["fr", "fr"], "-": ["fr"]}
    if operation == "create":
        assert read_study_local(Path(study.path)).get_districts()["new"].properties.areas == ["it"]
    elif operation == "delete":
        assert "to delete" not in saved
    else:
        assert saved["to delete"] == {}
    assert read_study_local(Path(study.path)).get_districts()["legacy"].properties.areas == ["fr"]


@pytest.mark.parametrize("separator", ["\n", "\r", "\r\n", "\v", "\x85", "\u2028", "\u2029"])
def test_district_changes_preserve_comment_separators(local_study_w_areas: Study, separator: str) -> None:
    study = local_study_w_areas
    if separator in ("\n", "\r", "\r\n"):
        with pytest.raises(ValueError, match="Multiline district comments"):
            DistrictProperties(comments=f"First{separator}Second")
        return
    district = DistrictProperties(areas=["fr"], comments=f"First{separator}[comment]")
    study.create_districts({"Existing": district})

    study.create_districts({"New": DistrictProperties()})
    assert read_study_local(Path(study.path)).get_districts()["existing"].properties == district

    study.delete_district("new")
    assert read_study_local(Path(study.path)).get_districts()["existing"].properties == district


def test_districts_follow_area_changes(local_study_w_areas: Study) -> None:
    study = local_study_w_areas
    study.create_area("es")
    sets_path = Path(study.path) / "input" / "areas" / "sets.ini"
    with sets_path.open("a") as stream:
        stream.write("""
[custom_area]
caption = Custom area district
+ = es
+ = es
+ = fr
- = es
comments = Custom comment
""")
    study = read_study_local(Path(study.path))
    study.create_districts({"Explicit": DistrictProperties(areas=["es", "fr"])})
    districts = study.get_districts()
    all_areas = districts["all areas"]
    assert all_areas.properties.areas == ["es", "fr", "it"]

    study.create_area("de")
    study.delete_area(study.get_areas()["es"])

    assert study.get_districts()["all areas"] is all_areas
    assert all_areas.properties.areas == ["fr", "it"]
    assert districts["explicit"].properties.areas == ["fr"]
    assert study.get_districts()["custom_area"].properties == DistrictProperties(comments="Custom comment", areas=["fr"])
    reloaded_districts = read_study_local(Path(study.path)).get_districts()
    assert reloaded_districts["all areas"].properties.areas == ["de", "fr", "it"]
    assert reloaded_districts["explicit"].properties == districts["explicit"].properties
    assert reloaded_districts["custom_area"].properties == districts["custom_area"].properties
    assert "es" not in IniReader(["+", "-"]).read(sets_path)["custom_area"].get("-", [])
