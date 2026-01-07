import marimo

__generated_with = "0.18.4"
app = marimo.App(width="full")


@app.cell
def _():
    import pandas as pd
    from google.oauth2 import service_account
    import gspread
    from gspread_dataframe import set_with_dataframe
    import json
    return gspread, json, pd, service_account, set_with_dataframe


@app.cell
def _(gspread, service_account):
    # googleスプレッドシートとの連携
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
      ]
    credentials = service_account.Credentials.from_service_account_file('.env/credentials.json', scopes=scopes)
    gc = gspread.authorize(credentials=credentials)

    spreadsheet_url = 'https://docs.google.com/spreadsheets/d/1zBzZTs5jF8cmYYTwmKuDWR6HRUkYbg6EXBPKgbdCeJI/edit?gid=759325330#gid=759325330'
    spreadsheet = gc.open_by_url(spreadsheet_url)
    worksheet = spreadsheet.worksheet("result_summary_processed")
    return spreadsheet, worksheet


@app.cell
def _(json, pd):
    #IR用ユーザーネームの読み込み
    df_ir_user_name = pd.read_csv('input/user_name.csv')
    df_ir_user_name

    #楽曲データの読み込み
    file = open('input/song_list.json', 'r')
    music_json = json.load(file)
    return df_ir_user_name, music_json


@app.cell
def _(df_ir_user_name, pd, worksheet):
    # googleスプレッドシートの読み込み
    df = pd.DataFrame(worksheet.get_values()[1:], columns=worksheet.get_values()[0])
    df = pd.merge(df, df_ir_user_name, how="left")
    df["best_score"] = df["best_score"].astype(int)
    df["score"] = df["score"].astype(int)
    df.fillna("")
    return (df,)


@app.cell
def _(df, df_song, set_with_dataframe, spreadsheet):
    # 脳筋IR結果シート更新用に、時間順にデータ抽出
    df_for_update = df.loc[:,["submission_date","submission_time","TwitterID", 'guess_song_name',"IRUserName", "score","Left", "Right","FLIP","LEGACY","A-SCR","play_format", "clear_award"]]
    df_for_update

    writesheet_for_update = spreadsheet.add_worksheet(title='for_update', rows=df_song.shape[1], cols=df_song.shape[0])
    set_with_dataframe(writesheet_for_update, df_for_update, row=1, col=1)
    return


@app.cell
def _(df, music_json, pd, set_with_dataframe, spreadsheet):
    # INFERNOの結果
    # クリアランプの優先順位
    LAMP_RANKS = {
        "F-COMBO": 6,
        "EXH-CLEAR": 5,
        "H-CLEAR": 4,
        "CLEAR": 3,
        "E-CLEAR": 2,
        "A-CLEAR": 1,
        "FAILED": 0,
        "NO PLAY": 0
    }

    df_song_list = []

    for key in music_json['selected_songs']:
        song_name = key['song_name']
        df_song_score = df[df['guess_song_name'] == song_name] \
                    .loc[:,["TwitterID", "IRUserName", "score","Left", "Right","FLIP","LEGACY","A-SCR","play_format"]] \
                    .fillna("") \
                    .sort_values("score", ascending=False) \
                    .drop_duplicates(subset="TwitterID", keep ='first')


        df_song_clear = df[df['guess_song_name'] == song_name] \
                    .loc[:,["TwitterID", "IRUserName","clear_award"]] \
                    .fillna("") \
                    .sort_values("clear_award", key=lambda col: col.map(LAMP_RANKS), ascending=False) \
                    .drop_duplicates(subset="TwitterID", keep="first")


        df_song = pd.merge(df_song_score, df_song_clear)
        df_song_list.append(df_song)

        writesheet = spreadsheet.add_worksheet(title=song_name+'_Latest', rows=df_song.shape[1], cols=df_song.shape[0])
        set_with_dataframe(writesheet, df_song, row=1, col=1)
    df_song_list
    return (df_song,)


if __name__ == "__main__":
    app.run()
