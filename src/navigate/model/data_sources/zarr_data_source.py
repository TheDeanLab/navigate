# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np
import numpy.typing as npt
import zarr

from .ome_zarr_writer import OMEZarrV3StoreWriter
from .pyramidal_data_source import PyramidalDataSource
from .storage_adapter import OMEZarrStorageAdapter
from ..metadata_sources.zarr_metadata import OMEZarrMetadata


class OMEZarrDataSource(PyramidalDataSource):
    """OME-Zarr data source backed by a Zarr v3 single-well HCS layout."""

    default_chunk_shape = (1, 1, 8, 256, 256)
    default_shard_shape = (1, 1, 32, 256, 256)
    default_scale_factors = (1, 2, 4, 8, 16)

    def __init__(self, file_name: str = None, mode: str = "w") -> None:
        self.metadata = OMEZarrMetadata()
        self.image = None
        self._writer: Optional[OMEZarrV3StoreWriter] = None
        self._adapter = OMEZarrStorageAdapter(file_name or "")
        self.chunk_shape = self.default_chunk_shape
        self.shard_shape = self.default_shard_shape
        self.scale_factors = self.default_scale_factors

        super().__init__(file_name=file_name, mode=mode)

    @property
    def artifact_refs(self):
        return self._adapter.artifact_manifest(range(self.positions))

    def setup(self) -> None:
        self._adapter = OMEZarrStorageAdapter(self.file_name)
        self._writer = OMEZarrV3StoreWriter(
            file_name=self.file_name,
            metadata=self.metadata,
            dtype=self.dtype,
            chunk_shape=self.chunk_shape,
            shard_shape=self.shard_shape,
            scale_factors=self.scale_factors,
        )
        self._writer.setup()
        self.image = self._writer.image

    def set_metadata_from_configuration_experiment(
        self, configuration: Dict[str, Any], microscope_name: str = None
    ) -> None:
        super().set_metadata_from_configuration_experiment(configuration, microscope_name)
        self._apply_storage_parameters(configuration)

    def set_metadata(self, metadata_config: dict) -> None:
        super().set_metadata(metadata_config)
        self._apply_storage_parameters(self.metadata.configuration)

    def _apply_storage_parameters(self, configuration: Optional[Dict[str, Any]]) -> None:
        experiment = configuration.get("experiment", {}) if configuration else {}
        params = experiment.get("OMEZarrParameters", {})
        if params is None:
            params = {}

        self.chunk_shape = self._normalize_axis_shape(
            params.get("chunk_shape", self.default_chunk_shape),
            self.default_chunk_shape,
        )
        self.shard_shape = self._normalize_axis_shape(
            params.get("shard_shape", self.default_shard_shape),
            self.default_shard_shape,
        )

        down_sample = params.get("down_sample", {})
        if down_sample and down_sample.get("enabled", False):
            configured_scale_factors = tuple(
                sorted(
                    {
                        max(int(factor), 1)
                        for factor in down_sample.get(
                            "scale_factors", self.default_scale_factors[1:]
                        )
                    }
                )
            )
            self.scale_factors = (1,) + tuple(
                factor for factor in configured_scale_factors if factor > 1
            )
        else:
            self.scale_factors = (1,)

        if self._writer is not None:
            self._writer.chunk_shape = self.chunk_shape
            self._writer.shard_shape = self.shard_shape
            self._writer.scale_factors = self.scale_factors

    @staticmethod
    def _normalize_axis_shape(
        value: Any, fallback: tuple[int, int, int, int, int]
    ) -> tuple[int, int, int, int, int]:
        try:
            normalized = tuple(max(int(axis), 1) for axis in list(value))
        except (TypeError, ValueError):
            return fallback
        if len(normalized) != len(fallback):
            return fallback
        return normalized

    def get_slice(self, x, y, c, z=0, t=0, p=0, subdiv=0) -> npt.ArrayLike:
        field_group = self.image[self._adapter.field_group_path(int(p))]
        level_name = str(int(subdiv))
        return field_group[level_name][t, c, z, y, x]

    def write(self, data: npt.ArrayLike, **kw) -> None:
        self.mode = "w"

        if self._writer is None:
            self.setup()

        c_index, z_index, t_index, p_index = self._cztp_indices(
            self._current_frame, self.metadata.per_stack
        )
        view = kw if kw else None
        self._writer.write_plane(
            position_index=p_index,
            time_index=t_index,
            channel_index=c_index,
            z_index=z_index,
            data=data,
            view=view,
        )
        self.image = self._writer.image
        self._current_frame += 1

    def read(self) -> None:
        self.mode = "r"
        self._adapter = OMEZarrStorageAdapter(self.file_name)
        self.image = zarr.open_group(self.file_name, mode="r")
        well_group = self.image[self._adapter.well_path]
        field_names = sorted(name for name in list(well_group.keys()) if name.isdigit())
        if not field_names:
            return

        first_field = well_group[field_names[0]]
        level0 = first_field["0"]
        self.shape_t, self.shape_c, self.shape_z, self.shape_y, self.shape_x = (
            int(axis) for axis in level0.shape
        )
        self.positions = len(field_names)

        multiscales = first_field.attrs.get("ome", {}).get("multiscales", [])
        if multiscales:
            datasets = multiscales[0].get("datasets", [])
            resolutions = [[1, 1, 1]]
            for dataset in datasets[1:]:
                transforms = dataset.get("coordinateTransformations", [])
                scale = next(
                    (
                        transform.get("scale")
                        for transform in transforms
                        if transform.get("type") == "scale"
                    ),
                    None,
                )
                if scale is None:
                    continue
                resolutions.append(
                    [
                        max(int(round(scale[4] / self.dx)), 1),
                        max(int(round(scale[3] / self.dy)), 1),
                        max(int(round(scale[2] / self.dz)), 1),
                    ]
                )
            self._resolutions = np.array(resolutions, dtype=int)

    def get_data(
        self,
        timepoint: int = 0,
        position: int = 0,
        channel: int = 0,
        z: int = -1,
        resolution: int = 1,
    ) -> npt.ArrayLike:
        level_index = 0
        if resolution > 1:
            if resolution in self.scale_factors:
                level_index = self.scale_factors.index(resolution)
            else:
                level_index = min(len(self.scale_factors) - 1, int(resolution))

        field_group = self.image[self._adapter.field_group_path(position)]
        level = field_group[str(level_index)]
        if z < 0:
            return level[timepoint, channel]
        return level[timepoint, channel, z]

    def close(self) -> None:
        if self._closed:
            self._writer = None
            self.image = None
            return

        try:
            if self.mode == "w" and self._writer is not None:
                self._check_shape(self._current_frame - 1, self.metadata.per_stack)
                self._writer.finalize(
                    shape_t=self.shape_t,
                    shape_c=self.shape_c,
                    shape_z=self.shape_z,
                    positions=self.positions,
                )
                self.image = self._writer.image
        finally:
            if self._writer is not None:
                self._writer.close()
            self._writer = None
            self.image = None
            self._closed = True
