# 概要
音楽ゲームのリザルト画面から取得したcsvファイルからランキングを更新できるように作成したスクリプト

## 処理のイメージ
input内にresult_summary.csvとsong_name_list.txtが置かれている状態とする。
- result_summary.csv は音楽ゲームのリザルト画面から取得したcsvファイル
- song_name_list.txt は課題曲となっている曲名のリスト


## 処理の流れ
1. result_summary.csvを読み込む
2. song_name_list.txtを読み込む
3. result_summary.csvのsong_nameをsong_name_list.txtの曲名と比較する
4. song_name_list.txtの曲名と一致する場合は、guess_song_nameにsong_name_list.txtの曲名を代入する
5. 一致しない場合は、曖昧マッチングを行い、最も似ている曲名をguess_song_nameに代入する
6. intermediate_songs.csvをoutputに出力する

## 注意点
guess_song_name,best_score,score,options,clear_lamp,best_clear_lampはリザルト画面から読み取れる情報となっている。
画像認識の精度により、これらレコードは間違っている可能性があるため、手動で修正する。

## 修正後
1. normalize_options.pyを実行する
2. proc_music_ranking.pyを実行する
3. 各楽曲ごとのcsvファイルがresult_rankingディレクトリに出力される