#!/usr/bin/env python

import os

from uefi_firmware import uefi
from uefi_firmware.misc import checker

types = {
    "DellPFS": "dell_pfs",
    "UEFIFirmwareVolume": "uefi_volume",
    "FlashDescriptor": "flash",
}

def test_files(files, type_name):
    for sample in files:
        with open(sample, "rb") as fh:
            sample_data = fh.read()
        matched_type = None
        matched_parser = None
        for tester in checker.TESTERS:
            if tester().match(sample_data[:100]):
                matched_type = tester().name
                matched_parser = tester().parser
                break
        if matched_type is None:
            print "Cannot parse (%s): No matched type." % sample
            return 1
        if matched_type != type_name:
            print ("Problem parsing (%s): mismatched type " +
                "expected %s, got %s") % (sample, matched_type, type_name)
            return 1
        firmware = matched_parser(sample_data)
        try:
            status = firmware.process()
        except Exception as e:
            print "Exception parsing (%s): (%s)." % (sample, str(e))
            return 1

        if not status:
            print "Error parsing (%s): failure in process." % (sample)
            return 1
        print "Parsing (%s): success" % (sample)
    return 0

def get_files(dir):
    files = []
    for base, dirnames, filenames in os.walk(dir):
        for filename in filenames:
            files.append(os.path.join(base, filename))
    return files      

if __name__ == "__main__":
    for type_name, samples_dir in types.iteritems():
        sample_files = get_files(samples_dir)
        status = test_files(sample_files, type_name)
        if status > 0:
            exit(status)
    exit(0)
