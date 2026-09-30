# Sample Files for Manual Testing

- `sample_assignment_valid.pdf` — a minimal but real PDF. Should upload successfully.
- `sample_assignment_too_large.pdf` — ~11MB PDF. Should be rejected with `413 FILE_TOO_LARGE` against an assignment with a 10MB (or lower) limit.
- `sample_bad_file.exe` — not an allowed type. Should be rejected with `415 INVALID_FILE_TYPE`.

Use these while working through `docs/LOCAL_SETUP_WALKTHROUGH.md`.
