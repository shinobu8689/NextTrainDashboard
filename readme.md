**※日本語は英語の後にあります。／Japanese version below.**

# Next Train

## Overview

Next Train is a home-based train dashboard application that displays real-time information for Metro Trains in Victoria.

It uses:

- GTFS Realtime – Trip Updates – Metro Train API
- GTFS Schedule dataset provided by Transport Victoria

The application displays:

- Time until the next train
- Trip status
- Delay information
- Stops for incoming trains

The dashboard automatically refreshes every 30 seconds.

---

## Planned Improvements

- Refactor the code to support a future web-based GUI using JavaScript instead of a terminal interface
- Add support for multi-station queries in the terminal
- Evaluate automatic dataset updates from Transport Victoria
- Simplify the setup process
- Implement option.txt for default stations and other settings
- Same trains switch Trips at Town Hall Station, showing as 2 trips where they shared the same block.

---

## Change Log
INSERT DATE HERE - inital release to github

---

## Data Sources

GTFS Realtime – Trip Updates – Metro Train  
https://opendata.transport.vic.gov.au/dataset/gtfs-realtime/resource/0010d606-47bf-4abb-a04f-63add63a4d23?inner_span=True

GTFS Schedule Dataset  
https://opendata.transport.vic.gov.au/dataset/gtfs-schedule

---

## Requirements

You will need:

- GTFS Schedule dataset (from Transport Victoria Open Data)
- A Transport Victoria Open Data API key

---

## Setup Instructions

1. Download the GTFS Schedule dataset and extract it.  
   It should contain folders numbered 1 to 11.

2. Open Folder 2 (Metropolitan Train Lines).

3. Extract google_transit.zip into a folder named:

   gtfs_metro_trains

   Create the folder if it does not already exist.

4. Run:

   gtfs_query.py

   This will prepare the dataset and generate api_key.txt.

5. Obtain your own API key from Transport Victoria Open Data.

6. Place your API key inside:

   api_key.txt

   (In the same directory as the Python files.)

7. Run:

   gtfs_query.py

   again.

8. On startup, enter the station name you wish to display.  
   Partial station names are accepted, but may not always match the exact station.

9. The dashboard will now auto-refresh every 30 seconds.

---

## Project Structure

```
Project Folder
├── gtfs_metro_trains/
│   └── ...
├── gtfs.db
├── gtfs_query.py
├── current_trips.py
└── api_key.txt
```

- `gtfs_metro_trains/` – Extracted text files from GTFS dataset (Folder 2)
- `gtfs.db` – Generated from data inside `gtfs_metro_trains`
- `api_key.txt` – Stores your Transport Victoria API key



# Next Train

## 概要

「Next Train」は、自宅で使用できるMetro Train（ビクトリア州）の
リアルタイム列車情報ダッシュボードアプリケーションです。

以下のデータを使用しています：

- GTFS Realtime – Trip Updates – Metro Train API
- Transport Victoriaが提供するGTFS Scheduleデータセット

表示内容：

- 次の列車までの残り時間
- 列車の運行状況
- 遅延情報
- 到着予定列車の停車駅一覧

30秒ごとに自動更新されます。

---

## 今後の改善予定

- ターミナルUIからJavaScriptを使用したWebベースGUIへのリファクタリング
- ターミナルでの複数駅検索対応
- Transport Victoriaからのデータセット自動更新の実現可能性検討
- セットアップ手順の簡略化
- デフォルト駅や各種設定を管理する option.txt の実装
- 同じ列車がTown Hall駅でTripを切り替えるため、同一ブロックを共有しているにもかかわらず、2つのTripとして表示される。

---

## 変更履歴

INSERT DATE HERE - GitHubへの初回リリース

---


## データソース

GTFS Realtime – Trip Updates – Metro Train  
https://opendata.transport.vic.gov.au/dataset/gtfs-realtime/resource/0010d606-47bf-4abb-a04f-63add63a4d23?inner_span=True

GTFS Schedule  
https://opendata.transport.vic.gov.au/dataset/gtfs-schedule

---

## 必要なもの

- Transport Victoria Open DataのGTFS Scheduleデータセット
- Transport Victoria Open DataのAPIキー

---

## セットアップ手順

1. GTFS Scheduleデータセットをダウンロードし、解凍します。
   フォルダ1〜11が含まれているはずです。

2. 「2」フォルダ（Metropolitan Train Lines）を開きます。

3. google_transit.zip を「gtfs_metro_trains」というフォルダに解凍します。
   フォルダが存在しない場合は作成してください。

4. gtfs_query.py を実行します。
   データセットの準備と api_key.txt の生成が行われます。

5. Transport Victoria Open DataからAPIキーを取得します。

6. 取得したAPIキーを api_key.txt に記入します。
   （Pythonファイルと同じディレクトリに配置）

7. 再度 gtfs_query.py を実行します。

8. 起動時に表示したい駅名を入力します。
   部分一致での入力も可能ですが、正確に一致しない場合があります。

9. 30秒ごとに自動更新されます。

---

## プロジェクト構成

```
Project Folder
├── gtfs_metro_trains/
│   └── ...
├── gtfs.db
├── gtfs_query.py
├── current_trips.py
└── api_key.txt
```

- `gtfs_metro_trains/` – GTFSデータセット（フォルダ2）から解凍したテキストファイル
- `gtfs.db` – `gtfs_metro_trains` 内のデータから生成されるデータベース
- `api_key.txt` – Transport VictoriaのAPIキーを保存するファイル