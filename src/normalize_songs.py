import csv
import difflib
import sys
import os
import json

# Files
INPUT_FILE = "../input/result_summary.csv"
OUTPUT_FILE = "../output/intermediate_songs.csv"
# Prefer JSON song list (selected_songs), fallback to text list
SONG_LIST_FILE = "../input/song_list.json"
SONG_LIST_TXT_FALLBACK = "../input/song_name_list.txt"


def load_song_names(filepath_json, fallback_txt=None):
    """Load standardized song names. Try JSON `selected_songs` first, then fallback to txt list."""
    names = []
    # Try JSON first
    try:
        if filepath_json and os.path.exists(filepath_json):
            with open(filepath_json, "r", encoding="utf-8") as f:
                data = json.load(f)
            songs = data.get("selected_songs") or []
            for s in songs:
                name = s.get("song_name") if isinstance(s, dict) else None
                if name:
                    names.append(str(name).strip())
            if names:
                return names
    except Exception:
        # If JSON is malformed or missing, fall through to txt
        pass

    # Fallback to txt file list
    txt_path = fallback_txt or SONG_LIST_TXT_FALLBACK
    try:
        if txt_path and os.path.exists(txt_path):
            with open(txt_path, "r", encoding="utf-8") as f:
                return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        pass

    print(f"Warning: No song list found at {filepath_json} or {txt_path}")
    return []


def get_best_match(name, candidates):
    """
    Find the best match for 'name' in 'candidates' using fuzzy matching.
    """
    if not candidates:
        return name

    # Try finding the best match with a lower cutoff (0.1)
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=0.1)

    if matches:
        return matches[0]

    # Fallback: substring check
    for cand in candidates:
        if name in cand or cand in name:
            return cand

    return name


def process_songs(input_path, output_path, song_list_path):
    # song_list_path may be a JSON path; provide fallback txt constant
    standard_names = load_song_names(song_list_path, SONG_LIST_TXT_FALLBACK)
    print(f"Loaded {len(standard_names)} standard song names.")

    try:
        with open(input_path, "r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)
            original_fields = reader.fieldnames

            # Construct new field order:
            # - insert 'guess_song_name' after 'song_name'
            # - insert 'play_format' after 'clear_lamp'
            new_fields = []
            # If fields already contain our new columns, keep original order
            if "guess_song_name" in original_fields or "play_format" in original_fields:
                new_fields = original_fields
            else:
                for f in original_fields:
                    new_fields.append(f)
                    if f == "song_name":
                        new_fields.append("guess_song_name")
                    if f == "clear_lamp":
                        new_fields.append("play_format")

                # Safety fallback if expected insertions didn't occur
                if "guess_song_name" not in new_fields:
                    new_fields.append("guess_song_name")
                if "play_format" not in new_fields:
                    new_fields.append("play_format")

            changed_count = 0
            for row in rows:
                original_song = row["song_name"]
                normalized_song = get_best_match(original_song, standard_names)

                if normalized_song != original_song:
                    changed_count += 1

                row["guess_song_name"] = normalized_song
                # Ensure play_format exists and is an empty string
                row["play_format"] = ""

            # Write output
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8", newline="") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=new_fields)
                writer.writeheader()
                writer.writerows(rows)

        print(
            f"Step 1 Complete. Processed {len(rows)} rows. Mapped {changed_count} songs."
        )
        print(f"Output saved to {output_path}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")


if __name__ == "__main__":
    # Allow CLI args override
    in_p = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    out_p = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILE
    list_p = sys.argv[3] if len(sys.argv) > 3 else SONG_LIST_FILE

    process_songs(in_p, out_p, list_p)
