# GenSIRO48 PTseq Scripts

This repository is the Git-managed conversion of the previous file-name-based script archive.

Product lines:

- `extraction/`: PTseq extraction scripts.
- `libraryprep/library/`: common library-only scripts.
- `libraryprep/full/`: library + pooling + DNB full workflow scripts, grouped by platform.
- `libraryprep/sequencingprep/`: sequencing-prep-only scripts, grouped by platform.
- `pcr_methods/`: PCR method XML files used by the scripts.
- `tests/`: robot or parameter isolation test scripts.

Version rule:

- Stable historical versions are Git tags, not `vxxx` filenames.
- Current runnable script names are kept stable inside each product-line folder.
- New experiments should use `test/...` branches or `TEST_` script names until confirmed.

Useful commands:

```bash
git tag --list
git log --oneline --decorate --all
git show libraryprep-g99-v7:libraryprep/full/G99/SIRO48-PTseq-Library-pooling-DNB-G99/SIRO48-PTseq-Library-pooling-DNB-G99.py
git diff libraryprep-g99-v11 libraryprep-g99-v12-current -- libraryprep/full/G99/SIRO48-PTseq-Library-pooling-DNB-G99/SIRO48-PTseq-Library-pooling-DNB-G99.py
```
