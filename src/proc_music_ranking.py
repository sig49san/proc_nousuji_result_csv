import csv
import collections
import os
import datetime

# Columns for history output (fixed order)
HISTORY_COLUMNS = [
    "submission_date",
    "submission_time",
    "UserName",
    "TwitterID",
    "score",
    "Left",
    "Right",
    "FLIP",
    "LEGACY",
    "A-SCR",
    "play_format",
    "clear_award",
]

# Resolve input file relative to project root (script location)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
INPUT_FILE = os.path.join(PROJECT_ROOT, "output", "result_summary_processed.csv")

# Rank definitions for Clear Award (Same as previous script)
LAMP_RANKS = {
    "F-COMBO": 6,
    "EXH-CLEAR": 5,
    "H-CLEAR": 4,
    "CLEAR": 3,
    "E-CLEAR": 2,
    "A-CLEAR": 1,
    "FAILED": 0,
    "NO PLAY": 0,
    "": 0,
}


def get_rank(lamp):
    return LAMP_RANKS.get(lamp, 0)


def process_ranking(input_file, manual_file=None):
    # Dictionary structure:
    # { guess_song_name: { twitter_id: { record_data } } }
    songs_data = collections.defaultdict(dict)
    # For history output: list of rows per song (preserve full row dict)
    songs_history = collections.defaultdict(list)

    # Read main processed CSV
    all_rows = []
    fieldnames = []
    if os.path.exists(input_file):
        with open(input_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames or []
            all_rows.extend(list(reader))

    # Read manual users file if provided or exists
    if manual_file is None:
        manual_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "input", "manual_users.csv"
        )
    if os.path.exists(manual_file):
        with open(manual_file, "r", encoding="utf-8") as mf:
            mreader = csv.DictReader(mf)
            mfields = mreader.fieldnames or []
            # extend fieldnames to include any extra manual columns while preserving order
            for f in mfields:
                if f not in fieldnames:
                    fieldnames.append(f)
            for mrow in mreader:
                # Ensure keys exist for expected columns
                all_rows.append(mrow)

    # Process rows
    for row in all_rows:
        song = row.get("guess_song_name", "").strip()
        twitter_id = row.get("TwitterID", "").strip()

        # Skip invalid rows
        if not song or not twitter_id:
            continue

        # Append to history using fixed HISTORY_COLUMNS order; normalize missing keys to ''
        normalized_row = {k: row.get(k, "") for k in HISTORY_COLUMNS}
        songs_history[song].append(normalized_row)

        score_raw = str(row.get("score", "")).strip()
        new_score = int(score_raw) if score_raw.isdigit() else 0
        new_award = row.get("clear_award", "")

        # Columns to track for best-record output
        data = {
            "UserName": row.get("UserName", ""),
            "TwitterID": twitter_id,
            "score": new_score,
            "Left": row.get("Left", ""),
            "Right": row.get("Right", ""),
            "FLIP": row.get("FLIP", ""),
            "LEGACY": row.get("LEGACY", ""),
            "A-SCR": row.get("A-SCR", ""),
            "play_format": row.get("play_format", ""),
            "clear_award": new_award,
        }

        if twitter_id not in songs_data[song]:
            songs_data[song][twitter_id] = data
        else:
            current_record = songs_data[song][twitter_id]
            if new_score > current_record["score"]:
                current_record["score"] = new_score
                current_record["Left"] = row.get("Left", "")
                current_record["Right"] = row.get("Right", "")
                current_record["FLIP"] = row.get("FLIP", "")
                current_record["LEGACY"] = row.get("LEGACY", "")
                current_record["A-SCR"] = row.get("A-SCR", "")
                current_record["play_format"] = row.get("play_format", "")
                current_record["UserName"] = row.get("UserName", "")
            if get_rank(new_award) > get_rank(current_record.get("clear_award", "")):
                current_record["clear_award"] = new_award
    # Output files
    output_columns = [
        "UserName",
        "TwitterID",
        "score",
        "Left",
        "Right",
        "FLIP",
        "LEGACY",
        "A-SCR",
        "play_format",
        "clear_award",
    ]

    # Determine project root and ensure Result directory exists
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    result_dir = os.path.join(project_root, "Result")
    os.makedirs(result_dir, exist_ok=True)

    # Timestamp for this run (same timestamp for all files in one execution)
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

    for song_name, users in songs_data.items():
        # Sanitize filename just in case
        safe_name = song_name.replace("/", "_")  # Basic safety
        filename = f"{safe_name}_{timestamp}.csv"
        filepath = os.path.join(result_dir, filename)

        # Sort by score descending
        sorted_users = sorted(users.values(), key=lambda x: x["score"], reverse=True)

        with open(filepath, "w", encoding="utf-8", newline="") as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_columns)
            writer.writeheader()
            writer.writerows(sorted_users)

        print(f"Created {filepath} with {len(sorted_users)} records.")

        # Also create history file for this song
        history_filename = f"{safe_name}_history_{timestamp}.csv"
        history_path = os.path.join(result_dir, history_filename)
        # If we have recorded history rows, write them sorted by date+time
        rows_hist = songs_history.get(song_name, [])
        if rows_hist:
            # Use fixed HISTORY_COLUMNS as header and sort by submission_date + submission_time
            hist_header = HISTORY_COLUMNS

            def hist_sort_key(r):
                return (r.get("submission_date", ""), r.get("submission_time", ""))

            rows_hist_sorted = sorted(rows_hist, key=hist_sort_key)
            with open(history_path, "w", encoding="utf-8", newline="") as hout:
                hwriter = csv.DictWriter(hout, fieldnames=hist_header)
                hwriter.writeheader()
                hwriter.writerows(rows_hist_sorted)
            print(f"Created {history_path} with {len(rows_hist_sorted)} records.")


if __name__ == "__main__":
    process_ranking(INPUT_FILE)
