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

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.area import AdequacyPatchMode, AreaProperties, AreaPropertiesUpdate, AreaUi, AreaUiUpdate
from antares.craft.model.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
    ClusterData,
    ConstraintTerm,
    ConstraintTermUpdate,
    LinkData,
)
from antares.craft.model.commons import FilterOption
from antares.craft.model.hydro import HydroProperties, HydroPropertiesUpdate
from antares.craft.model.link import (
    AssetType,
    LinkProperties,
    LinkPropertiesUpdate,
    LinkStyle,
    LinkUi,
    LinkUiUpdate,
    TransmissionCapacities,
)
from antares.craft.model.output import (
    Frequency,
    MCAllAreasDataType,
    MCAllLinksDataType,
    MCIndAreasDataType,
    MCIndLinksDataType,
)
from antares.craft.model.renewable import (
    RenewableClusterGroup,
    RenewableClusterProperties,
    RenewableClusterPropertiesUpdate,
    TimeSeriesInterpretation,
)
from antares.craft.model.scenario_builder import ScenarioBuilder
from antares.craft.model.settings.adequacy_patch import AdequacyPatchParametersUpdate, PriceTakingOrder
from antares.craft.model.settings.advanced_parameters import (
    AdvancedParametersUpdate,
    HydroHeuristicPolicy,
    HydroPricingMode,
    InitialReservoirLevel,
    PowerFluctuation,
    RenewableGenerationModeling,
    SeedParametersUpdate,
    SheddingPolicy,
    SimulationCore,
    UnitCommitmentMode,
)
from antares.craft.model.settings.general import (
    BuildingMode,
    GeneralParametersUpdate,
    Mode,
    Month,
    OutputChoices,
    WeekDay,
)
from antares.craft.model.settings.optimization import (
    ExportMPS,
    OptimizationParametersUpdate,
    OptimizationTransmissionCapacities,
    SimplexOptimizationRange,
    UnfeasibleProblemBehavior,
)
from antares.craft.model.settings.playlist_parameters import PlaylistParameters
from antares.craft.model.settings.study_settings import StudySettingsUpdate
from antares.craft.model.settings.thematic_trimming import ThematicTrimmingParameters
from antares.craft.model.simulation import AntaresSimulationParameters, Solver
from antares.craft.model.st_storage import STStorageGroup, STStorageProperties, STStoragePropertiesUpdate
from antares.craft.model.study import (
    Study,
    create_study_api,
    create_study_local,
    create_variant_api,
    import_study_api,
    read_study_api,
    read_study_local,
)
from antares.craft.model.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalClusterGroup,
    ThermalClusterProperties,
    ThermalClusterPropertiesUpdate,
    ThermalCostGeneration,
)

__all__ = [
    # Instantiation classes and methods
    "Study",
    "APIconf",
    "LocalConfiguration",
    "create_study_api",
    "import_study_api",
    "read_study_api",
    "create_variant_api",
    "read_study_local",
    "create_study_local",
    # Enums
    "PriceTakingOrder",
    "InitialReservoirLevel",
    "HydroHeuristicPolicy",
    "HydroPricingMode",
    "PowerFluctuation",
    "SheddingPolicy",
    "UnitCommitmentMode",
    "SimulationCore",
    "RenewableGenerationModeling",
    "Mode",
    "Month",
    "WeekDay",
    "BuildingMode",
    "OutputChoices",
    "OptimizationTransmissionCapacities",
    "UnfeasibleProblemBehavior",
    "SimplexOptimizationRange",
    "ExportMPS",
    "AdequacyPatchMode",
    "BindingConstraintFrequency",
    "BindingConstraintOperator",
    "TransmissionCapacities",
    "AssetType",
    "LinkStyle",
    "RenewableClusterGroup",
    "TimeSeriesInterpretation",
    "STStorageGroup",
    "LawOption",
    "ThermalClusterGroup",
    "LocalTSGenerationBehavior",
    "ThermalCostGeneration",
    "Frequency",
    "MCIndAreasDataType",
    "MCAllAreasDataType",
    "MCIndLinksDataType",
    "MCAllLinksDataType",
    # Model classes
    "AdequacyPatchParametersUpdate",
    "AdvancedParametersUpdate",
    "SeedParametersUpdate",
    "GeneralParametersUpdate",
    "OptimizationParametersUpdate",
    "PlaylistParameters",
    "ThematicTrimmingParameters",
    "StudySettingsUpdate",
    "ScenarioBuilder",
    "AreaProperties",
    "AreaPropertiesUpdate",
    "AreaUi",
    "AreaUiUpdate",
    "LinkData",
    "ClusterData",
    "ConstraintTerm",
    "ConstraintTermUpdate",
    "BindingConstraintProperties",
    "BindingConstraintPropertiesUpdate",
    "FilterOption",
    "HydroProperties",
    "HydroPropertiesUpdate",
    "LinkProperties",
    "LinkPropertiesUpdate",
    "LinkUi",
    "LinkUiUpdate",
    "RenewableClusterProperties",
    "RenewableClusterPropertiesUpdate",
    "Solver",
    "AntaresSimulationParameters",
    "STStorageProperties",
    "STStoragePropertiesUpdate",
    "ThermalClusterProperties",
    "ThermalClusterPropertiesUpdate",
]
