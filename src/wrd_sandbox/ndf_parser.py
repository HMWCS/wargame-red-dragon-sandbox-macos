from __future__ import annotations

from dataclasses import dataclass
import struct
from pathlib import Path
from typing import Any

from wgrd_cons_parsers.compress_ndfbin import compress_ndfbin
from wgrd_cons_parsers.decompress_ndfbin import decompress_ndfbin


TYPE_NAMES = {
    0x00000000: "Boolean",
    0x00000001: "Int8",
    0x00000002: "Int32",
    0x00000003: "UInt32",
    0x00000004: "Time64",
    0x00000005: "Float32",
    0x00000006: "Float64",
    0x00000007: "TableString",
    0x00000008: "WideString",
    0x00000009: "Reference",
    0x0000000B: "Vector",
    0x0000000C: "Color128",
    0x0000000D: "Color32",
    0x0000000E: "TrippleInt",
    0x00000011: "List",
    0x00000012: "MapList",
    0x00000013: "Long",
    0x00000014: "Blob",
    0x00000018: "Int16",
    0x00000019: "UInt16",
    0x0000001A: "Guid",
    0x0000001C: "TableStringFile",
    0x0000001D: "LocalisationHash",
    0x0000001E: "ZipBlob",
    0x0000001F: "EugInt2",
    0x00000021: "EugFloat2",
    0x00000022: "Map",
    0x00000025: "Hash",
    0xBBBBBBBB: "ObjectReference",
    0xAAAAAAAA: "TransTableReference",
}

TYPE_SIZES = {
    0x00000000: 1,
    0x00000001: 1,
    0x00000018: 2,
    0x00000019: 2,
    0x00000002: 4,
    0x00000003: 4,
    0x00000005: 4,
    0x00000007: 4,
    0x0000001C: 4,
    0x00000008: 4,
    0x0000000D: 4,
    0x00000006: 8,
    0x00000013: 8,
    0x0000001D: 8,
    0xBBBBBBBB: 8,
    0xAAAAAAAA: 4,
    0x0000001F: 8,
    0x00000021: 8,
    0x00000004: 8,
    0x0000000E: 12,
    0x0000000B: 12,
    0x0000000C: 16,
    0x0000001A: 16,
    0x00000025: 16,
}

TYPE_REFERENCE = 0x00000009
TYPE_MAP = 0x00000022
TYPE_LIST = 0x00000011
TYPE_MAP_LIST = 0x00000012
TYPE_BLOB = 0x00000014
TYPE_ZIP_BLOB = 0x0000001E
TYPE_WIDE_STRING = 0x00000008
OBJECT_TERMINATOR = 0xABABABAB


@dataclass
class FooterEntry:
    name: str
    offset: int
    size: int


@dataclass
class PropertyMeta:
    id: int
    name: str
    class_id: int
    class_name: str


@dataclass
class ValueNode:
    type_code: int
    type_name: str
    value: Any = None
    data_offset: int | None = None
    data_size: int = 0
    items: list[Any] | None = None
    actual_type_code: int | None = None


@dataclass
class PropertyNode:
    meta: PropertyMeta
    value: ValueNode


@dataclass
class ObjectNode:
    id: int
    class_id: int
    class_name: str
    properties: dict[str, PropertyNode]


