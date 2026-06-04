#!/usr/bin/env python

import os
import json
import traceback

import uefi_firmware
from uefi_firmware.utils import flatten_firmware_objects

import dictdiffer

# The types set bins various folder representing firmware types
# to the expected 'detected' type from the parser code.
with open('TYPES.json', 'r') as fh:
    TYPES = json.loads(fh.read())

# The files set binds explicit file names to the number of ojects
# detected. Modifications to the codebase should have expected changes
# in the addition/removal of objects.
with open('OBJECTS.json', 'r') as fh:
    OBJECTS = json.loads(fh.read())

class Status(object):
    def __init__(self, code, firmware=None):
        self.code = code
        self.firmware = firmware


def test_file(sample, type_name):
    with open(sample, "rb") as fh:
        sample_data = fh.read()
    parser = uefi_firmware.AutoParser(sample_data)
    if parser.type() is None:
        print("Cannot parse (%s): No matched type." % sample)
        return Status(1)
    if parser.type() != type_name:
        print("Problem parsing (%s): mismatched type " +
            "expected %s, got %s") % (sample, parser.type(), type_name)
        return Status(1)
    try:
        firmware = parser.parse()
    except Exception as e:
        # Wrap 'process' in exception handling for a pretty print.
        print("Exception parsing (%s): (%s)." % (sample, str(e)))
        return Status(1)

    # Check that 'process' does not encounter invalid formats/errors.
    if firmware is None:
        print("Error parsing (%s): failure in process." % (sample))
        return Status(1)

    # Attempt to iterate each of the nested/parsed objects.
    try:
        for _object in firmware.iterate_objects():
            pass
    except Exception as e:
        print("Exception iterating (%s): (%s)." % (sample, str(e)))
        print(traceback.print_exc())
        return Status(1)

    print("Parsing (%s): success" % (sample))
    return Status(0, firmware)


def test_items(sample, firmware):
    if sample not in OBJECTS:
        return Status(0)
    objects = firmware.iterate_objects()
    all_objects = flatten_firmware_objects(objects)
    num_objects = len(all_objects)
    if num_objects != OBJECTS[sample]:
        print("Inconsistency parsing (%s): expected %d objects, found: %d" % (
            sample, OBJECTS[sample], num_objects))
        print("This 'may' be expected if this change improves the object " +
            "discovery/parsing logic.")
        return Status(1)
    print("Listing (%s): item count: %d" % (sample, num_objects))
    return Status(0)

def test_repack(sample, type_name, firmware):
    if not hasattr(firmware, 'build'):
        return Status(0)
    repacked = firmware.build(generate_checksum=True)

    parser = uefi_firmware.AutoParser(repacked)
    if parser.type() is None:
        print("Cannot parse (%s (repacked)): No matched type." % sample)
        return Status(1)
    if parser.type() != type_name:
        print("Problem parsing (%s (repacked)): mismatched type " +
            "expected %s, got %s") % (sample, parser.type(), type_name)
        return Status(1)
    try:
        repacked_firmware = parser.parse()
    except Exception as e:
        # Wrap 'process' in exception handling for a pretty print.
        print("Exception parsing (%s (repacked)): (%s)." % (sample, str(e)))
        return Status(1)

    # Check that 'process' does not encounter invalid formats/errors.
    if repacked_firmware is None:
        print("Error parsing (%s (repacked)): failure in process." % (sample))
        return Status(1)

    repacked_dict = repacked_firmware.to_dict()
    firmware_dict = firmware.to_dict()


    result = dictdiffer.diff(firmware_dict, repacked_dict)

    for (diff, location, change) in dictdiffer.diff(firmware_dict, repacked_dict):
        # We can ignore some size diffs
        if diff == "change" and isinstance(location, list) and location[-1] == "size":
            node = firmware_dict
            for key in location[:-1]:
                node = node[key]
            # we can ignore LZMA section size diffs: our LZMA compression settings may differ
            if 'sectionType' in node and node['type'] == 0x2: # GUID Defined
                if node['data']['guid'] == uefi_firmware.structs.uefi_structs.FIRMWARE_GUIDED_GUIDS['LZMA_COMPRESSED']:
                    continue
            # We can ignore block size changes because of above LZMA compression
            if len(location) >= 3 and location[-3] == "blocks":
                continue
        print("Repacked %s did not match original: %s %s %s" % (sample, diff, location, change))
        return Status(1)

    return Status(0)


def get_files(dir):
    files = []
    for base, dirnames, filenames in os.walk(dir):
        for filename in filenames:
            files.append(os.path.join(base, filename).replace(os.path.sep, '/'))
    return files


if __name__ == "__main__":
    for type_name, samples_dir in TYPES:
        sample_files = get_files(samples_dir)
        for sample in sample_files:
            status = test_file(sample, type_name)
            if status.code > 0:
                exit(status.code)
            firmware = status.firmware
            status = test_items(sample, firmware)
            if status.code > 0:
                exit(status.code)
            status = test_repack(sample, type_name, firmware)
            if status.code > 0:
                exit(status.code)
    exit(0)
