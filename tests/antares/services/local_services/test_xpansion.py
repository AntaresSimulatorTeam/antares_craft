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

import zipfile

from pathlib import Path

import numpy as np
import pandas as pd

from antares.craft import Study, read_study_local
from antares.craft.exceptions.exceptions import XpansionMatrixDeletionError, XpansionMatrixReadingError
from antares.craft.model.xpansion.candidate import XpansionCandidate
from antares.craft.model.xpansion.constraint import ConstraintSign, XpansionConstraint
from antares.craft.model.xpansion.sensitivity import XpansionSensitivity
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration


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
            XpansionMatrixDeletionError,
            match="Could not delete the xpansion matrix fake_weight for study studyTest: The file does not exist",
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
            XpansionMatrixDeletionError,
            match="Could not delete the xpansion matrix fake_capacity for study studyTest: The file does not exist",
        ):
            xpansion.delete_capacity("fake_capacity")
