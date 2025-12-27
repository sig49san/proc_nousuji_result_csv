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
        fieldnames = reader.fieldnames + ['guess_song_name', 'Left', 'Right', 'FLIP', 'LEGACY', 'A-SCR', 'clear_award']
        
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
                
            row['guess_song_name'] = normalized_song
            # row['song_name'] = normalized_song # Keep original song name as requested
            
            # Options parsing
            opts = row.get('options', '')
            opts = opts.replace('.',',')
            
            if opts == 'OFF':
                row['Left'] = ''
                row['Right'] = ''
                row['FLIP'] = ''
                row['LEGACY'] = ''
                row['A-SCR'] = ''
            else:
                # 1. Flags
                row['FLIP'] = 'FLIP' if 'FLIP' in opts else ''
                row['LEGACY'] = 'LEGACY' if 'LEGACY' in opts else ''
                row['A-SCR'] = 'A-SCR' if 'A-SCR' in opts else ''
                
                # 2. Left/Right
                # Take the first part before any comma
                main_opt = opts.split(',')[0].strip()
                left_raw, right_raw = '', ''
                
                if '/' in main_opt:
                    parts = main_opt.split('/', 1)
                    left_raw = parts[0].strip()
                    right_raw = parts[1].strip()
                else:
                    left_raw = main_opt
                    right_raw = '' # Or should it be empty? Logic says "Other -> Empty", so if it was 'OFF' or 'RANDOM' (full) it defaults to empty unless matched? 
                    # Wait, if main_opt is 'OFF', it goes to 'Other' -> Empty. Correct.
                
                mapping = {
                    'RAN': 'RANDOM',
                    'R-RAN': 'R-RANDOM',
                    'S-RAN': 'S-RANDOM',
                    'MIR': 'MIRROR'
                }
                
                row['Left'] = mapping.get(left_raw, '')
                row['Right'] = mapping.get(right_raw, '')

            # Clear Award Logic
            # Rank: F-COMBO > EXH-CLEAR > H-CLEAR > CLEAR > E-CLEAR > A-CLEAR > FAILED = NO PLAY
            lamp_ranks = {
                'F-COMBO': 6,
                'EXH-CLEAR': 5,
                'H-CLEAR': 4,
                'CLEAR': 3,
                'E-CLEAR': 2,
                'A-CLEAR': 1,
                'FAILED': 0,
                'NO PLAY': 0,
                '': 0
            }
            
            # Helper to get rank, default to 0 if unknown
            def get_rank(lamp):
                return lamp_ranks.get(lamp, 0)

            current_lamp = row.get('clear_lamp', '').strip()
            best_lamp = row.get('best_clear_lamp', '').strip()
            
            if get_rank(current_lamp) > get_rank(best_lamp):
                row['clear_award'] = current_lamp
            else:
                row['clear_award'] = ''

            writer.writerow(row)
            processed_count += 1
            
    print(f"Processed {processed_count} rows. Normalized {changed_count} entries.")
    print(f"Output saved to {output_path}")

if __name__ == "__main__":
    process_csv(INPUT_FILE, OUTPUT_FILE, SONG_LIST_FILE)
