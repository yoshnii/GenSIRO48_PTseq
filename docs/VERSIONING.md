# Versioning Model

The original folders are left untouched. This repository copies the script content into stable canonical paths and uses Git history plus tags to represent older `vxxx` files.

## Directory Lines

- `extraction/`
- `libraryprep/G99/`
- `libraryprep/E25/`
- `libraryprep/2002000/`

## Tag Naming

- `received-extraction-baseline`
- `received-libraryprep-g99-baseline`
- `extraction-v1-current`
- `libraryprep-g99-v1`, `libraryprep-g99-v3`, ...
- `libraryprep-g99-v12-current`
- `libraryprep-e25-v1-current`
- `libraryprep-2002000-v1-current`

## Branch Rule

Keep `main` as the integrated current baseline. Use branches for work in progress, for example:

```bash
git switch -c test/g99-bead-transfer
git switch -c fix/g99-la-beads
```

After a test is confirmed, commit the production change on a `fix/...` branch or directly on `main`, then tag the accepted version.

