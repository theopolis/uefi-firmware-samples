## uefi-firmware-samples

This is a companion repository for [uefi-firmware-parser](https://github.com/theopolis/uefi-firmware-parser), it exists to store large UEFI-related firmware objects used during unittesting.

### Types of tests

#### Object identification

The `uefi-firmware-parser`: `uefi_firmware` Python module attempts to identify an input blob. The module is mostly organized into classes that represent object types. A subset of those can be provided as input.

There are several folders in this repository, e.g., `efi_capsule`, wherein each file must identify as a `EFICapsule` type. These simple folder-to-class relationships are stored in `TYPES.json`.

#### Object counting

A simple 'count' is used to protect against regressions that prevent parsing. If a change is introduced that alters the count of embedded objects expected from a sample the corresponding file must be updated in `OBJECTS.json`.

### Samples

The samples here are NOT provided for distribution, only for testing.

To add a new sample of an existing type add the binary object and update `OBJECTS.json`.
