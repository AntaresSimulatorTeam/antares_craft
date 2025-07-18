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

import re
import zipfile

from pathlib import Path

import numpy as np
import pandas as pd

from antares.craft import Study, XpansionCandidateUpdate, XpansionConstraintUpdate, read_study_local
from antares.craft.exceptions.exceptions import (
    BadCandidateFormatError,
    XpansionCandidateCoherenceError,
    XpansionCandidateDeletionError,
    XpansionCandidateEditionError,
    XpansionConstraintsDeletionError,
    XpansionConstraintsEditionError,
    XpansionFileDeletionError,
    XpansionMatrixReadingError,
)
from antares.craft.model.xpansion.candidate import XpansionCandidate, XpansionLinkProfile
from antares.craft.model.xpansion.constraint import ConstraintSign, XpansionConstraint
from antares.craft.model.xpansion.sensitivity import XpansionSensitivity
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
from antares.craft.tools.serde_local.ini_reader import IniReader


class TestXpansion:
    def _set_up(self, study: Study, resource: Path) -> XpansionConfiguration:
        study_path = Path(study.path)
        # Put a real case configuration inside the study and tests the reading method.
        with zipfile.ZipFile(resource, "r") as zf:
            zf.extractall(study_path / "user" / "expansion")
        # Read the study
        xpansion = read_study_local(study_path).xpansion
        assert isinstance(xpansion, XpansionConfiguration)
        return xpansion

    def test_create_and_read_basic_configuration(self, local_study_w_links: Study) -> None:
        # Asserts at first Xpansion is None.
        assert local_study_w_links.xpansion is None
        # Reading a study without an Xpansion configuration works. It returns None as an ` xpansion ` attribute.
        study_path = Path(local_study_w_links.path)
        study = read_study_local(study_path)
        assert study.xpansion is None

        # Create Xpansion configuration.
        xpansion = local_study_w_links.create_xpansion_configuration()
        assert isinstance(xpansion, XpansionConfiguration)
        assert xpansion.settings == XpansionSettings()
        assert xpansion.get_candidates() == {}
        assert xpansion.get_constraints() == {}
        assert xpansion.sensitivity is None

        # Asserts the reading works.
        study = read_study_local(study_path)
        xpansion_read = study.xpansion
        assert isinstance(xpansion_read, XpansionConfiguration)
        assert xpansion_read.settings == XpansionSettings()
        assert xpansion_read.get_candidates() == {}
        assert xpansion_read.get_constraints() == {}
        assert xpansion_read.sensitivity is None

        # Deletes the configuration.
        study.delete_xpansion_configuration()
        assert study.xpansion is None
        assert not (study_path / "user" / "expansion").exists()

    def test_fancy_configuration(self, local_study_w_links: Study, xpansion_input_path: Path) -> None:
        # Asserts at first Xpansion is None.
        assert local_study_w_links.xpansion is None
        # Set up
        xpansion = self._set_up(local_study_w_links, xpansion_input_path)
        # Checks
        assert xpansion.settings == XpansionSettings(
            optimality_gap=10000, batch_size=0, additional_constraints="contraintes.txt"
        )
        assert xpansion.get_candidates() == {
            "battery": XpansionCandidate(
                name="battery", area_from="Area2", area_to="flex", annual_cost_per_mw=60000, max_investment=1000
            ),
            "peak": XpansionCandidate(
                name="peak", area_from="area1", area_to="peak", annual_cost_per_mw=60000, unit_size=100, max_units=20
            ),
            "pv": XpansionCandidate(
                name="pv",
                area_from="area2",
                area_to="pv",
                annual_cost_per_mw=55400,
                max_investment=1000,
                direct_link_profile="direct_capa_pv.ini",
                indirect_link_profile="direct_capa_pv.ini",
            ),
            "semibase": XpansionCandidate(
                name="semibase",
                area_from="area1",
                area_to="semibase",
                annual_cost_per_mw=126000,
                unit_size=200,
                max_units=10,
            ),
            "transmission_line": XpansionCandidate(
                name="transmission_line",
                area_from="area1",
                area_to="area2",
                annual_cost_per_mw=10000,
                unit_size=400,
                max_units=8,
                direct_link_profile="direct_04_fr-05_fr.txt",
                indirect_link_profile="indirect_04_fr-05_fr.txt",
            ),
        }
        assert xpansion.get_constraints() == {
            "additional_c1": XpansionConstraint(
                name="additional_c1",
                sign=ConstraintSign.LESS_OR_EQUAL,
                right_hand_side=300,
                candidates_coefficients={"semibase": 1, "transmission_line": 1},
            )
        }
        assert xpansion.sensitivity == XpansionSensitivity(epsilon=10000, projection=["battery", "pv"], capex=True)

    def test_weight_matrices(self, local_study_w_links: Study, xpansion_input_path: Path) -> None:
        # Set up
        xpansion = self._set_up(local_study_w_links, xpansion_input_path)

        # Asserts we can get a content
        weight = xpansion.get_weight("weights.txt")
        assert weight.equals(pd.DataFrame([0.2, 0.4, 0.4]))

        # Asserts fetching a fake matrix raises an appropriate exception
        with pytest.raises(
            XpansionMatrixReadingError,
            match="Could not read the xpansion matrix fake_weight for study studyTest: The file does not exist",
        ):
            xpansion.get_weight("fake_weight")

        # Asserts we can modify and create a matrix
        new_weight_matrix = pd.DataFrame([0.1, 0.2, 0.7])
        for file_name in ["weights.txt", "other_weights.ini"]:
            xpansion.set_weight(file_name, new_weight_matrix)
            weight = xpansion.get_weight(file_name)
            assert weight.equals(new_weight_matrix)

        # Asserts there's no default matrix for weights
        empty_matrix = pd.DataFrame()
        xpansion.set_weight("weights.txt", empty_matrix)
        weight = xpansion.get_weight("weights.txt")
        assert weight.equals(empty_matrix)

        # Asserts we can delete a matrix
        study_path = Path(local_study_w_links.path)
        xpansion.delete_weight("weights.txt")
        assert not (study_path / "user" / "expansion" / "weights" / "weights.txt").exists()

        # Asserts deleting a fake matrix raises an appropriate exception
        with pytest.raises(
            XpansionFileDeletionError,
            match="Could not delete the xpansion file fake_weight for study studyTest: The file does not exist",
        ):
            xpansion.delete_weight("fake_weight")

    def test_capacities_matrices(self, local_study_w_links: Study, xpansion_input_path: Path) -> None:
        # Set up
        xpansion = self._set_up(local_study_w_links, xpansion_input_path)

        # Asserts we can get a content
        capacity = xpansion.get_capacity("direct_04_fr-05_fr.txt")
        expected_capacity = pd.DataFrame(np.full((8760, 1), 0.95))
        expected_capacity[2208:6576] = 1
        assert capacity.equals(expected_capacity)

        # Asserts fetching a fake matrix raises an appropriate exception
        with pytest.raises(
            XpansionMatrixReadingError,
            match="Could not read the xpansion matrix fake_capacity for study studyTest: The file does not exist",
        ):
            xpansion.get_capacity("fake_capacity")

        # Asserts we can modify and create a matrix
        new_capacity_matrix = pd.DataFrame(np.full((8760, 1), 0.87))
        for file_name in ["capa_pv.ini", "other_capa.txt"]:
            xpansion.set_capacity(file_name, new_capacity_matrix)
            capacity = xpansion.get_capacity(file_name)
            assert capacity.equals(new_capacity_matrix)

        # Asserts there's a default matrix for capacities
        empty_matrix = pd.DataFrame()
        xpansion.set_capacity("capa_pv.ini", empty_matrix)
        capacity = xpansion.get_capacity("capa_pv.ini")
        assert capacity.equals(pd.DataFrame(np.ones((8760, 1))))

        # Asserts we can delete a matrix
        study_path = Path(local_study_w_links.path)
        xpansion.delete_capacity("04_fr-05_fr.txt")
        assert not (study_path / "user" / "expansion" / "capa" / "04_fr-05_fr.txt").exists()

        # Asserts deleting a fake matrix raises an appropriate exception
        with pytest.raises(
            XpansionFileDeletionError,
            match="Could not delete the xpansion file fake_capacity for study studyTest: The file does not exist",
        ):
            xpansion.delete_capacity("fake_capacity")

    def test_candidates_error_cases(self, local_study_w_links: Study, xpansion_input_path: Path) -> None:
        # Set up
        xpansion = self._set_up(local_study_w_links, xpansion_input_path)

        # Asserts we cannot create a candidate without filling investment values
        with pytest.raises(
            BadCandidateFormatError,
            match=re.escape(
                "The candidate my_cdt is not well formatted. It should either contain max-investment or (max-units and unit-size)."
            ),
        ):
            my_cdt = XpansionCandidate(name="my_cdt", area_from="Area1", area_to="Area2", annual_cost_per_mw=3.17)
            xpansion.create_candidate(my_cdt)

        # Asserts we cannot create a candidate with fake links
        with pytest.raises(
            XpansionCandidateCoherenceError,
            match="The candidate my_cdt for study studyTest has incoherence: Link between Area1 and Area2 does not exist",
        ):
            my_cdt = XpansionCandidate(
                name="my_cdt", area_from="Area1", area_to="Area2", annual_cost_per_mw=3.17, max_investment=2
            )
            xpansion.create_candidate(my_cdt)

        # Asserts we cannot create a candidate with fake link-profiles
        with pytest.raises(
            XpansionCandidateCoherenceError,
            match="The candidate my_cdt for study studyTest has incoherence: File fake_profile does not exist",
        ):
            my_cdt = XpansionCandidate(
                name="my_cdt",
                area_from="fr",
                area_to="at",
                annual_cost_per_mw=3.17,
                max_investment=2,
                direct_link_profile="fake_profile",
            )
            xpansion.create_candidate(my_cdt)

        # Asserts we cannot update a fake candidate
        with pytest.raises(
            XpansionCandidateEditionError,
            match="Could not edit the candidate fake_candidate for study studyTest: Candidate does not exist",
        ):
            xpansion.update_candidate("fake_candidate", XpansionCandidateUpdate(name="new_name"))

        # Asserts we cannot remove a fake candidate
        with pytest.raises(
            XpansionCandidateDeletionError,
            match="Could not delete candidates {'fake_candidate'} for study studyTest: They do not exist",
        ):
            xpansion.delete_candidates(["fake_candidate"])

    def test_candidates(self, local_study: Study, xpansion_input_path: Path) -> None:
        # Set up
        xpansion = self._set_up(local_study, xpansion_input_path)
        areas_to_create = ["area1", "area2", "flex", "peak", "pv", "semibase"]
        links_to_create = [
            ("area1", "area2"),
            ("area2", "flex"),
            ("area1", "peak"),
            ("area2", "pv"),
            ("area1", "semibase"),
        ]
        for area in areas_to_create:
            local_study.create_area(area)
        for link in links_to_create:
            local_study.create_link(area_from=link[0], area_to=link[1])

        # Creates a candidate
        my_cdt = XpansionCandidate(
            name="my_cdt",
            area_from="area1",
            area_to="area2",
            annual_cost_per_mw=3.17,
            max_investment=2,
            direct_link_profile="capa_pv.ini",
        )
        cdt = xpansion.create_candidate(my_cdt)
        assert cdt == my_cdt

        # Update several properties
        new_properties = XpansionCandidateUpdate(area_from="pv", max_investment=3)
        cdt = xpansion.update_candidate("my_cdt", new_properties)
        assert cdt.name == "my_cdt"
        assert cdt.area_from == "area2"  # Areas were re-ordered by alphabetical name
        assert cdt.area_to == "pv"
        assert cdt.max_investment == 3
        assert cdt.direct_link_profile == "capa_pv.ini"

        # Rename it
        new_properties = XpansionCandidateUpdate(name="new_name")
        cdt = xpansion.update_candidate("my_cdt", new_properties)
        assert cdt.name == "new_name"
        assert cdt.max_investment == 3
        assert cdt.direct_link_profile == "capa_pv.ini"

        # Checks ini content
        ini_path = Path(local_study.path) / "user" / "expansion" / "candidates.ini"
        content = IniReader().read(ini_path)
        assert len(content) == 6
        my_candidate = content["6"]
        assert my_candidate == {
            "name": "new_name",
            "link": "area2 - pv",
            "annual-cost-per-mw": 3.17,
            "max-investment": 3.0,
            "direct-link-profile": "capa_pv.ini",
        }

        # Removes the direct link profile from the candidate
        xpansion.remove_links_profile_from_candidate("new_name", [XpansionLinkProfile.DIRECT_LINK])
        assert xpansion.get_candidates()["new_name"].direct_link_profile is None
        content = IniReader().read(ini_path)
        assert len(content) == 6
        my_candidate = content["6"]
        assert my_candidate == {
            "name": "new_name",
            "link": "area2 - pv",
            "annual-cost-per-mw": 3.17,
            "max-investment": 3.0,
        }

        # Removes several candidates
        xpansion.delete_candidates(["peak", "battery"])
        assert len(xpansion.get_candidates()) == 4
        content = IniReader().read(ini_path)
        assert len(content) == 4

    def test_constraints_error_cases(self, local_study_w_links: Study, xpansion_input_path: Path) -> None:
        # Set up
        xpansion = self._set_up(local_study_w_links, xpansion_input_path)

        # Deletes a fake file
        with pytest.raises(
            XpansionFileDeletionError,
            match="Could not delete the xpansion file fake_file for study studyTest: The file does not exist",
        ):
            xpansion.delete_constraints_file("fake_file")

        # Edits a fake constraint
        file_name = "contraintes.txt"
        with pytest.raises(
            XpansionConstraintsEditionError,
            match="Could not edit the xpansion constraint fake_constraint inside the file contraintes.txt for study studyTest: Constraint does not exist",
        ):
            new_constraint = XpansionConstraintUpdate(right_hand_side=0.4)
            xpansion.update_constraint("fake_constraint", new_constraint, file_name)

        # Deletes a fake constraint
        with pytest.raises(
            XpansionConstraintsDeletionError,
            match=re.escape(
                "Could not create the xpansion constraints ['fake_constraint'] inside the file contraintes.txt for study studyTest: Constraint does not exist",
            ),
        ):
            xpansion.delete_constraints(["fake_constraint"], file_name)

    def test_constraints(self, local_study_w_links: Study, xpansion_input_path: Path) -> None:
        # Set up
        xpansion = self._set_up(local_study_w_links, xpansion_input_path)

        # Checks current constraints
        assert xpansion.get_constraints() == {
            "additional_c1": XpansionConstraint(
                name="additional_c1",
                sign=ConstraintSign.LESS_OR_EQUAL,
                right_hand_side=300,
                candidates_coefficients={"semibase": 1, "transmission_line": 1},
            )
        }

        file_name = "contraintes.txt"

        # Creates a constraint
        new_constraint = XpansionConstraint(
            name="new_constraint",
            sign=ConstraintSign.GREATER_OR_EQUAL,
            right_hand_side=100,
            candidates_coefficients={"semibase": 0.5},
        )
        constraint = xpansion.create_constraint(new_constraint, file_name)
        assert constraint == new_constraint

        # Edits it
        new_properties = XpansionConstraintUpdate(right_hand_side=1000, candidates_coefficients={"test": 0.3})
        modified_constraint = xpansion.update_constraint("new_constraint", new_properties, file_name)
        assert modified_constraint == XpansionConstraint(
            name="new_constraint",
            sign=ConstraintSign.GREATER_OR_EQUAL,
            right_hand_side=1000,
            candidates_coefficients={"semibase": 0.5, "test": 0.3},
        )

        # Ensures the edition for candidates coefficients is working correctly
        new_properties = XpansionConstraintUpdate(
            sign=ConstraintSign.EQUAL, candidates_coefficients={"test": 0.2, "test2": 0.8}
        )
        modified_constraint = xpansion.update_constraint("new_constraint", new_properties, file_name)
        assert modified_constraint == XpansionConstraint(
            name="new_constraint",
            sign=ConstraintSign.EQUAL,
            right_hand_side=1000,
            candidates_coefficients={"semibase": 0.5, "test": 0.2, "test2": 0.8},
        )

        # Rename it
        new_properties = XpansionConstraintUpdate(name="new_name")
        modified_constraint = xpansion.update_constraint("new_constraint", new_properties, file_name)
        assert modified_constraint.name == "new_name"

        # Checks ini content
        ini_path = Path(local_study_w_links.path) / "user" / "expansion" / "constraints" / file_name
        content = IniReader().read(ini_path)
        assert len(content) == 2
        assert content["2"] == {
            "name": "new_name",
            "sign": "equal",
            "rhs": 1000.0,
            "semibase": 0.5,
            "test": 0.2,
            "test2": 0.8,
        }

        # Deletes it
        xpansion.delete_constraints(["new_name", "additional_c1"], file_name)
        assert xpansion.get_constraints() == {}
        content = IniReader().read(ini_path)
        assert content == {}

        # Create a constraint in a non-existing file
        constraint = XpansionConstraint(
            name="my_constraint", sign=ConstraintSign.GREATER_OR_EQUAL, right_hand_side=0.1, candidates_coefficients={}
        )
        xpansion.create_constraint(constraint, "new_file.ini")
        ini_path = ini_path.parent / "new_file.ini"
        assert ini_path.exists()

        # Deletes the file
        xpansion.delete_constraints_file("new_file.ini")
        assert not ini_path.exists()
