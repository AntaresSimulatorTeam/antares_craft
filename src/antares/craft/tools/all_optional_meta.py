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

from typing import Optional, Type, TypeVar

from pydantic import BaseModel, Field, create_model

ModelClass = TypeVar("ModelClass", bound=BaseModel)


def all_optional_model(model: Type[ModelClass]) -> Type[ModelClass]:
    """
    This decorator can be used to make all fields of a pydantic model optionals.

    Args:
        model: The pydantic model to modify.

    Returns:
        The modified model.
    """
    kwargs = {}
    for field_name, field_info in model.model_fields.items():
        # Create a new Field with default=None to make it optional
        new_field = Field(
            default=None,
            alias=field_info.alias,
            validation_alias=field_info.validation_alias,
            serialization_alias=field_info.serialization_alias,
            title=field_info.title,
            description=field_info.description,
        )
        new_annotation = Optional[field_info.annotation]  # type: ignore
        kwargs[field_name] = (new_annotation, new_field)

    return create_model(f"Partial{model.__name__}", __base__=model, __module__=model.__module__, **kwargs)  # type: ignore
