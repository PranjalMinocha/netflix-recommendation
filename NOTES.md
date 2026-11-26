# Netflix viewing-event cleaning notes

## Source files

- `Netflix title catalog, November 2026.csv` is the title catalog.
- `Netflix viewing events export, 17 Aug to 16 Nov 2026.csv` contains 5,000 viewing events.
- The source CSVs are left unchanged. `clean_viewing_events.py` reads them from the same folder.

## Cleaning decisions

The cleaning script removes an event if:

- its `title_id` is not present in the title catalog;
- `watch_seconds` is blank.

Blank `country` and `device_type` values are preserved. For titles with a known runtime:

- watch times greater than twice the runtime are capped at the title runtime; smaller overruns are preserved;
- if `completed` is true but watch time is below 90% of runtime, `completed` is changed to false and the event is kept.

Rows are not removed based on date. Valid events are split into two CSVs using November 10, 2026 as the boundary:

- `viewing_events_before_2026-11-10.csv`: events before November 10;
- `viewing_events_on_or_after_2026-11-10.csv`: events on or after November 10.

Both output files retain the viewing-events export's original columns and their order. A blank `runtime_minutes` in the catalog prevents runtime comparisons for that title; those events are kept unless another cleaning rule removes them.

## Issues observed in the source data

- The viewing events include title IDs `TT-0412`, `TT-0347`, and `TT-0588`, which are absent from the title catalog.
- 74 events have no watch time; 49 have no country; 135 have no device type.
- The catalog has 10 titles with no runtime; 104 events reference those titles and cannot be checked against runtime.
- Some completed events have watch times below runtime; those below 90% of runtime are retained with `completed` changed to false.
- The screenshot highlights an event marked complete after 34 seconds for `TT-0105`, whose catalog runtime is 47 minutes.
- The screenshot also highlights event `EV-002303`: member `M-10020` watched `TT-0003` for 85,372 seconds, although its runtime is 96 minutes.

The script prints removal counts, adjustment counts, and output row counts each time it runs.

## Current run

Running `python clean_viewing_events.py` removed 249 unique events and retained 4,751:

- 4,404 events before November 10;
- 347 events on or after November 10.

The removal-reason counts were 180 events with missing catalog title IDs and 74 with blank watch times; five events matched both reasons. The script set `completed` to false for 1,477 events and capped watch time for 183 events. Runtime checks were skipped for 104 events whose catalog title has no runtime. The command prints current counts each time it runs.
