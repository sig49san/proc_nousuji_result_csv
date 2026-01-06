import csv
import sys
import os
import logging

# Files
INPUT_FILE = "../output/intermediate_songs.csv"
OUTPUT_FILE = "../output/result_summary_processed.csv"


def process_options_and_awards(input_path, output_path):
    try:
        with open(input_path, "r", encoding="utf-8") as infile:
            reader = csv.DictReader(infile)
            rows = list(reader)
            original_fields = reader.fieldnames

            # Prepare headers with specific order
            # Add play_format after clear_lamp
            # Add option columns at the end if not present

            new_fields = []
            seen_fields = set()

            for f in original_fields:
                new_fields.append(f)
                seen_fields.add(f)

            extras = ["Left", "Right", "FLIP", "LEGACY", "A-SCR", "clear_award"]
            for e in extras:
                if e not in seen_fields:
                    new_fields.append(e)
                    seen_fields.add(e)

            # Mapping for abbreviations; unknown tokens will be preserved
            mapping = {
                "RAN": "RANDOM",
                "R-RAN": "R-RANDOM",
                "S-RAN": "S-RANDOM",
                "MIR": "MIRROR",
            }

            # Allowed Left/Right tokens after normalization
            allowed_lr = {"RANDOM", "R-RANDOM", "S-RANDOM", "MIRROR"}

            # Ensure warnings are visible when running as a script
            logging.basicConfig(level=logging.WARNING)

            def normalize_lr(token, row_idx=None, row=None):
                """Normalize a Left/Right token.

                - Strip and uppercase the token.
                - Expand known abbreviations via `mapping`.
                - If result is in allowed_lr, return it; otherwise return ''.
                - Log a warning (including row info) when sanitizing an invalid token.
                """
                if not token:
                    return ""

                tok = token.strip().upper()
                tok = mapping.get(tok, tok)

                if tok in allowed_lr:
                    return tok

                # Build minimal row info for logging
                user = ""
                tw = ""
                if isinstance(row, dict):
                    user = row.get("UserName", "")
                    tw = row.get("TwitterID", "")

                logging.warning(
                    "Invalid Left/Right token '%s' at row %s (UserName=%s,TwitterID=%s); sanitizing to empty",
                    token,
                    str(row_idx) if row_idx is not None else "?",
                    user,
                    tw,
                )
                return ""

            # Lamp ranks
            lamp_ranks = {
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
                return lamp_ranks.get(lamp, 0)

            for idx, row in enumerate(rows, start=1):
                # Options parsing
                opts = row.get("options", "")
                opts = opts.replace(".", ",")

                if opts == "OFF":
                    row["Left"] = ""
                    row["Right"] = ""
                    row["FLIP"] = ""
                    row["LEGACY"] = ""
                    row["A-SCR"] = ""
                else:
                    # 1. Flags
                    row["FLIP"] = "FLIP" if "FLIP" in opts else ""
                    row["LEGACY"] = "LEGACY" if "LEGACY" in opts else ""
                    row["A-SCR"] = "A-SCR" if "A-SCR" in opts else ""

                    # 2. Left/Right
                    main_opt = opts.split(",")[0].strip()
                    left_raw, right_raw = "", ""

                    if "/" in main_opt:
                        parts = main_opt.split("/", 1)
                        left_raw = parts[0].strip()
                        right_raw = parts[1].strip()
                    else:
                        left_raw = main_opt
                        right_raw = ""

                    # Normalize Left/Right tokens to allowed set (sanitize invalid)
                    row["Left"] = normalize_lr(left_raw, idx, row)
                    row["Right"] = normalize_lr(right_raw, idx, row)

                # Clear Award Logic
                current_lamp = row.get("clear_lamp", "").strip()
                best_lamp = row.get("best_clear_lamp", "").strip()

                if get_rank(current_lamp) > get_rank(best_lamp):
                    row["clear_award"] = current_lamp
                else:
                    row["clear_award"] = ""

            # Write output
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, "w", encoding="utf-8", newline="") as outfile:
                writer = csv.DictWriter(outfile, fieldnames=new_fields)
                writer.writeheader()
                writer.writerows(rows)

        print(f"Step 2 Complete. Processed {len(rows)} rows.")
        print(f"Output saved to {output_path}")

    except FileNotFoundError:
        print(f"Error: Input file not found at {input_path}")


if __name__ == "__main__":
    # Allow CLI args override
    in_p = sys.argv[1] if len(sys.argv) > 1 else INPUT_FILE
    out_p = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_FILE

    process_options_and_awards(in_p, out_p)
