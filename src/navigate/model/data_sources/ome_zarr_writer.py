# Copyright (c) 2021-2026  The University of Texas Southwestern Medical Center.
# All rights reserved.

from __future__ import annotations

import json
from typing import Dict, Iterable, Optional

import numpy as np
import numpy.typing as npt
import zarr
from zarr.codecs import BloscCodec

from navigate.tools.common_functions import copy_proxy_object

from .storage_adapter import OMEZarrStorageAdapter


class OMEZarrV3StoreWriter:
    """Write Navigate acquisitions into the canonical v0.5 OME-Zarr layout."""

    def __init__(
        self,
        file_name: str,
        metadata,
        dtype: str,
        chunk_shape: tuple[int, int, int, int, int],
        shard_shape: tuple[int, int, int, int, int],
        scale_factors: tuple[int, ...],
    ) -> None:
        self.file_name = file_name
        self.metadata = metadata
        self.dtype = np.dtype(dtype)
        self.chunk_shape = tuple(int(v) for v in chunk_shape)
        self.shard_shape = tuple(int(v) for v in shard_shape)
        self.scale_factors = tuple(int(v) for v in scale_factors)
        self.adapter = OMEZarrStorageAdapter(file_name)
        self.compressor = BloscCodec(cname="zstd", clevel=1, shuffle="bitshuffle")

        self.root = None
        self._well_group = None
        self._field_groups: dict[int, zarr.Group] = {}
        self._field_views: dict[int, Dict] = {}
        self._slabs: dict[tuple[int, int, int], dict] = {}
        self._written_positions: set[int] = set()

    @property
    def image(self):
        return self.root

    def setup(self) -> None:
        self.root = zarr.open_group(self.file_name, mode="w", zarr_format=3)
        row_group = self.root.create_group(self.adapter.row_name)
        self._well_group = row_group.create_group(self.adapter.column_name)
        self._update_hcs_metadata(positions=self.metadata.positions)
        self._update_well_metadata([])

    def _update_hcs_metadata(self, positions: int) -> None:
        self.root.attrs.update(self.metadata.hcs_attributes(positions))
        self.root.attrs["bioformats2raw.layout"] = 3

    def _update_well_metadata(self, field_names: Iterable[str]) -> None:
        self._well_group.attrs.update(self.metadata.well_attributes(field_names))

    def _field_group(self, position_index: int) -> zarr.Group:
        if position_index in self._field_groups:
            return self._field_groups[position_index]

        field_group = self._well_group.create_group(str(position_index))
        level0_shape = (
            int(self.metadata.shape_t),
            int(self.metadata.shape_c),
            int(self.metadata.shape_z),
            int(self.metadata.shape_y),
            int(self.metadata.shape_x),
        )
        chunks = self._clamp_chunks(level0_shape)
        shards = self._clamp_shards(level0_shape, chunks)
        field_group.create_array(
            "0",
            shape=level0_shape,
            dtype=self.dtype,
            chunks=chunks,
            shards=shards,
            compressors=self.compressor,
            dimension_names=self.metadata.axes_names,
            overwrite=True,
        )
        self._field_groups[position_index] = field_group
        return field_group

    def write_plane(
        self,
        position_index: int,
        time_index: int,
        channel_index: int,
        z_index: int,
        data: npt.ArrayLike,
        view: Optional[Dict] = None,
    ) -> None:
        self._field_group(position_index)
        self._written_positions.add(position_index)
        if view is not None and position_index not in self._field_views:
            self._field_views[position_index] = dict(view)

        chunk_depth = max(int(self.chunk_shape[2]), 1)
        slab_key = (position_index, time_index, channel_index)
        slab_start = (z_index // chunk_depth) * chunk_depth
        slab = self._slabs.get(slab_key)
        if slab is None or slab["start_z"] != slab_start:
            self._flush_slab(slab_key)
            slab_length = min(chunk_depth, self.metadata.shape_z - slab_start)
            slab = {
                "start_z": slab_start,
                "data": np.zeros(
                    (slab_length, self.metadata.shape_y, self.metadata.shape_x),
                    dtype=self.dtype,
                ),
                "count": 0,
            }
            self._slabs[slab_key] = slab

        plane_offset = z_index - slab_start
        slab["data"][plane_offset] = np.asarray(data, dtype=self.dtype)
        slab["count"] = max(slab["count"], plane_offset + 1)

        if slab["count"] == slab["data"].shape[0]:
            self._flush_slab(slab_key)

    def _flush_slab(self, slab_key: tuple[int, int, int]) -> None:
        slab = self._slabs.pop(slab_key, None)
        if slab is None or slab["count"] == 0:
            return

        position_index, time_index, channel_index = slab_key
        field_group = self._field_groups[position_index]
        level0 = field_group["0"]
        start = slab["start_z"]
        stop = start + slab["count"]
        level0[
            time_index,
            channel_index,
            start:stop,
            : self.metadata.shape_y,
            : self.metadata.shape_x,
        ] = slab["data"][: slab["count"]]

    def finalize(self, shape_t: int, shape_c: int, shape_z: int, positions: int) -> None:
        for slab_key in list(self._slabs):
            self._flush_slab(slab_key)

        valid_positions = sorted(position for position in self._written_positions if position < positions)
        for position_index in valid_positions:
            field_group = self._field_groups[position_index]
            level0 = field_group["0"]
            target_shape = (
                int(shape_t),
                int(shape_c),
                int(shape_z),
                int(self.metadata.shape_y),
                int(self.metadata.shape_x),
            )
            if tuple(level0.shape) != target_shape:
                level0.resize(target_shape)

            level_paths = ["0"]
            for level_index, scale_factor in enumerate(self.scale_factors[1:], start=1):
                level_name = str(level_index)
                if level_name in field_group:
                    del field_group[level_name]

                level_shape = self._scaled_shape(target_shape, scale_factor)
                chunks = self._clamp_chunks(level_shape)
                shards = self._clamp_shards(level_shape, chunks)
                level_array = field_group.create_array(
                    level_name,
                    shape=level_shape,
                    dtype=self.dtype,
                    chunks=chunks,
                    shards=shards,
                    compressors=self.compressor,
                    dimension_names=self.metadata.axes_names,
                    overwrite=True,
                )
                for t_idx in range(level_shape[0]):
                    for c_idx in range(level_shape[1]):
                        downsampled = level0[
                            t_idx,
                            c_idx,
                            : target_shape[2],
                            : target_shape[3],
                            : target_shape[4],
                        ][::scale_factor, ::scale_factor, ::scale_factor]
                        level_array[t_idx, c_idx, ...] = np.asarray(
                            downsampled, dtype=self.dtype
                        )
                level_paths.append(level_name)

            field_group.attrs.update(
                self.metadata.image_attributes(
                    name=f"Field {position_index}",
                    paths=level_paths,
                    scale_factors=self.scale_factors[: len(level_paths)],
                    view=self._field_views.get(position_index),
                )
            )
            self.metadata.validate_image_group(field_group)

        field_names = [str(position_index) for position_index in valid_positions]
        self._update_hcs_metadata(positions=max(len(field_names), 1))
        self._update_well_metadata(field_names)
        self.metadata.validate_hcs_group(self.root)
        self.metadata.validate_well_group(self._well_group)
        self._write_metadata_sidecars(field_names)

    def _write_metadata_sidecars(self, field_names: list[str]) -> None:
        metadata_dir = self.adapter.absolute_path(self.adapter.metadata_root)
        metadata_dir.mkdir(parents=True, exist_ok=True)

        acquisition = copy_proxy_object(self.metadata.configuration.get("experiment", {}))
        configuration = copy_proxy_object(
            self.metadata.configuration.get("configuration", {})
        )
        artifacts = self.adapter.artifact_manifest(
            int(name) for name in field_names if name.isdigit()
        )

        acquisition["field_names"] = field_names
        acquisition["store"] = self.file_name

        for name, payload in (
            ("artifacts", artifacts),
            ("acquisition", acquisition),
            ("configuration", configuration),
        ):
            target_path = self.adapter.absolute_path(self.adapter.metadata_blob_path(name))
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2, default=self._json_default)

        ome_dir = self.adapter.absolute_path("OME")
        ome_dir.mkdir(parents=True, exist_ok=True)
        with open(ome_dir / "METADATA.ome.xml", "w", encoding="utf-8") as handle:
            handle.write(self.metadata.metadata_only_xml(field_names))

    @staticmethod
    def _json_default(value):
        if isinstance(value, np.generic):
            return value.item()
        if hasattr(value, "isoformat"):
            return value.isoformat()
        return str(value)

    def close(self) -> None:
        self.root = None
        self._well_group = None
        self._field_groups.clear()
        self._field_views.clear()
        self._slabs.clear()
        self._written_positions.clear()

    def _scaled_shape(
        self, shape: tuple[int, int, int, int, int], scale_factor: int
    ) -> tuple[int, int, int, int, int]:
        return (
            shape[0],
            shape[1],
            max((shape[2] + scale_factor - 1) // scale_factor, 1),
            max((shape[3] + scale_factor - 1) // scale_factor, 1),
            max((shape[4] + scale_factor - 1) // scale_factor, 1),
        )

    def _clamp_chunks(self, shape: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(max(1, min(target, axis_len)) for target, axis_len in zip(self.chunk_shape, shape))

    def _clamp_shards(
        self, shape: tuple[int, ...], chunks: tuple[int, ...]
    ) -> tuple[int, ...]:
        shards = []
        for axis_len, chunk, target in zip(shape, chunks, self.shard_shape):
            axis_target = min(target, axis_len)
            multiple = max((axis_target // chunk), 1)
            shards.append(max(chunk, multiple * chunk))
        return tuple(shards)
