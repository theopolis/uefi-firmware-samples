#!/usr/bin/env python

import os

import uefi_firmware
from uefi_firmware.utils import flatten_firmware_objects

# The types set bins various folder representing firmware types
# to the expected 'detected' type from the parser code.
TYPES = {
    "DellPFS": "dell_pfs",
    "UEFIFirmwareVolume": "uefi_volume",
    "FlashDescriptor": "flash",
    "IntelME": "intel_me",
    "EFICapsule": "efi_capsule",
}

# The files set binds explicit file names to the number of ojects
# detected. Modifications to the codebase should have expected changes
# in the addition/removal of objects.
FILES = {
    "dell_pfs/M4600A16.pfs": 2723,
    "flash/Latitude-E6410-A10.flash": 1186,
    "intel_me/dell_1176upd.me": 2,
    "uefi_volume/MINNOW1.fd": 664,
    "efi_capsule/MBP111_0138_B16_LOCKED.scap": 3043,
}

class Status(object):
    def __init__(self, code, firmware=None):
        self.code = code
        self.firmware = firmware


def test_file(sample, type_name):
    with open(sample, "rb") as fh:
        sample_data = fh.read()
    parser = uefi_firmware.AutoParser(sample_data)
    if parser.type() is None:
        print ("Cannot parse (%s): No matched type." % sample)
        return Status(1)
    if parser.type() != type_name:
        print ("Problem parsing (%s): mismatched type " +
            "expected %s, got %s") % (sample, parser.type(), type_name)
        return Status(1)
    try:
        firmware = parser.parse()
    except Exception as e:
        # Wrap 'process' in exception handling for a pretty print.
        print ("Exception parsing (%s): (%s)." % (sample, str(e)))
        return Status(1)

    # Check that 'process' does not encounter invalid formats/errors.
    if firmware is None:
        print ("Error parsing (%s): failure in process." % (sample))
        return Status(1)

    # Attempt to iterate each of the nested/parsed objects.
    try:
        for _object in firmware.iterate_objects():
            pass
    except Exception as e:
        print ("Exception iterating (%s): (%s)." % (sample, str(e)))
        return Status(1)

    print ("Parsing (%s): success" % (sample))
    return Status(0, firmware)


def test_items(sample, firmware):
    if sample not in FILES:
        return Status(0)
    objects = firmware.iterate_objects()
    all_objects = flatten_firmware_objects(objects)
    num_objects = len(all_objects)
    if num_objects != FILES[sample]:
        print ("Inconsistency parsing (%s): expected %d objects, found: %d" % (
            sample, FILES[sample], num_objects))
        print ("This 'may' be expected if this change improves the object " +
            "discovery/parsing logic.")
        return Status(1)
    print ("Listing (%s): item count: %d" % (sample, num_objects))
    return Status(0)


def get_files(dir):
    files = []
    for base, dirnames, filenames in os.walk(dir):
        for filename in filenames:
            files.append(os.path.join(base, filename))
    return files      


if __name__ == "__main__":
    for type_name, samples_dir in TYPES.iteritems():
        sample_files = get_files(samples_dir)
        for sample in sample_files:
            status = test_file(sample, type_name)
            if status.code > 0:
                exit(status.code)
            status = test_items(sample, status.firmware)
            if status.code > 0:
                exit(status.code)
    exit(0)
