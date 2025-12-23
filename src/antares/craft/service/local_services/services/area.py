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
import contextlib
import copy
import os
import shutil

from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import numpy as np
import pandas as pd

from typing_extensions import override

from antares.craft import ClusterData
from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import (
    AreaCreationError,
    ReferencedObjectDeletionNotAllowed,
    ThermalCreationError,
)
from antares.craft.model.area import (
    Area,
    AreaProperties,
    AreaPropertiesUpdate,
    AreaUi,
    AreaUiUpdate,
)
from antares.craft.model.commons import STUDY_VERSION_9_2
from antares.craft.model.hydro import Hydro, HydroAllocation, HydroProperties, InflowStructure
from antares.craft.model.link import Link
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.craft.model.st_storage import STStorage, STStorageProperties
from antares.craft.model.thermal import ThermalCluster, ThermalClusterProperties
from antares.craft.service.base_services import (
    BaseAreaService,
    BaseBindingConstraintService,
    BaseHydroService,
    BaseRenewableService,
    BaseShortTermStorageService,
    BaseThermalService,
)
from antares.craft.service.local_services.models.area import AreaPropertiesLocal, AreaUiLocal
from antares.craft.service.local_services.models.hydro import HydroInflowStructureLocal, parse_hydro_properties_local
from antares.craft.service.local_services.models.renewable import (
    parse_renewable_cluster_local,
    serialize_renewable_cluster_local,
)
from antares.craft.service.local_services.models.st_storage import (
    parse_st_storage_local,
    serialize_st_storage_local,
)
from antares.craft.service.local_services.models.thermal import (
    parse_thermal_cluster_local,
    serialize_thermal_cluster_local,
)
from antares.craft.service.local_services.services.binding_constraint import BindingConstraintLocalService
from antares.craft.service.local_services.services.hydro import HydroLocalService
from antares.craft.service.local_services.services.link import LinkLocalService
from antares.craft.service.local_services.services.renewable import RenewableLocalService
from antares.craft.service.local_services.services.st_storage import ShortTermStorageLocalService
from antares.craft.service.local_services.services.thermal import ThermalLocalService
from antares.craft.service.local_services.services.utils import (
    remove_object_from_scenario_builder,
)
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.prepro_folder import PreproFolder
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from antares.study.version import StudyVersion


