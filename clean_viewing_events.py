import csv
from collections import Counter
from datetime import date
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
CATALOG_FILE = BASE_DIR / "Netflix title catalog, November 2026.csv"
EVENTS_FILE = BASE_DIR / "Netflix viewing events export, 17 Aug to 16 Nov 2026.csv"
CUTOFF_DATE = date(2026, 11, 10)
COMPLETION_THRESHOLD_PERCENT = 90
OVERRUN_CAP_MULTIPLIER = 2
BEFORE_FILE = BASE_DIR / "viewing_events_before_2026-11-10.csv"
ON_OR_AFTER_FILE = BASE_DIR / "viewing_events_on_or_after_2026-11-10.csv"

EVENT_COLUMNS = (
    "event_id",
    "member_id",
    "title_id",
    "event_datetime",
    "watch_seconds",
    "completed",
    "device_type",
    "country",
    "profile_type",
)
CATALOG_COLUMNS = ("title_id", "runtime_minutes")


def read_csv(path):
    with path.open("r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"{path.name} is missing a header row")
        return reader.fieldnames, list(reader)


def require_columns(path, actual_columns, required_columns):
    missing = [column for column in required_columns if column not in actual_columns]
    if missing:
        raise ValueError(f"{path.name} is missing required columns: {', '.join(missing)}")


def parse_integer(value, field, event_id):
    try:
        parsed = int(value.strip())
    except ValueError as error:
        raise ValueError(f"Invalid {field} for event {event_id}: {value!r}") from error
    if parsed < 0:
        raise ValueError(f"Negative {field} for event {event_id}: {value!r}")
    return parsed


def parse_completed(value, event_id):
    normalized = value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"Invalid completed value for event {event_id}: {value!r}")


def write_csv(path, columns, rows):
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    catalog_columns, catalog_rows = read_csv(CATALOG_FILE)
    require_columns(CATALOG_FILE, catalog_columns, CATALOG_COLUMNS)
    event_columns, event_rows = read_csv(EVENTS_FILE)
    require_columns(EVENTS_FILE, event_columns, EVENT_COLUMNS)

    titles = {}
    for row in catalog_rows:
        title_id = row["title_id"].strip()
        if title_id in titles:
            raise ValueError(f"Duplicate title_id in catalog: {title_id}")
        runtime_text = row["runtime_minutes"].strip()
        titles[title_id] = (
            parse_integer(runtime_text, "runtime_minutes", title_id)
            if runtime_text
            else None
        )

    kept_before = []
    kept_on_or_after = []
    removal_counts = Counter()
    adjustment_counts = Counter()
    removed_rows = 0
    unknown_runtime_rows = 0

    for row in event_rows:
        event_id = row["event_id"].strip()
        title_id = row["title_id"].strip()
        watch_text = row["watch_seconds"].strip()
        reasons = []

        if title_id not in titles:
            reasons.append("title_id_not_in_catalog")

        if not watch_text:
            reasons.append("missing_watch_seconds")

        event_date = date.fromisoformat(row["event_datetime"].strip())
        completed = parse_completed(row["completed"], event_id)
        watch_seconds = (
            parse_integer(watch_text, "watch_seconds", event_id)
            if watch_text
            else None
        )

        runtime_minutes = titles.get(title_id)
        if title_id in titles and runtime_minutes is None:
            unknown_runtime_rows += 1
        elif runtime_minutes is not None and watch_seconds is not None:
            runtime_seconds = runtime_minutes * 60
            if watch_seconds > runtime_seconds * OVERRUN_CAP_MULTIPLIER:
                row["watch_seconds"] = str(runtime_seconds)
                watch_seconds = runtime_seconds
                adjustment_counts["watch_seconds_capped"] += 1
            if (
                completed
                and watch_seconds * 100
                < runtime_seconds * COMPLETION_THRESHOLD_PERCENT
            ):
                row["completed"] = "False"
                adjustment_counts["completed_set_false_below_threshold"] += 1

        if reasons:
            removed_rows += 1
            removal_counts.update(reasons)
            continue

        if event_date < CUTOFF_DATE:
            kept_before.append(row)
        else:
            kept_on_or_after.append(row)

    write_csv(BEFORE_FILE, event_columns, kept_before)
    write_csv(ON_OR_AFTER_FILE, event_columns, kept_on_or_after)

    print(f"Input events: {len(event_rows)}")
    print(f"Removed events (unique rows): {removed_rows}")
    for reason, count in sorted(removal_counts.items()):
        print(f"  {reason}: {count}")
    print("Adjusted events:")
    for adjustment, count in sorted(adjustment_counts.items()):
        print(f"  {adjustment}: {count}")
    print(f"Events with missing catalog runtime (runtime checks skipped): {unknown_runtime_rows}")
    print(f"Before {CUTOFF_DATE}: {len(kept_before)} -> {BEFORE_FILE.name}")
    print(f"On/after {CUTOFF_DATE}: {len(kept_on_or_after)} -> {ON_OR_AFTER_FILE.name}")


if __name__ == "__main__":
    main()
