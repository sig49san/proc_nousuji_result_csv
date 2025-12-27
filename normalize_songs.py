import csv
import shutil
import difflib

# Files
INPUT_FILE = 'result_summary.csv'
OUTPUT_FILE = 'result_summary_processed.csv'
SONG_LIST_FILE = 'song_name_list.txt'

def load_song_names(filepath):
    """Load standardized song names from a file."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]

def get_best_match(name, candidates):
    """
    Find the best match for 'name' in 'candidates' using fuzzy matching.
    Returns the best match from candidates, or the original name if confidence is too low.
    """
    if not candidates:
        return name
        
    # Try finding the best match with a lower cutoff (0.1) to catch "冬霞" -> "冬椿..."
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=0.1)
    
    if matches:
        return matches[0]
    
    # Fallback: substring check
    for cand in candidates:
        if name in cand or cand in name:
            return cand
            
    # If still no match, find max ratio manually to force a match if possible
    # (Optional: only if truly necessary. "make it one of them" implies forced mapping)
    # ratios = [(difflib.SequenceMatcher(None, name, c).ratio(), c) for c in candidates]
    # best_ratio, best_cand = max(ratios, key=lambda x: x[0])
    # if best_ratio > 0: # Even a small overlap
    #     return best_cand
            
    return name

def process_csv(input_path, output_path, song_list_path):
    standard_names = load_song_names(song_list_path)
    print(f"Loaded {len(standard_names)} standard song names: {standard_names}")
    
    with open(input_path, 'r', encoding='utf-8') as infile, \
         open(output_path, 'w', encoding='utf-8', newline='') as outfile:
        
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        
        processed_count = 0
        changed_count = 0
        
        for row in reader:
            original_song = row['song_name']
            normalized_song = get_best_match(original_song, standard_names)
            
            if normalized_song != original_song:
                changed_count += 1
                print(f"Mapped '{original_song}' -> '{normalized_song}'")
                
            row['song_name'] = normalized_song
            writer.writerow(row)
            processed_count += 1
            
    print(f"Processed {processed_count} rows. Normalized {changed_count} entries.")
    print(f"Output saved to {output_path}")

if __name__ == "__main__":
    process_csv(INPUT_FILE, OUTPUT_FILE, SONG_LIST_FILE)
