# Netflix viewing-event cleaning notes

## Source files

- `Netflix title catalog, November 2026.csv` is the title catalog.
- `Netflix viewing events export, 17 Aug to 16 Nov 2026.csv` contains 5,000 viewing events.
- The source CSVs are left unchanged. `clean_viewing_events.py` reads them from the same folder.

## Cleaning decisions

The cleaning script removes an event if:

- its `title_id` is not present in the title catalog;
- `country`, `device_type`, or `watch_seconds` is blank;
- `watch_seconds` exceeds the title's runtime in seconds; or
- `completed` is true while `watch_seconds` is less than the title's full runtime.

Rows are not removed based on date. Valid events are split into two CSVs using November 10, 2026 as the boundary:

- `viewing_events_before_2026-11-10.csv`: events before November 10;
- `viewing_events_on_or_after_2026-11-10.csv`: events on or after November 10.

Both output files retain the viewing-events export's original columns and their order. A blank `runtime_minutes` in the catalog prevents runtime comparisons for that title; those events are kept unless another cleaning rule removes them.

## Issues observed in the source data

- The viewing events include title IDs `TT-0412`, `TT-0347`, and `TT-0588`, which are absent from the title catalog.
- 74 events have no watch time; 49 have no country; 135 have no device type.
- The catalog has 10 titles with no runtime; 104 events reference those titles and cannot be checked against runtime.
- The data includes completed events with watch time below the full title runtime. These are removed as requested.
- The screenshot highlights an event marked complete after 34 seconds for `TT-0105`, whose catalog runtime is 47 minutes.
- The screenshot also highlights event `EV-002303`: member `M-10020` watched `TT-0003` for 85,372 seconds, although its runtime is 96 minutes.

The script prints the actual removal counts and output row counts each time it runs.

## Current run

The script removed 2,941 unique events and retained 2,059:

- 1,911 events before November 10;
- 148 events on or after November 10.

Removal-reason counts were 180 missing-catalog title IDs, 74 blank watch times, 49 blank countries, 135 blank device types, 1,000 watch times above runtime, and 1,607 completed events below full runtime. These reason counts overlap when a row has multiple issues, so they do not sum to the unique removed-row count.
