from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wrd_sandbox.ndf_parser import NdfParser, ValueNode


GLOBALS_PATH = Path("pc/ndf/patchable/misc/globals.ndfbin")
EVERYTHING_PATH = Path("pc/ndf/patchable/gfx/everything.ndfbin")
DEFAULT_SLOT_KEYS = {3, 6, 7, 8, 9, 10, 11, 12, 13}


@dataclass
class ScanSummary:
    map_unlock_matches: int = 0
    deck_rule_matches: int = 0
    max_packs_matches: int = 0
    prototype_matches: int = 0
    fob_supply_matches: int = 0
    default_slot_key_matches: int = 0


def scan_workspace_targets(workspace: Path) -> ScanSummary:
    summary = ScanSummary()
    globals_parser, _ = NdfParser.from_file(workspace / GLOBALS_PATH)
    everything_parser, _ = NdfParser.from_file(workspace / EVERYTHING_PATH)

    for obj in globals_parser.find_objects("TModernWarfareMultiMapInfo"):
        if _scalar_value(obj, "NbMaxPlayers") == 20:
            summary.map_unlock_matches += 1

    deck_objects = everything_parser.find_objects("TShowRoomDeckRuleManager")
    if deck_objects:
        summary.deck_rule_matches = 1
        summary.default_slot_key_matches = len(_slot_matrix_targets(deck_objects[0]))

    for obj in everything_parser.find_objects("TUniteAuSolDescriptor"):
        if _scalar_value(obj, "MaxPacks") is not None:
            summary.max_packs_matches += 1
        if _scalar_value(obj, "IsPrototype") is True:
            summary.prototype_matches += 1

    for obj in everything_parser.find_objects("TModuleModernWarfareSupplyDescriptor"):
        if _scalar_value(obj, "SupplyCapacity") == 16000:
            summary.fob_supply_matches += 1

    return summary


def apply_all_patches(workspace: Path, max_packs_99: bool = False) -> ScanSummary:
    summary = ScanSummary()
    globals_path = workspace / GLOBALS_PATH
    everything_path = workspace / EVERYTHING_PATH

    globals_parser, _ = NdfParser.from_file(globals_path)
    for obj in globals_parser.find_objects("TModernWarfareMultiMapInfo"):
        if _scalar_value(obj, "NbMaxPlayers") == 20:
            globals_parser.write_scalar(obj.properties["NbMinPlayers"].value, 0)
            summary.map_unlock_matches += 1
    globals_parser.write_back(globals_path)

    everything_parser, _ = NdfParser.from_file(everything_path)
    deck_objects = everything_parser.find_objects("TShowRoomDeckRuleManager")
    if deck_objects:
        deck = deck_objects[0]
        everything_parser.write_scalar(deck.properties["DefaultActivationPoints"].value, 900)
        summary.deck_rule_matches = 1
        for slot_value in _slot_matrix_targets(deck):
            everything_parser.write_scalar(slot_value, 9)
            summary.default_slot_key_matches += 1

    for obj in everything_parser.find_objects("TUniteAuSolDescriptor"):
        if max_packs_99 and _scalar_value(obj, "MaxPacks") is not None:
            everything_parser.write_scalar(obj.properties["MaxPacks"].value, 99)
            summary.max_packs_matches += 1
        if _scalar_value(obj, "IsPrototype") is True:
            everything_parser.write_scalar(obj.properties["IsPrototype"].value, False)
            summary.prototype_matches += 1

    for obj in everything_parser.find_objects("TModuleModernWarfareSupplyDescriptor"):
        if _scalar_value(obj, "SupplyCapacity") == 16000:
            everything_parser.write_scalar(obj.properties["SupplyCapacity"].value, 999999)
            summary.fob_supply_matches += 1

    everything_parser.write_back(everything_path)
    return summary


def _scalar_value(obj, property_name: str):
    prop = obj.properties.get(property_name)
    return None if prop is None else prop.value.value


def _slot_matrix_targets(deck_object) -> list[ValueNode]:
    prop = deck_object.properties["DefaultSlotMatrix"].value
    pairs: list[tuple[ValueNode, ValueNode]] = []
    if prop.actual_type_code == 0x00000012:
        pairs = list(prop.items or [])
    elif prop.actual_type_code == 0x00000011:
        for item in prop.items or []:
            if item.actual_type_code == 0x00000022 and item.items:
                pairs.extend(item.items)
    elif prop.actual_type_code == 0x00000022 and prop.items:
        pairs = list(prop.items)

    return [
        value
        for key, value in pairs
        if isinstance(key.value, int) and key.value in DEFAULT_SLOT_KEYS
    ]
