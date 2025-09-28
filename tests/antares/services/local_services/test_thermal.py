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

import numpy as np
import pandas as pd

from checksumdir import dirhash

from antares.craft import ClusterData, ConstraintTerm, Study
from antares.craft.exceptions.exceptions import (
    MatrixFormatError,
    ReferencedObjectDeletionNotAllowed,
    ThermalCreationError,
    ThermalDeletionError,
    ThermalPropertiesUpdateError,
)
from antares.craft.model.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalCluster,
    ThermalClusterGroup,
    ThermalClusterProperties,
    ThermalClusterPropertiesUpdate,
    ThermalCostGeneration,
)
from antares.craft.service.local_services.factory import read_study_local
from antares.craft.service.local_services.models.thermal import ThermalClusterPropertiesLocal
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter


class TestThermalCluster:
    def test_can_be_created(self, local_study_w_areas: Study) -> None:
        # Given
        thermal_name = "test_thermal_cluster"

        # When
        created_thermal = local_study_w_areas.get_areas()["fr"].create_thermal_cluster(thermal_name)
        assert isinstance(created_thermal, ThermalCluster)

    def test_cluster_with_numeric_name(self, local_study_w_areas: Study) -> None:
        # Given
        thermal_name = "123"

        # When
        created_thermal = local_study_w_areas.get_areas()["fr"].create_thermal_cluster(thermal_name)
        assert isinstance(created_thermal, ThermalCluster)

        # Then this should not raise an exception
        local_study_w_areas.get_areas()["fr"]._thermal_service.read_thermal_clusters()

    def test_duplicate_name_errors(self, local_study_w_thermal: Study) -> None:
        # Given
        area_name = "fr"
        thermal_name = "test thermal cluster"

        # Then
        with pytest.raises(
            ThermalCreationError,
            match=f"Could not create the thermal cluster '{thermal_name}' inside area '{area_name}': A thermal cluster called '{thermal_name}' already exists in area '{area_name}'.",
        ):
            local_study_w_thermal.get_areas()[area_name].create_thermal_cluster(thermal_name)

    def test_has_correct_default_properties(self, local_study_w_thermal: Study) -> None:
        thermal_cluster = local_study_w_thermal.get_areas()["fr"].get_thermals()["test thermal cluster"]
        assert thermal_cluster.properties == ThermalClusterProperties(group=ThermalClusterGroup.NUCLEAR, must_run=True)

    def test_required_ini_files_exist(self, tmp_path: Path, local_study_w_thermal: Study) -> None:
        study_path = Path(local_study_w_thermal.path)
        assert (study_path / "input" / "thermal" / "clusters" / "fr" / "list.ini").exists()
        assert (study_path / "input" / "thermal" / "areas.ini").exists()

    def test_list_ini_has_default_properties(self, tmp_path: Path, local_study_w_thermal: Study) -> None:
        # Given
        expected_list_ini_contents = """[test thermal cluster]
name = test thermal cluster
enabled = True
unitcount = 1
nominalcapacity = 0.0
group = nuclear
gen-ts = use global
min-stable-power = 0.0
min-up-time = 1
min-down-time = 1
must-run = True
spinning = 0.0
volatility.forced = 0.0
volatility.planned = 0.0
law.forced = uniform
law.planned = uniform
marginal-cost = 0.0
spread-cost = 0.0
fixed-cost = 0.0
startup-cost = 0.0
market-bid-cost = 0.0
co2 = 0.0
nh3 = 0.0
so2 = 0.0
nox = 0.0
pm2_5 = 0.0
pm5 = 0.0
pm10 = 0.0
nmvoc = 0.0
op1 = 0.0
op2 = 0.0
op3 = 0.0
op4 = 0.0
op5 = 0.0
costgeneration = SetManually
efficiency = 100.0
variableomcost = 0.0

"""
        study_path = Path(local_study_w_thermal.path)
        assert (
            study_path / "input" / "thermal" / "clusters" / "fr" / "list.ini"
        ).read_text() == expected_list_ini_contents

    def test_list_ini_has_custom_properties(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # Given
        expected_list_ini_contents = """[test thermal cluster]
name = test thermal cluster
enabled = False
unitcount = 12
nominalcapacity = 3.9
group = nuclear
gen-ts = force no generation
min-stable-power = 3.1
min-up-time = 3
min-down-time = 2
must-run = True
spinning = 2.3
volatility.forced = 3.5
volatility.planned = 3.7
law.forced = geometric
law.planned = geometric
marginal-cost = 2.9
spread-cost = 4.2
fixed-cost = 3.6
startup-cost = 0.7
market-bid-cost = 0.8
co2 = 1.0
nh3 = 2.0
so2 = 3.0
nox = 4.0
pm2_5 = 5.0
pm5 = 6.0
pm10 = 7.0
nmvoc = 8.0
op1 = 9.0
op2 = 10.0
op3 = 11.0
op4 = 12.0
op5 = 13.0
costgeneration = useCostTimeseries
efficiency = 123.4
variableomcost = 5.0

"""
        thermal_cluster_properties = ThermalClusterProperties(
            group=ThermalClusterGroup.NUCLEAR,
            enabled=False,
            unit_count=12,
            nominal_capacity=3.9,
            gen_ts=LocalTSGenerationBehavior.FORCE_NO_GENERATION,
            min_stable_power=3.1,
            min_up_time=3,
            min_down_time=2,
            must_run=True,
            spinning=2.3,
            volatility_forced=3.5,
            volatility_planned=3.7,
            law_forced=LawOption.GEOMETRIC,
            law_planned=LawOption.GEOMETRIC,
            marginal_cost=2.9,
            spread_cost=4.2,
            fixed_cost=3.6,
            startup_cost=0.7,
            market_bid_cost=0.8,
            co2=1.0,
            nh3=2.0,
            so2=3.0,
            nox=4.0,
            pm2_5=5.0,
            pm5=6.0,
            pm10=7.0,
            nmvoc=8.0,
            op1=9.0,
            op2=10.0,
            op3=11.0,
            op4=12.0,
            op5=13.0,
            cost_generation=ThermalCostGeneration.USE_COST_TIME_SERIES,
            efficiency=123.4,
            variable_o_m_cost=5.0,
        )

        # When
        local_study_w_areas.get_areas()["fr"].create_thermal_cluster("test thermal cluster", thermal_cluster_properties)
        study_path = Path(local_study_w_areas.path)
        ini_content = (study_path / "input" / "thermal" / "clusters" / "fr" / "list.ini").read_text()
        assert ini_content == expected_list_ini_contents

    def test_list_ini_has_multiple_clusters(self, local_study_w_thermal: Study) -> None:
        # Asserts we can create 2 clusters
        local_study_w_thermal.get_areas()["fr"].create_thermal_cluster("test thermal cluster two")
        study_path = Path(local_study_w_thermal.path)
        ini_content = IniReader().read(study_path / "input" / "thermal" / "clusters" / "fr" / "list.ini")

        assert len(ini_content.keys()) == 2
        expected_sections = ["test thermal cluster", "test thermal cluster two"]
        for key in expected_sections:
            assert key in ini_content
            ini_content[key].pop("name")
            created_properties = ThermalClusterPropertiesLocal(**ini_content[key]).to_user_model()
            if key == "test thermal cluster":
                assert created_properties == ThermalClusterProperties(group=ThermalClusterGroup.NUCLEAR, must_run=True)
            else:
                assert created_properties == ThermalClusterProperties()

    def test_create_thermal_initialization_files(self, local_study_w_areas: Study) -> None:
        study_path = Path(local_study_w_areas.path)
        areas = local_study_w_areas.get_areas()
        cluster_id = "cluster_test"
        for area_id, area in areas.items():
            area.create_thermal_cluster(cluster_id)

        for area_id in areas.keys():
            expected_paths = [
                study_path / f"input/thermal/prepro/{area_id}/{cluster_id}/modulation.txt",
                study_path / f"input/thermal/prepro/{area_id}/{cluster_id}/data.txt",
                study_path / f"input/thermal/series/{area_id}/{cluster_id}/series.txt",
            ]

            for expected_path in expected_paths:
                assert expected_path.is_file(), f"File not created: {expected_path}"

    def test_update_properties(self, local_study_w_thermal: Study) -> None:
        # Checks values before update
        thermal = local_study_w_thermal.get_areas()["fr"].get_thermals()["test thermal cluster"]
        current_properties = ThermalClusterProperties(
            must_run=True, group=ThermalClusterGroup.NUCLEAR, law_forced=LawOption.UNIFORM, startup_cost=0
        )
        assert thermal.properties == current_properties
        # Updates properties
        update_properties = ThermalClusterPropertiesUpdate(
            spinning=0.1, startup_cost=1.2, law_forced=LawOption.GEOMETRIC
        )
        new_properties = thermal.update_properties(update_properties)
        expected_properties = ThermalClusterProperties(
            must_run=True,
            group=ThermalClusterGroup.NUCLEAR,
            spinning=0.1,
            startup_cost=1.2,
            law_forced=LawOption.GEOMETRIC,
        )
        assert new_properties == expected_properties
        assert thermal.properties == expected_properties
        # Asserts the ini file is properly modified
        study_path = Path(local_study_w_thermal.path)
        ini_content = IniReader().read(study_path / "input" / "thermal" / "clusters" / "fr" / "list.ini")
        assert ini_content == {
            "test thermal cluster": {
                "name": "test thermal cluster",
                "enabled": True,
                "unitcount": 1,
                "nominalcapacity": 0.0,
                "group": "nuclear",
                "gen-ts": "use global",
                "min-stable-power": 0.0,
                "min-up-time": 1,
                "min-down-time": 1,
                "must-run": True,
                "spinning": 0.1,
                "volatility.forced": 0.0,
                "volatility.planned": 0.0,
                "law.forced": "geometric",
                "law.planned": "uniform",
                "marginal-cost": 0.0,
                "spread-cost": 0.0,
                "fixed-cost": 0.0,
                "startup-cost": 1.2,
                "market-bid-cost": 0.0,
                "co2": 0.0,
                "nh3": 0.0,
                "so2": 0.0,
                "nox": 0.0,
                "pm2_5": 0.0,
                "pm5": 0.0,
                "pm10": 0.0,
                "nmvoc": 0.0,
                "op1": 0.0,
                "op2": 0.0,
                "op3": 0.0,
                "op4": 0.0,
                "op5": 0.0,
                "costgeneration": "SetManually",
                "efficiency": 100.0,
                "variableomcost": 0.0,
            }
        }

    def test_update_matrices(self, local_study_w_thermal: Study) -> None:
        # Checks all matrices exist
        thermal = local_study_w_thermal.get_areas()["fr"].get_thermals()["test thermal cluster"]
        thermal.get_series_matrix()
        thermal.get_fuel_cost_matrix()
        thermal.get_co2_cost_matrix()
        thermal.get_prepro_data_matrix()
        thermal.get_prepro_modulation_matrix()

        # Replace matrices
        data_matrix = pd.DataFrame(data=np.ones((365, 6)))
        thermal.set_prepro_data(data_matrix)
        assert thermal.get_prepro_data_matrix().equals(data_matrix)

        modulation_matrix = pd.DataFrame(data=np.ones((8760, 4)))
        thermal.set_prepro_modulation(modulation_matrix)
        assert thermal.get_prepro_modulation_matrix().equals(modulation_matrix)

        series_matrix = pd.DataFrame(data=8760 * [[3]])
        thermal.set_series(series_matrix)
        assert thermal.get_series_matrix().equals(series_matrix)

        thermal.set_fuel_cost(series_matrix)
        assert thermal.get_fuel_cost_matrix().equals(series_matrix)

        thermal.set_co2_cost(series_matrix)
        assert thermal.get_co2_cost_matrix().equals(series_matrix)

        # Try to update with wrongly formatted matrix
        matrix = pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]])
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                "Wrong format for thermal/fr/test thermal cluster/series matrix, expected shape is (8760, Any) and was : (2, 3)"
            ),
        ):
            thermal.set_series(matrix)

    def test_deletion(self, local_study_w_thermal: Study) -> None:
        # Creates 3 cluster to test all cases
        area_fr = local_study_w_thermal.get_areas()["fr"]
        thermal_1 = area_fr.get_thermals()["test thermal cluster"]
        thermal_2 = area_fr.create_thermal_cluster("th_2")
        thermal_3 = area_fr.create_thermal_cluster("th_3")

        # Deletes one cluster
        area_fr.delete_thermal_cluster(thermal_1)
        assert list(area_fr.get_thermals().keys()) == ["th_2", "th_3"]
        # Checks ini content
        study_path = Path(local_study_w_thermal.path)
        ini_content = IniReader().read(study_path / "input" / "thermal" / "clusters" / "fr" / "list.ini")
        assert list(ini_content.keys()) == ["th_2", "th_3"]
        # Asserts the series do not exist anymore
        assert not (study_path / "input" / "thermal" / "series" / "fr" / "test thermal cluster").exists()

        # Deletes the remaining clusters
        area_fr.delete_thermal_clusters([thermal_2, thermal_3])
        # Asserts the area dict is empty
        assert area_fr.get_thermals() == {}
        # Asserts the file is empty
        ini_path = Path(local_study_w_thermal.path / "input" / "thermal" / "clusters" / "fr" / "list.ini")
        assert not ini_path.read_text()

        with pytest.raises(
            ThermalDeletionError,
            match=re.escape(
                "Could not delete the following thermal clusters: 'test thermal cluster' inside area 'fr': it doesn't exist"
            ),
        ):
            area_fr.delete_thermal_cluster(thermal_1)

    def test_update_thermal_properties(self, local_study_w_thermals: Study) -> None:
        area_fr = local_study_w_thermals.get_areas()["fr"]
        thermal = area_fr.get_thermals()["test thermal cluster"]
        update_for_thermal = ThermalClusterPropertiesUpdate(enabled=False, unit_count=13)
        dict_thermal = {thermal: update_for_thermal}
        local_study_w_thermals.update_thermal_clusters(dict_thermal)

        # testing the modified value
        assert not thermal.properties.enabled
        assert thermal.properties.unit_count == 13

        # testing the unmodified value
        assert thermal.properties.group == ThermalClusterGroup.NUCLEAR

    def test_update_several_properties_fails(self, local_study_w_thermals: Study) -> None:
        """
        Ensures the update fails as the area doesn't exist.
        We also want to ensure the study wasn't partially modified.
        """
        update_for_thermal = ThermalClusterPropertiesUpdate(enabled=False, unit_count=13)
        thermal = local_study_w_thermals.get_areas()["fr"].get_thermals()["test thermal cluster"]
        fake_thermal = copy.deepcopy(thermal)
        fake_thermal._area_id = "fake"
        dict_thermal = {thermal: update_for_thermal, fake_thermal: update_for_thermal}
        thermal_folder = Path(local_study_w_thermals.path) / "input" / "thermal"
        hash_before_update = dirhash(thermal_folder, "md5")
        with pytest.raises(
            ThermalPropertiesUpdateError,
            match=re.escape(
                "Could not update properties for thermal cluster 'test thermal cluster' inside area 'fake': The cluster does not exist"
            ),
        ):
            local_study_w_thermals.update_thermal_clusters(dict_thermal)
        hash_after_update = dirhash(thermal_folder, "md5")
        assert hash_before_update == hash_after_update

    def test_read_legacy_groups(self, local_study_w_thermal: Study) -> None:
        """The group OTHER exists and is considered the same as OTHER1, so we have to be able to parse it"""
        study_path = Path(local_study_w_thermal.path)
        ini_path = study_path / "input" / "thermal" / "clusters" / "fr" / "list.ini"
        ini_content = IniReader().read(ini_path)
        ini_content["test thermal cluster"]["group"] = "othER"
        IniWriter().write(ini_content, ini_path)
        # Ensure we're able to read the study
        study = read_study_local(study_path)
        thermal = study.get_areas()["fr"].get_thermals()["test thermal cluster"]
        # Ensure we consider the group as OTHER1
        assert thermal.properties.group == ThermalClusterGroup.OTHER1

    def test_delete_referenced_cluster(self, local_study_w_thermal: Study) -> None:
        area_fr = local_study_w_thermal.get_areas()["fr"]

        # Create a constraint referencing the cluster
        cluster_data = ClusterData(area=area_fr.id, cluster="test thermal cluster")
        cluster_term = ConstraintTerm(data=cluster_data, weight=4.5, offset=3)
        local_study_w_thermal.create_binding_constraint(name="bc 1", terms=[cluster_term])

        # Ensures the area deletion fails
        with pytest.raises(
            ReferencedObjectDeletionNotAllowed,
            match="Area 'fr' is not allowed to be deleted, because it is referenced in the following binding constraints:\n1- 'bc 1'",
        ):
            local_study_w_thermal.delete_area(area_fr)

        # Ensures the cluster deletion fails
        with pytest.raises(
            ReferencedObjectDeletionNotAllowed,
            match="Thermal cluster 'test thermal cluster' is not allowed to be deleted, because it is referenced in the following binding constraints:\n1- 'bc 1'",
        ):
            area_fr.delete_thermal_cluster(area_fr.get_thermals()["test thermal cluster"])