class AreaLocalService(BaseAreaService):
    def __init__(
        self,
        config: LocalConfiguration,
        study_name: str,
        study_version: StudyVersion,
        storage_service: BaseShortTermStorageService,
        thermal_service: BaseThermalService,
        renewable_service: BaseRenewableService,
        hydro_service: BaseHydroService,
        binding_constraint_service: BaseBindingConstraintService,
        link_service: LinkLocalService,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name
        self.study_version = study_version
        self._storage_service: BaseShortTermStorageService = storage_service
        self._thermal_service: BaseThermalService = thermal_service
        self._renewable_service: BaseRenewableService = renewable_service
        self._hydro_service: BaseHydroService = hydro_service
        self._binding_constraint_service: BaseBindingConstraintService = binding_constraint_service
        self._link_service = link_service

    def read_adequacy_ini(self, area_id: str) -> dict[str, Any]:
        return IniReader().read(self.config.study_path / "input" / "areas" / area_id / "adequacy_patch.ini")

    def _save_adequacy_ini(self, content: dict[str, Any], area_id: str) -> None:
        IniWriter().write(content, self.config.study_path / "input" / "areas" / area_id / "adequacy_patch.ini")

    def read_optimization_ini(self, area_id: str) -> dict[str, Any]:
        return IniReader().read(self.config.study_path / "input" / "areas" / area_id / "optimization.ini")

    def _save_optimization_ini(self, content: dict[str, Any], area_id: str) -> None:
        IniWriter().write(content, self.config.study_path / "input" / "areas" / area_id / "optimization.ini")

    def read_ui_ini(self, area_id: str) -> dict[str, Any]:
        return IniReader().read(self.config.study_path / "input" / "areas" / area_id / "ui.ini")

    def _save_ui_ini(self, content: dict[str, Any], area_id: str) -> None:
        IniWriter().write(content, self.config.study_path / "input" / "areas" / area_id / "ui.ini")

    def _get_thermal_areas_ini_path(self) -> Path:
        return self.config.study_path / "input" / "thermal" / "areas.ini"

    def read_thermal_areas_ini(self) -> dict[str, Any]:
        return IniReader().read(self._get_thermal_areas_ini_path())

    def _save_thermal_areas_ini(self, content: dict[str, Any]) -> None:
        IniWriter().write(content, self._get_thermal_areas_ini_path())

    @override
    def create_thermal_cluster(
        self, area_id: str, thermal_name: str, properties: Optional[ThermalClusterProperties] = None
    ) -> ThermalCluster:
        local_thermal_service = cast(ThermalLocalService, self.thermal_service)
        thermal_list_content = local_thermal_service.read_ini(area_id)

        # Checks for duplication
        thermal_id = transform_name_to_id(thermal_name)
        existing_ids = {transform_name_to_id(key) for key in thermal_list_content}
        if thermal_id in existing_ids:
            raise ThermalCreationError(
                thermal_name,
                area_id,
                f"A thermal cluster called '{thermal_name}' already exists in area '{area_id}'.",
            )

        # Writing properties
        content = serialize_thermal_cluster_local(self.study_version, properties or ThermalClusterProperties())
        thermal_list_content[thermal_name] = {"name": thermal_name, **content}
        local_thermal_service.save_ini(thermal_list_content, area_id)

        # Upload matrices
        cluster_id = transform_name_to_id(thermal_name)

        # Use default matrices for prepro and modulation as in AntaresWeb.
        # We do so because the default Simulator matrices don't make sense
        default_data_matrix = np.zeros((365, 6), dtype=np.float64)
        default_data_matrix[:, :2] = 1
        prepro = pd.DataFrame(default_data_matrix)
        default_modulation_matrix = np.ones((8760, 4), dtype=np.float64)
        default_modulation_matrix[:, 3] = 0
        modulation = pd.DataFrame(default_modulation_matrix)

        write_timeseries(self.config.study_path, prepro, TimeSeriesFileType.THERMAL_DATA, area_id, cluster_id)
        write_timeseries(self.config.study_path, modulation, TimeSeriesFileType.THERMAL_MODULATION, area_id, cluster_id)
        write_timeseries(self.config.study_path, None, TimeSeriesFileType.THERMAL_SERIES, area_id, cluster_id)

        # Round trip around properties for the groups.
        final_props = parse_thermal_cluster_local(self.study_version, content)
        return ThermalCluster(self.thermal_service, area_id, thermal_name, final_props)

    @override
    @property
    def thermal_service(self) -> "BaseThermalService":
        return self._thermal_service

    @override
    @property
    def renewable_service(self) -> "BaseRenewableService":
        return self._renewable_service

    @override
    @property
    def storage_service(self) -> "BaseShortTermStorageService":
        return self._storage_service

    @override
    @property
    def hydro_service(self) -> "BaseHydroService":
        return self._hydro_service

    @override
    def create_renewable_cluster(
        self, area_id: str, renewable_name: str, properties: Optional[RenewableClusterProperties] = None
    ) -> RenewableCluster:
        local_renewable_service = cast(RenewableLocalService, self.renewable_service)
        local_renewable_service.read_ini(area_id)
        ini_content = local_renewable_service.read_ini(area_id)
        content = serialize_renewable_cluster_local(self.study_version, properties or RenewableClusterProperties())
        ini_content[renewable_name] = {"name": renewable_name, **content}
        local_renewable_service.save_ini(ini_content, area_id)

        write_timeseries(
            self.config.study_path,
            None,
            TimeSeriesFileType.RENEWABLE_SERIES,
            area_id,
            cluster_id=transform_name_to_id(renewable_name),
        )

        # Round trip around properties for the groups.
        final_props = parse_renewable_cluster_local(self.study_version, content)
        return RenewableCluster(self.renewable_service, area_id, renewable_name, final_props)

    @override
    def set_load(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.LOAD, area_id)
        PreproFolder.LOAD.save(self.config.study_path, area_id)

    @override
    def create_st_storage(
        self, area_id: str, st_storage_name: str, properties: Optional[STStorageProperties] = None
    ) -> STStorage:
        properties = properties or STStorageProperties()
        local_properties = serialize_st_storage_local(self.study_version, properties)
        user_properties = parse_st_storage_local(self.study_version, local_properties)

        local_storage_service = cast(ShortTermStorageLocalService, self.storage_service)
        ini_content = local_storage_service.read_ini(area_id)

        ini_content[st_storage_name] = {
            "name": st_storage_name,
            **local_properties,
        }

        local_storage_service.save_ini(ini_content, area_id)

        storage = STStorage(
            self.storage_service,
            area_id,
            st_storage_name,
            user_properties,
        )

        # Create matrices
        cluster_id = storage.id
        empty_matrix = pd.DataFrame()
        # fmt: off
        write_timeseries(self.config.study_path, empty_matrix, TimeSeriesFileType.ST_STORAGE_PMAX_INJECTION, area_id, cluster_id=cluster_id)
        write_timeseries(self.config.study_path, empty_matrix, TimeSeriesFileType.ST_STORAGE_PMAX_WITHDRAWAL, area_id, cluster_id=cluster_id)
        write_timeseries(self.config.study_path, empty_matrix, TimeSeriesFileType.ST_STORAGE_INFLOWS, area_id, cluster_id=cluster_id)
        write_timeseries(self.config.study_path, empty_matrix, TimeSeriesFileType.ST_STORAGE_LOWER_RULE_CURVE, area_id, cluster_id=cluster_id)
        write_timeseries(self.config.study_path, empty_matrix, TimeSeriesFileType.ST_STORAGE_UPPER_RULE_CURVE, area_id, cluster_id=cluster_id)
        # fmt: on

        return storage

    @override
    def set_wind(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.WIND, area_id)
        PreproFolder.WIND.save(self.config.study_path, area_id)

    @override
    def set_reserves(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.RESERVES, area_id)

    @override
    def set_solar(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.SOLAR, area_id)
        PreproFolder.SOLAR.save(self.config.study_path, area_id)

    @override
    def set_misc_gen(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.MISC_GEN, area_id)

    @override
    def create_area(
        self, area_name: str, properties: Optional[AreaProperties] = None, ui: Optional[AreaUi] = None
    ) -> Area:
        """
        Args:
            area_name: area to be added to study
            properties: area's properties. If not provided, default values will be used.
            ui: area's ui characteristics. If not provided, default values will be used.

        Returns: area name if success or Error if area can not be
        created
        """

        study_path = self.config.study_path
        areas_directory = study_path / "input" / "areas"
        area_id = transform_name_to_id(area_name)
        new_area_directory = areas_directory / area_id

        if new_area_directory.is_dir():
            raise AreaCreationError(
                area_name, f"There is already an area '{area_name}' in the study '{self.study_name}'"
            )

        # Create "areas" directory if it doesn't exist
        new_area_directory.mkdir(parents=True)

        list_path = areas_directory.joinpath("list.txt")

        area_to_add = f"{area_name}\n"
        try:
            if os.path.isfile(list_path):
                with open(list_path, "r") as list_file:
                    list_file_content = list_file.read()
                updated_list = sorted(list_file_content.splitlines(keepends=True) + [area_to_add])
            else:
                updated_list = [area_to_add]

            # Write area(s) to file list.txt
            with open(list_path, "w") as list_txt:
                list_txt.write("".join(map(str, updated_list)))

            # TODO: Handle districts in sets.ini later
            sets_ini_path = study_path / "input" / "areas" / "sets.ini"
            if not sets_ini_path.exists():
                sets_ini_content = {
                    "all areas": {
                        "caption": "All areas",
                        "comments": "Spatial aggregates on all areas",
                        "output": "false",
                        "apply-filter": "add-all",
                    }
                }
                IniWriter().write(sets_ini_content, study_path / "input" / "areas" / "sets.ini")

            properties = properties or AreaProperties()
            local_properties = AreaPropertiesLocal.from_user_model(properties)

            adequacy_patch_ini = self.read_adequacy_ini(area_id)
            adequacy_patch_ini.update(local_properties.to_adequacy_ini())
            self._save_adequacy_ini(adequacy_patch_ini, area_id)

            self._save_optimization_ini(local_properties.to_optimization_ini(), area_id)

            self._get_thermal_areas_ini_path().touch(exist_ok=True)
            areas_ini = self.read_thermal_areas_ini()
            areas_ini.setdefault("unserverdenergycost", {})[area_id] = str(local_properties.energy_cost_unsupplied)
            areas_ini.setdefault("spilledenergycost", {})[area_id] = str(local_properties.energy_cost_spilled)
            self._save_thermal_areas_ini(areas_ini)

            ui = ui or AreaUi()
            local_ui = AreaUiLocal.from_user_model(ui)
            local_ui_content = local_ui.model_dump(mode="json", by_alias=True)
            self._save_ui_ini(local_ui_content, area_id)

            empty_df = pd.DataFrame()
            self.set_reserves(area_id, empty_df)
            self.set_misc_gen(area_id, empty_df)
            self.set_load(area_id, empty_df)
            self.set_solar(area_id, empty_df)
            self.set_wind(area_id, empty_df)

            # Links
            link_path = study_path / "input" / "links" / area_id
            (link_path / "capacities").mkdir(parents=True)
            (link_path / "properties.ini").touch()

            # Clusters
            for cluster_type in ["thermal", "renewables", "st-storage"]:
                ini_path = self.config.study_path / "input" / cluster_type / "clusters" / area_id / "list.ini"
                IniWriter().write({}, ini_path)

            # Hydro
            default_hydro_properties = HydroProperties()
            update_properties = default_hydro_properties.to_update_properties()
            hydro_local_service = cast(HydroLocalService, self.hydro_service)
            hydro_local_service.edit_hydro_properties(area_id, update_properties, creation=True)
            # Use parsing method to fill default values according to version
            hydro_properties = parse_hydro_properties_local(self.study_version, {})
            hydro_allocation = [HydroAllocation(area_id=area_id)]
            hydro = Hydro(self.hydro_service, area_id, hydro_properties, InflowStructure(), hydro_allocation)
            # Create files
            hydro_local_service.save_inflow_ini(
                HydroInflowStructureLocal.from_user_model(InflowStructure()).model_dump(by_alias=True), area_id
            )
            allocation_data = {item.area_id: float(item.coefficient) for item in hydro_allocation}
            hydro_local_service.save_allocation_ini({"[allocation]": allocation_data}, area_id)

            for ts in [
                TimeSeriesFileType.HYDRO_MAX_POWER,
                TimeSeriesFileType.HYDRO_RESERVOIR,
                TimeSeriesFileType.HYDRO_INFLOW_PATTERN,
                TimeSeriesFileType.HYDRO_CREDITS_MODULATION,
                TimeSeriesFileType.HYDRO_WATER_VALUES,
                TimeSeriesFileType.HYDRO_ROR,
                TimeSeriesFileType.HYDRO_MOD,
                TimeSeriesFileType.HYDRO_MINGEN,
                TimeSeriesFileType.HYDRO_ENERGY,
            ]:
                write_timeseries(study_path, pd.DataFrame(), ts, area_id=area_id)

        except Exception as e:
            raise AreaCreationError(area_name, f"{e}") from e

        created_area = Area(
            name=area_name,
            area_service=self,
            storage_service=self.storage_service,
            thermal_service=self.thermal_service,
            renewable_service=self.renewable_service,
            hydro_service=self.hydro_service,
            hydro=hydro,
            properties=local_properties.to_user_model(),  # round-trip to do the validation inside Pydantic
            ui=local_ui.to_user_model(),
        )
        return created_area

    def update_area_properties(self, area: Area, properties: AreaPropertiesUpdate) -> AreaProperties:
        area_id = area.id
        new_local_properties = AreaPropertiesLocal.build_for_update(properties, area.properties)

        # Adequacy patch
        if properties.adequacy_patch_mode:
            adequacy_patch_ini = new_local_properties.to_adequacy_ini()
            self._save_adequacy_ini(adequacy_patch_ini, area_id)

        # Thermal properties
        if properties.energy_cost_spilled is not None or properties.energy_cost_unsupplied is not None:
            current_content = self.read_thermal_areas_ini()
            if properties.energy_cost_spilled is not None:
                current_content["spilledenergycost"][area_id] = properties.energy_cost_spilled
            if properties.energy_cost_unsupplied is not None:
                current_content["unserverdenergycost"][area_id] = properties.energy_cost_unsupplied
            self._save_thermal_areas_ini(current_content)

        # Optimization properties
        if (
            properties.filter_synthesis is not None
            or properties.filter_by_year is not None
            or properties.non_dispatch_power is not None
            or properties.dispatch_hydro_power is not None
            or properties.other_dispatch_power is not None
            or properties.spread_spilled_energy_cost is not None
            or properties.spread_unsupplied_energy_cost is not None
        ):
            new_content = new_local_properties.to_optimization_ini()
            self._save_optimization_ini(new_content, area_id)

        return new_local_properties.to_user_model()

    @override
    def update_area_ui(self, area: Area, ui: AreaUiUpdate) -> AreaUi:
        new_local_ui = AreaUiLocal.build_for_update(ui, area.ui)
        self._save_ui_ini(new_local_ui.model_dump(mode="json", by_alias=True, exclude_unset=True), area.id)
        return new_local_ui.to_user_model()

    def _delete_clusters(self, cluster_type: str, area_id: str, names_to_delete: set[str]) -> None:
        ini_path = self.config.study_path / "input" / cluster_type / "clusters" / area_id / "list.ini"
        clusters_dict = IniReader().read(ini_path)
        clusters_dict_after_deletion = copy.deepcopy(clusters_dict)
        for cluster_id, cluster in clusters_dict.items():
            if cluster["name"] in names_to_delete:
                del clusters_dict_after_deletion[cluster_id]
        IniWriter().write(clusters_dict_after_deletion, ini_path)

    @override
    def delete_thermal_clusters(self, area_id: str, thermal_clusters: List[ThermalCluster]) -> None:
        thermal_names_to_delete = {th.name for th in thermal_clusters}
        # Check thermal clusters are not referenced in any binding constraint
        bc_service = cast(BindingConstraintLocalService, self._binding_constraint_service)
        all_constraints = bc_service.read_binding_constraints()
        for cluster in thermal_clusters:
            referencing_binding_constraints = []
            for bc in all_constraints.values():
                for term in bc._terms.values():
                    data = term.data
                    if isinstance(data, ClusterData) and data.area == cluster.area_id and data.cluster == cluster.id:
                        referencing_binding_constraints.append(bc.name)
                        break
            if referencing_binding_constraints:
                raise ReferencedObjectDeletionNotAllowed(
                    cluster.id, referencing_binding_constraints, object_type="Thermal cluster"
                )

        # Delete the clusters
        self._delete_clusters("thermal", area_id, thermal_names_to_delete)

        # Remove the matrices
        for thermal in thermal_clusters:
            shutil.rmtree(self.config.study_path / "input" / "thermal" / "series" / thermal.area_id / thermal.id)

        # Clean the scenario-builder
        cluster_ids = {th.id for th in thermal_clusters}

        def clean_thermals(symbol: str, parts: list[str]) -> bool:
            return symbol == "t" and parts[0] == area_id and parts[2] in cluster_ids

        remove_object_from_scenario_builder(self.config.study_path, clean_thermals)

    @override
    def delete_renewable_clusters(self, area_id: str, renewable_clusters: List[RenewableCluster]) -> None:
        renewable_names_to_delete = {renewable.name for renewable in renewable_clusters}
        self._delete_clusters("renewables", area_id, renewable_names_to_delete)

        # Remove the matrices
        for renewable in renewable_clusters:
            shutil.rmtree(self.config.study_path / "input" / "renewables" / "series" / renewable.area_id / renewable.id)

        # Clean the scenario-builder
        cluster_ids = {renewable.id for renewable in renewable_clusters}

        def clean_renewables(symbol: str, parts: list[str]) -> bool:
            return symbol == "r" and parts[0] == area_id and parts[2] in cluster_ids

        remove_object_from_scenario_builder(self.config.study_path, clean_renewables)

    @override
    def delete_st_storages(self, area_id: str, storages: List[STStorage]) -> None:
        storage_names_to_delete = {st.name for st in storages}
        self._delete_clusters("st-storage", area_id, storage_names_to_delete)

        for storage in storages:
            area_id = storage.area_id
            # Remove the matrices
            shutil.rmtree(self.config.study_path / "input" / "st-storage" / "series" / area_id / storage.id)

            # Remove the constraints
            constraints_path = self.config.study_path / "input" / "st-storage" / "constraints" / area_id / storage.id
            if constraints_path.exists():
                shutil.rmtree(constraints_path)

        # Clean the scenario-builder
        if self.study_version < STUDY_VERSION_9_2:
            # The sc builder is filled with sts data since v9.2 alone
            return

        storage_ids = {sts.id for sts in storages}

        def clean_sts(symbol: str, parts: list[str]) -> bool:
            return symbol in {"sts", "sta"} and parts[0] == area_id and parts[2] in storage_ids

        remove_object_from_scenario_builder(self.config.study_path, clean_sts)

    @override
    def get_load_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.LOAD, self.config.study_path, area_id=area_id)

    @override
    def get_solar_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.SOLAR, self.config.study_path, area_id=area_id)

    @override
    def get_wind_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.WIND, self.config.study_path, area_id=area_id)

    @override
    def get_reserves_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.RESERVES, self.config.study_path, area_id=area_id)

    @override
    def get_misc_gen_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.MISC_GEN, self.config.study_path, area_id=area_id)

    @override
    def update_areas_properties(self, dict_areas: Dict[Area, AreaPropertiesUpdate]) -> Dict[str, AreaProperties]:
        new_properties_dict = {}
        for area, update_properties in dict_areas.items():
            new_properties = self.update_area_properties(area, update_properties)
            new_properties_dict[area.id] = new_properties
        return new_properties_dict

    @override
    def delete_area(self, area_id: str, links: list[Link]) -> None:
        for link in links:
            if link.area_to_id == area_id:
                self._link_service.delete_link(link)

        folders = [
            Path(f"input/areas/{area_id}"),
            Path(f"input/links/{area_id}"),
            Path(f"input/hydro/prepro/{area_id}"),
            Path(f"input/hydro/series/{area_id}"),
            Path(f"input/load/prepro/{area_id}"),
            Path(f"input/solar/prepro/{area_id}"),
            Path(f"input/wind/prepro/{area_id}"),
            Path(f"input/renewables/clusters/{area_id}"),
            Path(f"input/renewables/series/{area_id}"),
            Path(f"input/st-storage/clusters/{area_id}"),
            Path(f"input/st-storage/series/{area_id}"),
            Path(f"input/thermal/clusters/{area_id}"),
            Path(f"input/thermal/prepro/{area_id}"),
            Path(f"input/thermal/series/{area_id}"),
            Path(f"input/st-storage/constraints/{area_id}"),
        ]
        for folder in folders:
            shutil.rmtree(self.config.study_path / folder, ignore_errors=True)

        files = [
            TimeSeriesFileType.HYDRO_MAX_POWER.value.format(area_id=area_id),
            TimeSeriesFileType.HYDRO_RESERVOIR.value.format(area_id=area_id),
            TimeSeriesFileType.HYDRO_INFLOW_PATTERN.value.format(area_id=area_id),
            TimeSeriesFileType.HYDRO_CREDITS_MODULATION.value.format(area_id=area_id),
            TimeSeriesFileType.HYDRO_WATER_VALUES.value.format(area_id=area_id),
            TimeSeriesFileType.LOAD.value.format(area_id=area_id),
            TimeSeriesFileType.MISC_GEN.value.format(area_id=area_id),
            TimeSeriesFileType.SOLAR.value.format(area_id=area_id),
            TimeSeriesFileType.WIND.value.format(area_id=area_id),
            TimeSeriesFileType.RESERVES.value.format(area_id=area_id),
        ]
        for file in files:
            (self.config.study_path / file).unlink(missing_ok=True)

        self._remove_area_from_hydro_ini_file(area_id)
        self._remove_area_from_thermal_ini_file(area_id)
        self._remove_area_from_list_txt_file(area_id)
        self._remove_area_from_correlation_matrices(area_id)
        self._remove_area_from_hydro_allocation(area_id)
        self._remove_area_from_districts(area_id)

        def clean_area(symbol: str, parts: list[str]) -> bool:
            area_keys = {"l", "h", "w", "s", "t", "r", "hl", "hfl", "hgp", "sts", "sta"}
            link_keys = {"ntc"}
            return (symbol in area_keys and parts[0] == area_id) or (
                symbol in link_keys and (parts[0] == area_id or parts[1] == area_id)
            )

        remove_object_from_scenario_builder(self.config.study_path, clean_area)

    def _remove_area_from_hydro_ini_file(self, id_to_remove: str) -> None:
        hydro_service = cast(HydroLocalService, self._hydro_service)
        ini_content = hydro_service.read_hydro_ini()
        for key, values in ini_content.items():
            for area_id in values:
                if area_id == id_to_remove:
                    del ini_content[key][area_id]
                    break
        hydro_service.save_hydro_ini(ini_content)

    def _remove_area_from_thermal_ini_file(self, id_to_remove: str) -> None:
        ini_content = self.read_thermal_areas_ini()
        for key, values in ini_content.items():
            for area_id in values:
                if area_id == id_to_remove:
                    del ini_content[key][area_id]
                    break
        self._save_thermal_areas_ini(ini_content)

    def _remove_area_from_list_txt_file(self, id_to_remove: str) -> None:
        file_path = self.config.study_path / "input" / "areas" / "list.txt"
        context = file_path.read_text().splitlines()
        context.remove(id_to_remove)
        file_path.write_text("\n".join(context) + "\n")

    def _remove_area_from_correlation_matrices(self, area_id: str) -> None:
        file_path = self.config.study_path / "input" / "hydro" / "prepro" / "correlation.ini"
        correlation_cfg = IniReader().read(file_path)
        for section, correlation in correlation_cfg.items():
            if section == "general":
                continue
            for key in list(correlation):
                a1, a2 = key.split("%")
                if a1 == area_id or a2 == area_id:
                    del correlation[key]
        IniWriter().write(correlation_cfg, file_path)

    def _remove_area_from_hydro_allocation(self, area_id: str) -> None:
        file_path = self.config.study_path / "input" / "hydro" / "allocation" / f"{area_id}.ini"
        file_path.unlink(missing_ok=True)
        hydro_service = cast(HydroLocalService, self._hydro_service)
        for file in (self.config.study_path / "input" / "hydro" / "allocation").iterdir():
            other_area_id = file.stem
            allocation = hydro_service.read_allocation_for_area(other_area_id)
            new_allocations = copy.deepcopy(allocation)
            for alloc in allocation:
                if alloc.area_id == area_id:
                    new_allocations.remove(alloc)
            if len(new_allocations) != len(allocation):
                hydro_service.set_allocation(other_area_id, allocation)

    def _remove_area_from_districts(self, area_id: str) -> None:
        file_path = self.config.study_path / "input" / "areas" / "sets.ini"
        districts = IniReader().read(file_path)
        for district in districts.values():
            if district.get("+", None):
                with contextlib.suppress(ValueError):
                    district["+"].remove(area_id)
            elif district.get("-", None):
                with contextlib.suppress(ValueError):
                    district["-"].remove(area_id)

        IniWriter().write(districts, file_path)