class NdfParser:
    def __init__(self, raw_data: bytearray):
        self.raw_data = raw_data
        self.footer = self._read_footer()
        self.class_names = self._read_classes()
        self.properties = self._read_properties()
        self.objects = self._read_objects()

    @classmethod
    def from_file(cls, path: Path) -> tuple["NdfParser", bytes]:
        original = path.read_bytes()
        raw = bytearray(decompress_ndfbin(original))
        return cls(raw), original

    def write_back(self, output_path: Path) -> None:
        output_path.write_bytes(compress_ndfbin(bytes(self.raw_data)))

    def find_objects(self, class_name: str) -> list[ObjectNode]:
        return [obj for obj in self.objects if obj.class_name == class_name]

    def _read_footer(self) -> dict[str, FooterEntry]:
        footer_offset = struct.unpack_from("<Q", self.raw_data, 0x10)[0]
        magic = self.raw_data[footer_offset : footer_offset + 4]
        if magic != b"TOC0":
            raise RuntimeError("Could not find TOC0 footer")
        entry_count = struct.unpack_from("<I", self.raw_data, footer_offset + 4)[0]
        cursor = footer_offset + 8
        entries: dict[str, FooterEntry] = {}
        for _ in range(entry_count):
            name = bytes(self.raw_data[cursor : cursor + 8]).rstrip(b"\0").decode("ascii")
            offset = struct.unpack_from("<Q", self.raw_data, cursor + 8)[0]
            size = struct.unpack_from("<Q", self.raw_data, cursor + 16)[0]
            entries[name] = FooterEntry(name=name, offset=offset, size=size)
            cursor += 24
        return entries

    def _read_classes(self) -> list[str]:
        entry = self.footer["CLAS"]
        cursor = entry.offset
        names: list[str] = []
        while cursor < entry.offset + entry.size:
            length = struct.unpack_from("<I", self.raw_data, cursor)[0]
            cursor += 4
            names.append(bytes(self.raw_data[cursor : cursor + length]).decode("latin-1"))
            cursor += length
        return names

    def _read_properties(self) -> dict[int, PropertyMeta]:
        entry = self.footer["PROP"]
        cursor = entry.offset
        prop_id = 0
        props: dict[int, PropertyMeta] = {}
        while cursor < entry.offset + entry.size:
            length = struct.unpack_from("<I", self.raw_data, cursor)[0]
            cursor += 4
            name = bytes(self.raw_data[cursor : cursor + length]).decode("latin-1")
            cursor += length
            class_id = struct.unpack_from("<I", self.raw_data, cursor)[0]
            cursor += 4
            props[prop_id] = PropertyMeta(
                id=prop_id,
                name=name,
                class_id=class_id,
                class_name=self.class_names[class_id],
            )
            prop_id += 1
        return props

    def _read_objects(self) -> list[ObjectNode]:
        chunk_entry = self.footer["CHNK"]
        object_count = struct.unpack_from("<I", self.raw_data, chunk_entry.offset + 4)[0]
        objects_entry = self.footer["OBJE"]
        cursor = objects_entry.offset
        objects: list[ObjectNode] = []
        for object_id in range(object_count):
            class_id = struct.unpack_from("<I", self.raw_data, cursor)[0]
            cursor += 4
            properties: dict[str, PropertyNode] = {}
            while True:
                property_id = struct.unpack_from("<I", self.raw_data, cursor)[0]
                cursor += 4
                if property_id == OBJECT_TERMINATOR:
                    break
                meta = self.properties[property_id]
                value, cursor = self._read_value(cursor)
                properties[meta.name] = PropertyNode(meta=meta, value=value)
            objects.append(
                ObjectNode(
                    id=object_id,
                    class_id=class_id,
                    class_name=self.class_names[class_id],
                    properties=properties,
                )
            )
        return objects

    def _read_value(self, cursor: int) -> tuple[ValueNode, int]:
        type_code = struct.unpack_from("<I", self.raw_data, cursor)[0]
        cursor += 4
        actual_type = type_code
        if type_code == TYPE_REFERENCE:
            actual_type = struct.unpack_from("<I", self.raw_data, cursor)[0]
            cursor += 4

        if actual_type in (TYPE_LIST, TYPE_MAP_LIST, TYPE_WIDE_STRING, TYPE_BLOB, TYPE_ZIP_BLOB):
            count = struct.unpack_from("<I", self.raw_data, cursor)[0]
            cursor += 4
            if actual_type == TYPE_ZIP_BLOB:
                cursor += 1
        else:
            count = None

        if actual_type == TYPE_LIST:
            items = []
            for _ in range(count or 0):
                item, cursor = self._read_value(cursor)
                items.append(item)
            return ValueNode(type_code, TYPE_NAMES[actual_type], items=items, actual_type_code=actual_type), cursor

        if actual_type == TYPE_MAP_LIST:
            items = []
            for _ in range(count or 0):
                key, cursor = self._read_value(cursor)
                value, cursor = self._read_value(cursor)
                items.append((key, value))
            return ValueNode(type_code, TYPE_NAMES[actual_type], items=items, actual_type_code=actual_type), cursor

        if actual_type == TYPE_MAP:
            key, cursor = self._read_value(cursor)
            value, cursor = self._read_value(cursor)
            return ValueNode(
                type_code,
                TYPE_NAMES[actual_type],
                items=[(key, value)],
                actual_type_code=actual_type,
            ), cursor

        data_size = count if actual_type in (TYPE_WIDE_STRING, TYPE_BLOB, TYPE_ZIP_BLOB) else TYPE_SIZES[actual_type]
        data_offset = cursor
        raw = bytes(self.raw_data[cursor : cursor + data_size])
        cursor += data_size
        return ValueNode(
            type_code=type_code,
            type_name=TYPE_NAMES.get(actual_type, hex(actual_type)),
            value=self._decode_flat_value(actual_type, raw),
            data_offset=data_offset,
            data_size=data_size,
            actual_type_code=actual_type,
        ), cursor

    def _decode_flat_value(self, actual_type: int, raw: bytes) -> Any:
        if actual_type == 0x00000000:
            return raw != b"\x00"
        if actual_type == 0x00000001:
            return raw[0]
        if actual_type == 0x00000018:
            return struct.unpack("<h", raw)[0]
        if actual_type == 0x00000019:
            return struct.unpack("<H", raw)[0]
        if actual_type == 0x00000002:
            return struct.unpack("<i", raw)[0]
        if actual_type == 0x00000003:
            return struct.unpack("<I", raw)[0]
        if actual_type == 0x00000013:
            return struct.unpack("<q", raw)[0]
        if actual_type == 0x00000005:
            return struct.unpack("<f", raw)[0]
        if actual_type == 0x00000006:
            return struct.unpack("<d", raw)[0]
        if actual_type == 0x00000008:
            return raw.decode("utf-16-le", errors="ignore")
        if actual_type == 0xBBBBBBBB:
            return struct.unpack("<II", raw)
        if actual_type == 0xAAAAAAAA:
            return struct.unpack("<I", raw)[0]
        return raw

    def write_scalar(self, node: ValueNode, value: int | bool) -> None:
        if node.data_offset is None or node.actual_type_code is None:
            raise RuntimeError("Value node is not directly writable")
        packed = self._encode_scalar(node.actual_type_code, value)
        if len(packed) != node.data_size:
            raise RuntimeError("Replacement changed byte width")
        self.raw_data[node.data_offset : node.data_offset + node.data_size] = packed
        node.value = value

    def _encode_scalar(self, actual_type: int, value: int | bool) -> bytes:
        if actual_type == 0x00000000:
            return struct.pack("<?", bool(value))
        if actual_type == 0x00000002:
            return struct.pack("<i", int(value))
        if actual_type == 0x00000003:
            return struct.pack("<I", int(value))
        if actual_type == 0x00000005:
            return struct.pack("<f", float(value))
        raise RuntimeError(f"Unsupported writable scalar type: {TYPE_NAMES.get(actual_type, hex(actual_type))}")
