import os
import json
import csv
import datetime


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
INPUT_CSV = os.path.join(PROJECT_ROOT, 'output', 'result_summary_processed.csv')
INPUT_JSON = os.path.join(PROJECT_ROOT, 'input', 'song_list.json')
RESULT_DIR = os.path.join(PROJECT_ROOT, 'Result')
# Output filename will include timestamp per run
timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
OUTPUT_FILE = os.path.join(RESULT_DIR, f'GrandMaster_{timestamp}.csv')


def load_song_list(json_path):
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    songs = data.get('selected_songs', [])
    # map song_name -> song_no, collect chart_notes by song_no
    name_to_no = {}
    notes_by_no = {}
    song_nos = []
    for s in songs:
        no = s.get('song_no')
        name = s.get('song_name')
        notes = s.get('chart_notes', 0)
        if no is None or name is None:
            continue
        name_to_no[name] = no
        notes_by_no[no] = notes
        song_nos.append(no)
    song_nos = sorted(song_nos)
    return name_to_no, notes_by_no, song_nos


def build_grandmaster(input_csv, input_json, output_file):
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    name_to_no, notes_by_no, song_nos = load_song_list(input_json)

    users = {}
    # Collect history entries keyed by Tweet_URL (if present) or generated unique key
    history_entries = {}

    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            twitter_id = row.get('TwitterID', '').strip()
            if not twitter_id:
                continue
            user_name = row.get('UserName', '').strip()
            guess_song = row.get('guess_song_name', '').strip()
            score_raw = row.get('score', '').strip()
            try:
                score = int(score_raw) if score_raw.isdigit() else 0
            except Exception:
                score = 0
            comment = row.get('Post_Content', '').strip()
            # capture submission date/time for history (prefer latest)
            sub_date = row.get('submission_date', '').strip()
            sub_time = row.get('submission_time', '').strip()

            # Only consider songs that are in the selected list
            if guess_song not in name_to_no:
                continue
            song_no = name_to_no[guess_song]

            if twitter_id not in users:
                users[twitter_id] = {
                    'UserName': user_name,
                    'SNS': twitter_id,
                    'scores': {},  # song_no -> best score
                    'comments': [],
                    'last_submission_date': sub_date,
                    'last_submission_time': sub_time
                }
            user = users[twitter_id]
            # keep first seen UserName if empty later rows
            if not user['UserName'] and user_name:
                user['UserName'] = user_name

            # update best score per song
            prev = user['scores'].get(song_no, -1)
            if score > prev:
                user['scores'][song_no] = score

            # collect comments (avoid exact duplicates)
            if comment:
                if comment not in user['comments']:
                    user['comments'].append(comment)

            # update last submission date/time to the latest seen
            if sub_date:
                # compare tuple (date, time)
                prev_date = user.get('last_submission_date', '')
                prev_time = user.get('last_submission_time', '')
                if (sub_date, sub_time) > (prev_date, prev_time):
                    user['last_submission_date'] = sub_date
                    user['last_submission_time'] = sub_time

            # Build history entry per Tweet_URL; if Tweet_URL missing, create unique key
            tweet_url = row.get('Tweet_URL', '').strip()
            key = tweet_url if tweet_url else f"{twitter_id}|{sub_date}|{sub_time}|{len(history_entries)}"
            if key not in history_entries:
                history_entries[key] = {
                    'submission_date': sub_date,
                    'submission_time': sub_time,
                    'UserName': user_name,
                    'SNS': twitter_id,
                    'comments': [],
                    'rates': {}
                }
            hent = history_entries[key]
            if comment and comment not in hent['comments']:
                hent['comments'].append(comment)
            # compute rate for this song_no and store
            if guess_song in name_to_no:
                no = name_to_no[guess_song]
                notes = notes_by_no.get(no, 0)
                try:
                    rate = score / (notes * 2) if notes else 0.0
                except Exception:
                    rate = 0.0
                hent['rates'][no] = rate

    # Prepare header (add total_score after song columns)
    header = ['UserName'] + [f'song_no{no}' for no in song_nos] + ['total_score', 'SNS', 'Comment']

    # Build rows with numeric total_score for sorting
    rows = []
    for twitter_id, u in users.items():
        row_vals = [u.get('UserName', '')]
        total = 0.0
        per_rates = []
        for no in song_nos:
            score = u['scores'].get(no)
            notes = notes_by_no.get(no, 0)
            if score is None or notes == 0:
                rate = 0.0
                per_rates.append(rate)
            else:
                rate = score / (notes * 2)
                per_rates.append(rate)
            total += rate
        # row_vals will contain formatted rate strings (4 decimal places)
        row_vals += [f'{r:.4f}' if r != 0.0 else '' for r in per_rates]
        row_vals.append(total)
        row_vals.append(u.get('SNS', ''))
        comment_text = ' | '.join(u['comments']) if u['comments'] else ''
        row_vals.append(comment_text)
        rows.append(row_vals)

    # Sort by total_score (index after UserName and song columns)
    total_idx = 1 + len(song_nos)
    rows.sort(key=lambda r: r[total_idx], reverse=True)

    # Write output CSV, formatting total_score to 4 decimals
    with open(output_file, 'w', encoding='utf-8', newline='') as out:
        writer = csv.writer(out)
        writer.writerow(header)
        for r in rows:
            # format total_score to 4 decimals string
            formatted = list(r)
            formatted[total_idx] = f'{formatted[total_idx]:.4f}'
            writer.writerow(formatted)

    print(f'Created {output_file} with {len(users)} records.')

    # Also write a history file per tweet (do not collapse same user; merge rows with same Tweet_URL)
    history_file = os.path.join(RESULT_DIR, f'GrandMaster_history_{timestamp}.csv')
    history_header = ['submission_date', 'submission_time', 'UserName'] + [f'song_no{no}' for no in song_nos] + ['total_score', 'SNS', 'Comment']
    # Sort history entries by submission_date then submission_time
    sorted_entries = sorted(history_entries.values(), key=lambda e: (e.get('submission_date',''), e.get('submission_time','')))
    with open(history_file, 'w', encoding='utf-8', newline='') as hf:
        hwriter = csv.writer(hf)
        hwriter.writerow(history_header)
        for hent in sorted_entries:
            row_vals = [hent.get('submission_date',''), hent.get('submission_time',''), hent.get('UserName','')]
            total = 0.0
            per_rates = []
            for no in song_nos:
                rate = hent['rates'].get(no)
                if rate is None:
                    per_rates.append('')
                else:
                    per_rates.append(f'{rate:.4f}')
                    total += rate
            row_vals += per_rates
            row_vals.append(f'{total:.4f}')
            row_vals.append(hent.get('SNS',''))
            comment_text = ' | '.join(hent['comments']) if hent.get('comments') else ''
            row_vals.append(comment_text)
            hwriter.writerow(row_vals)

    print(f'Created {history_file} with {len(sorted_entries)} records.')


if __name__ == '__main__':
    build_grandmaster(INPUT_CSV, INPUT_JSON, OUTPUT_FILE)
