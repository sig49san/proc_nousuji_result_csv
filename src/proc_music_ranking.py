import csv
import collections
import os

INPUT_FILE = '../output/result_summary_processed.csv'

# Rank definitions for Clear Award (Same as previous script)
LAMP_RANKS = {
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

def get_rank(lamp):
    return LAMP_RANKS.get(lamp, 0)

def process_ranking(input_file):
    # Dictionary structure:
    # { guess_song_name: { twitter_id: { record_data } } }
    songs_data = collections.defaultdict(dict)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            song = row['guess_song_name']
            twitter_id = row['TwitterID']
            
            # Skip invalid rows
            if not song:
                continue
                
            new_score = int(row['score']) if row['score'].isdigit() else 0
            new_award = row.get('clear_award', '')
            
            # Columns to track
            data = {
                'UserName': row['UserName'],
                'TwitterID': twitter_id,
                'score': new_score,
                'Left': row['Left'],
                'Right': row['Right'],
                'FLIP': row['FLIP'],
                'LEGACY': row['LEGACY'],
                'A-SCR': row['A-SCR'],
                'clear_award': new_award
            }
            
            if twitter_id not in songs_data[song]:
                # New user for this song
                songs_data[song][twitter_id] = data
            else:
                # User exists, check for updates
                current_record = songs_data[song][twitter_id]
                
                # Check Score Update
                if new_score > current_record['score']:
                    # Update score and options
                    current_record['score'] = new_score
                    current_record['Left'] = row['Left']
                    current_record['Right'] = row['Right']
                    current_record['FLIP'] = row['FLIP']
                    current_record['LEGACY'] = row['LEGACY']
                    current_record['A-SCR'] = row['A-SCR']
                    current_record['UserName'] = row['UserName'] # Update username too just in case
                
                # Check Clear Award Update
                # Only update if new award is better than current stored award
                if get_rank(new_award) > get_rank(current_record['clear_award']):
                     current_record['clear_award'] = new_award
                     
    # Output files
    output_columns = ['UserName', 'TwitterID', 'score', 'Left', 'Right', 'FLIP', 'LEGACY', 'A-SCR', 'clear_award']
    
    for song_name, users in songs_data.items():
        # Sanitize filename just in case
        safe_name = song_name.replace('/', '_') # Basic safety
        filename = f"{safe_name}.csv"
        
        # Sort by score descending? User didn't specify sort order but ranking implies sorting.
        # usually ranking is sorted. I will sort by score descending.
        sorted_users = sorted(users.values(), key=lambda x: x['score'], reverse=True)
        
        with open(filename, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=output_columns)
            writer.writeheader()
            writer.writerows(sorted_users)
            
        print(f"Created {filename} with {len(sorted_users)} records.")

if __name__ == "__main__":
    process_ranking(INPUT_FILE)
