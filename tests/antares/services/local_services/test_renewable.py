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

import copy
import re

from pathlib import Path

import pandas as pd

from checksumdir import dirhash

from antares.craft import RenewableClusterGroup, Study, TimeSeriesInterpretation, read_study_local
from antares.craft.exceptions.exceptions import MatrixFormatError, RenewablePropertiesUpdateError
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties, RenewableClusterPropertiesUpdate
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter


class TestRenewable:
    def test_update_properties(self, tmp_path: Path, local_study_with_renewable: Study) -> None:
        # Checks values before update
        renewable = local_study_with_renewable.get_areas()["fr"].get_renewables()["renewable cluster"]
        assert renewable.properties == RenewableClusterProperties(enabled=False, unit_count=44)
        # Updates properties
        update_properties = RenewableClusterPropertiesUpdate(group=RenewableClusterGroup.WIND_ON_SHORE, enabled=True)
        new_properties = renewable.update_properties(update_properties)
        expected_properties = RenewableClusterProperties(
            enabled=True, unit_count=44, group=RenewableClusterGroup.WIND_ON_SHORE
        )
        assert new_properties == expected_properties
        assert renewable.properties == expected_properties

    def test_cluster_with_numeric_name(self, local_study_with_renewable: Study) -> None:
        # Given
        cluster_name = "123"

        # When
        created_thermal = local_study_with_renewable.get_areas()["fr"].create_renewable_cluster(cluster_name)
        assert isinstance(created_thermal, RenewableCluster)

        # Then this should not raise an exception
        local_study_with_renewable.get_areas()["fr"]._renewable_service.read_renewables()


    def test_matrices(self, tmp_path: Path, local_study_with_renewable: Study) -> None:
        # Checks all matrices exist
        renewable = local_study_with_renewable.get_areas()["fr"].get_renewables()["renewable cluster"]
        renewable.get_timeseries()

        # Replace matrix
        matrix = pd.DataFrame(data=8760 * [[3]])
        renewable.set_series(matrix)
        assert renewable.get_timeseries().equals(matrix)

        # Try to update with wrongly formatted matrix
        matrix = pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]])
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                "Wrong format for renewable/fr/renewable cluster/series matrix, expected shape is (8760, Any) and was : (2, 3)"
            ),
        ):
            renewable.set_series(matrix)

    def test_deletion(self, local_study_with_renewable: Study) -> None:
        area_fr = local_study_with_renewable.get_areas()["fr"]
        renewable = area_fr.get_renewables()["renewable cluster"]
        area_fr.delete_renewable_clusters([renewable])
        # Asserts the area dict is empty
        assert area_fr.get_renewables() == {}
        # Asserts the file is empty
        renewable_folder = Path(local_study_with_renewable.path) / "input" / "renewables"
        assert not (renewable_folder / "clusters" / "fr" / "list.ini").read_text()
        # Asserts the series matrix does not exist anymore
        assert not (renewable_folder / "series" / "fr" / "renewable cluster" / "series.txt").exists()

    def test_update_renewable_properties(self, local_study_with_renewable: Study) -> None:
        area_fr = local_study_with_renewable.get_areas()["fr"]
        renewable = area_fr.get_renewables()["renewable cluster"]
        update_for_renewable = RenewableClusterPropertiesUpdate(
            enabled=False, unit_count=13, ts_interpretation=TimeSeriesInterpretation.PRODUCTION_FACTOR
        )
        dict_renewable = {renewable: update_for_renewable}
        local_study_with_renewable.update_renewable_clusters(dict_renewable)

        # testing the modified value
        assert not renewable.properties.enabled
        assert renewable.properties.unit_count == 13
        assert renewable.properties.ts_interpretation == TimeSeriesInterpretation.PRODUCTION_FACTOR

        # testing the unmodified value
        assert renewable.properties.group == RenewableClusterGroup.OTHER1

    def test_update_several_properties_fails(self, local_study_with_renewable: Study) -> None:
        """
        Ensures the update fails as the area doesn't exist.
        We also want to ensure the study wasn't partially modified.
        """
        update_for_renewable = RenewableClusterPropertiesUpdate(enabled=False, unit_count=13)
        renewable = local_study_with_renewable.get_areas()["fr"].get_renewables()["renewable cluster"]
        fake_renewable = copy.deepcopy(renewable)
        fake_renewable._area_id = "fake"
        dict_renewable = {renewable: update_for_renewable, fake_renewable: update_for_renewable}
        renewable_folder = Path(local_study_with_renewable.path) / "input" / "renewables"
        hash_before_update = dirhash(renewable_folder, "md5")
        with pytest.raises(
            RenewablePropertiesUpdateError,
            match=re.escape(
                "Could not update properties for renewable cluster 'renewable cluster' inside area 'fake': The cluster does not exist"
            ),
        ):
            local_study_with_renewable.update_renewable_clusters(dict_renewable)
        hash_after_update = dirhash(renewable_folder, "md5")
        assert hash_before_update == hash_after_update

    def test_read_renewable_group_with_weird_case(self, local_study_with_renewable: Study) -> None:
        """Asserts we're able to read a group written in a weird case"""
        study_path = Path(local_study_with_renewable.path)
        ini_path = study_path / "input" / "renewables" / "clusters" / "fr" / "list.ini"
        ini_content = IniReader().read(ini_path)
        ini_content["renewable cluster"]["group"] = "SolaR THERMAl"
        IniWriter().write(ini_content, ini_path)
        # Ensure we're able to read the study
        study = read_study_local(study_path)
        thermal = study.get_areas()["fr"].get_renewables()["renewable cluster"]
        # Ensure we consider the group as THERMAL SOLAR
        assert thermal.properties.group == RenewableClusterGroup.THERMAL_SOLAR
