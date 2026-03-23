# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

from __future__ import annotations

import logging
from typing import Dict, Iterable, List, Optional, Union

import numpy.typing as npt
from ome_zarr_models.v05.coordinate_transformations import (
    VectorScale,
    VectorTranslation,
)
from ome_zarr_models.v05.hcs import HCS, HCSAttrs, Well
from ome_zarr_models.v05.image import Axis, Dataset, Image, ImageAttrs, Multiscale
from ome_zarr_models.v05.image_label import ImageLabelAttrs
from ome_zarr_models.v05.image_label_types import Label
from ome_zarr_models.v05.labels import LabelsAttrs
from ome_zarr_models.v05.plate import Column, Plate, Row, WellInPlate
from ome_zarr_models.v05.well import WellAttrs
from ome_zarr_models.v05.well_types import WellImage, WellMeta

from navigate import __commit__, __version__
from navigate.tools import xml_tools

from .metadata import Metadata

NGFF_VERSION = "0.5"

p = __name__.split(".")[1]
logger = logging.getLogger(p)


class OMEZarrMetadata(Metadata):
    """Canonical OME-Zarr v0.5 metadata builder for Navigate."""

    @property
    def axes(self) -> List[Axis]:
        return [
            Axis(name="t", type="time", unit="second"),
            Axis(name="c", type="channel"),
            Axis(name="z", type="space", unit="micrometer"),
            Axis(name="y", type="space", unit="micrometer"),
            Axis(name="x", type="space", unit="micrometer"),
        ]

    @property
    def axes_names(self) -> tuple[str, ...]:
        return tuple(axis.name for axis in self.axes)

    def _stage_positions_to_translation_transform(
        self, x: float, y: float, z: float, theta: float, f: Optional[float] = None
    ) -> List[float]:
        xp, yp, zp = x, y, z
        if self._coupled_axes is not None:
            for leader, follower in self._coupled_axes.items():
                if leader.lower() not in "xyz":
                    logger.warning("Ignoring unsupported coupled axis %s.", leader)
                    continue
                follower_value = float(locals().get(follower.lower(), 0.0) or 0.0)
                if leader.lower() == "x":
                    xp += follower_value
                elif leader.lower() == "y":
                    yp += follower_value
                elif leader.lower() == "z":
                    zp += follower_value
        return [0.0, 0.0, zp, yp, xp]

    def _scale_transform(self, scale_factor: Union[int, npt.ArrayLike, List]) -> List[float]:
        if isinstance(scale_factor, int):
            zx = float(scale_factor)
            zy = float(scale_factor)
            zz = float(scale_factor)
        else:
            values = list(scale_factor)
            if len(values) != 3:
                raise ValueError("Scale factor must contain exactly 3 spatial values.")
            zx, zy, zz = map(float, values)
        return [1.0, 1.0, self.dz * zz, self.dy * zy, self.dx * zx]

    def _coordinate_transformations(
        self, scale: List[float], translation: Optional[List[float]] = None
    ) -> list:
        transformations = [VectorScale(type="scale", scale=scale)]
        if translation is not None:
            transformations.append(
                VectorTranslation(type="translation", translation=translation)
            )
        return transformations

    def hcs_attributes(self, positions: int) -> dict:
        plate = Plate(
            rows=[Row(name="A")],
            columns=[Column(name="1")],
            wells=[WellInPlate(path="A/1", rowIndex=0, columnIndex=0)],
            field_count=max(int(positions), 1),
            version=NGFF_VERSION,
        )
        return {
            "ome": HCSAttrs(version=NGFF_VERSION, plate=plate).model_dump(
                mode="json", exclude_none=True
            )
        }

    def well_attributes(self, field_names: Iterable[str]) -> dict:
        images = [WellImage(path=str(name)) for name in field_names]
        return {
            "ome": WellAttrs(
                version=NGFF_VERSION,
                well=WellMeta(images=images, version=NGFF_VERSION),
            ).model_dump(mode="json", exclude_none=True)
        }

    def image_attributes(
        self,
        name: str,
        paths: list[str],
        scale_factors: Union[npt.ArrayLike, List[int]],
        view: Optional[Dict] = None,
    ) -> dict:
        datasets = []
        for path, factor in zip(paths, scale_factors):
            scale = self._scale_transform(factor)
            datasets.append(
                Dataset(
                    path=path,
                    coordinateTransformations=self._coordinate_transformations(scale),
                )
            )
        multiscale = Multiscale(
            axes=self.axes,
            datasets=tuple(datasets),
            name=name,
            coordinateTransformations=(
                None
                if view is None
                else tuple(
                    self._coordinate_transformations(
                        [1.0] * len(self.axes),
                        self._stage_positions_to_translation_transform(**view),
                    )
                )
            ),
            metadata={"method": "subsample"},
            type="subsample",
        )
        return {
            "ome": ImageAttrs(version=NGFF_VERSION, multiscales=[multiscale]).model_dump(
                mode="json", exclude_none=True
            )
        }

    def labels_attributes(self, label_paths: list[str]) -> dict:
        return {
            "ome": LabelsAttrs(version=NGFF_VERSION, labels=label_paths).model_dump(
                mode="json", exclude_none=True
            )
        }

    def image_label_attributes(
        self, label_name: str, multiscale_paths: list[str], scale_factors: list[int]
    ) -> dict:
        datasets = []
        for path, factor in zip(multiscale_paths, scale_factors):
            datasets.append(
                Dataset(
                    path=path,
                    coordinateTransformations=self._coordinate_transformations(
                        self._scale_transform(factor)
                    ),
                )
            )
        multiscale = Multiscale(
            axes=self.axes,
            datasets=tuple(datasets),
            name=label_name,
            metadata={"method": "subsample"},
            type="subsample",
        )
        return {
            "ome": ImageLabelAttrs(
                version=NGFF_VERSION,
                image_label=Label(
                    source={"image": "../../../0"},
                    properties={"name": label_name},
                ),
                multiscales=[multiscale],
            ).model_dump(mode="json", exclude_none=True)
        }

    def validate_hcs_group(self, group) -> HCS:
        return HCS.from_zarr(group)

    def validate_well_group(self, group) -> Well:
        return Well.from_zarr(group)

    def validate_image_group(self, group) -> Image:
        return Image.from_zarr(group)

    def metadata_only_xml(self, field_names: list[str]) -> str:
        channels = [
            {"ID": f"Channel:0:{idx}", "SamplesPerPixel": "1", "LightPath": {}}
            for idx in range(self.shape_c)
        ]
        images = []
        for idx, field_name in enumerate(field_names):
            images.append(
                {
                    "ID": f"Image:{idx}",
                    "Name": field_name,
                    "Pixels": {
                        "ID": f"Pixels:{idx}",
                        "BigEndian": "false",
                        "Interleaved": "false",
                        "Type": str(self.dtype if hasattr(self, "dtype") else "uint16"),
                        "SizeX": self.shape_x,
                        "SizeY": self.shape_y,
                        "SizeZ": self.shape_z,
                        "SizeC": self.shape_c,
                        "SizeT": self.shape_t,
                        "DimensionOrder": "XYZCT",
                        "PhysicalSizeX": self.dx,
                        "PhysicalSizeY": self.dy,
                        "PhysicalSizeZ": self.dz,
                        "TimeIncrement": self.dt,
                        "Channel": channels,
                        "MetadataOnly": {},
                    },
                }
            )

        ome_dict = {
            "Creator": f"Navigate,v{__version__}, Commit {__commit__}, Dean Lab at UTSW",
            "xmlns": "http://www.openmicroscopy.org/Schemas/OME/2016-06",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:schemaLocation": "http://www.openmicroscopy.org/Schemas/OME/2016-06 "
            "https://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd",
            "Image": images,
            "StructuredAnnotations": {
                "ListAnnotation": {
                    "ID": "Annotation:misc",
                    "Description": {"text": self.misc},
                }
            },
        }
        xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += f"<!-- Created by Navigate, v{__version__}, Commit {__commit__} -->\n"
        xml += xml_tools.dict_to_xml(ome_dict, "OME")
        return xml
