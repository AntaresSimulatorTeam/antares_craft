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

import typing

if typing.TYPE_CHECKING:
    from pathlib import Path
    from typing import Optional

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.model.study import Study

__all__ = [
    "Study",
    "create_study_api",
    "import_study_api",
    "read_study_api",
    "create_variant_api",
    "read_study_local",
    "create_study_local"
]


# Design note:
# all following methods are entry points for study creation.
# They use methods defined in "local" and "API" implementation services,
# that we inject here.
# Generally speaking, implementations should reference the API, not the
# opposite. Here we perform dependency injection, and because of python
# import mechanics, we need to use local imports to avoid circular dependencies.

def create_study_local(study_name: str, version: str, parent_directory: "Path") -> "Study":
    # Here we inject implementation of this method,
    # we need to have a local import to avoid python circular dependency
    from antares.craft.service.local_services.factory import create_study_local
    return create_study_local(study_name, version, parent_directory)

def read_study_local(study_path: "Path") -> "Study":
    # Here we inject implementation of this method,
    # we need to have a local import to avoid python circular dependency
    from antares.craft.service.local_services.factory import read_study_local
    return read_study_local(study_path)


def create_study_api(
    study_name: str,
    version: str,
    api_config: APIconf,
    parent_path: "Optional[Path]" = None,
) -> "Study":
    """
    Args:
        study_name: antares study name to be created
        version: antares version
        api_config: host and token config for API

    Raises:
        MissingTokenError if api_token is missing
        StudyCreationError if an HTTP Exception occurs
    """
    from antares.craft.service.api_services.factory import create_study_api
    return create_study_api(study_name, version, api_config, parent_path)


def import_study_api(api_config: APIconf, study_path: "Path", destination_path: "Optional[Path]" = None) -> "Study":
    from antares.craft.service.api_services.factory import import_study_api
    return import_study_api(api_config, study_path, destination_path)


def read_study_api(api_config: APIconf, study_id: str) -> "Study":
    from antares.craft.service.api_services.factory import read_study_api
    return read_study_api(api_config, study_id)


def create_variant_api(api_config: APIconf, study_id: str, variant_name: str) -> "Study":
    """
    Creates a variant from a study_id
    Args:
        api_config: API configuration
        study_id: The id of the study to create a variant of
        variant_name: the name of the new variant
    Returns: The variant in the form of a Study object
    """
    from antares.craft.service.api_services.factory import create_variant_api
    return create_variant_api(api_config, study_id, variant_name)


