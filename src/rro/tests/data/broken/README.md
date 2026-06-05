# Negative GTFS fixtures

Deliberately corrupted feeds used to assert the ingestion failure path
(handbook §8.4): a feed missing required files or with broken referential
integrity must raise before graph build and map to CLI exit `2`.

Populated alongside the `data/ingest.py` validation implementation.
