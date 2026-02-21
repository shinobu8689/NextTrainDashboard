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

---

## Furture Improvements
- Weekly update gtfs.zip updates from Transport Victoria
- Add support for multi-station (i.e Melbourne Central <-> State Library / Flinders Street <-> Town Hall )
- City Loop trains to show Clockwise/Anti-Clockwise in the City Loop
- option to show all stops for first train for each platform


---

## Change Log
- 21/02/2026
   - Unified time display format to (00:00 - 23:59) instead of operational hour 24h+
   - Moved API Key issue warning from Terminal to Web-Based UI
- 20/02/2026
   - Code cleaned and refactored, added data_validation
- 16/02/2026
   - Replacement Bus will not crash the program, and fixed direction from city headsign
   - Same trains/block with different trips at Town Hall will shown as one entry
- 15/02/2026
   - Coverting to partial working Web-based UI with bugs
- 12/02/2026
   - initial release to github

---

## Data Sources

GTFS Realtime – Trip Updates – Metro Train  
https://opendata.transport.vic.gov.au/dataset/gtfs-realtime/resource/0010d606-47bf-4abb-a04f-63add63a4d23?inner_span=True

GTFS Schedule Dataset  
https://opendata.transport.vic.gov.au/dataset/gtfs-schedule

---

## Requirements
<!--  -->
You will need:

- GTFS Schedule dataset (from Transport Victoria OpenData)
- A Transport Victoria OpenData API key

---

## Setup Instructions

1. Download the GTFS Schedule dataset and extract it.  
   It should contain folders numbered 1 to 11.

2. Extract google_transit.zip from Folder 2 (Metropolitan Train Lines) into a folder named:

      gtfs_metro_trains

   Create the folder if it does not already exist.
 
3. Startup the server in the terminal using:
   
      uvicorn startup:app --reload 

4. Obtain your own API key from Transport Victoria OpenData, and place it inside:

   api_key.txt

   (In the same directory as the Python files.)

5. Run:

   uvicorn startup:app --reload 

   again.


6. The system should startup automatically, te dashboard will now auto-refresh every 30 seconds.

---

## Project Structure

```
Project Folder
├── gtfs_metro_trains/
│   └── ...
├── frontend/
│   └── index.html
├── gtfs.db
├── gtfs_query.py
├── current_trips.py
├── startup.py
└── api_key.txt
```

- `gtfs_metro_trains/` – Extracted text files from GTFS dataset (Folder 2)
- `gtfs.db` – Generated from data inside `gtfs_metro_trains`
- `api_key.txt` – Stores your Transport Victoria API key



# Next Train

## 概要

Next Train は、ビクトリア州の Metro Trainsを対象とした、自宅用のリアルタイム列車ダッシュボードアプリです。

以下のデータを使用しています：

- GTFS Realtime – Trip Updates – Metro Train API
- Transport Victoria が提供する GTFS Schedule データセット

本アプリケーションでは、以下の情報を表示します：

-   次の列車までの残り時間
-   列車の運行ステータス
-   遅延情報

------------------------------------------------------------------------

## 今後の改善予定

-   Transport Victoria からの gtfs.zip を週次で自動更新
-   複数駅対応（例：Melbourne Central <-> State Library / Flinders Street <-> Town Hall）
-   City Loop 内の列車について、時計回り／反時計回りを表示
-   各プラットフォームの最初の列車について、全停車駅を表示するオプション

------------------------------------------------------------------------

## 更新履歴

-   2026/02/21
    -   運用時間（24時間超表記）ではなく、00:00 - 23:59 の統一フォーマットへ変更
    -   APIキー未設定時の警告表示を、ターミナルからWeb UIへ移動
-   2026/02/20
    -   コードの整理およびリファクタリング
    -   data_validation を追加
-   2026/02/16
    -   Replacement Bus 表示時にプログラムがクラッシュしないよう修正
    -   都心駅での headsign 方向表示を修正
    -   Town Hall 駅において、同一ブロックで異なる trip に切り替わる列車を1件として表示
-   2026/02/15
    -   一部動作するWebベースUIへ移行（不具合あり）
-   2026/02/12
    -   GitHub 初回公開

------------------------------------------------------------------------

## データソース

GTFS Realtime – Trip Updates – Metro Train  
https://opendata.transport.vic.gov.au/dataset/gtfs-realtime/resource/0010d606-47bf-4abb-a04f-63add63a4d23?inner_span=True

GTFS Schedule Dataset
https://opendata.transport.vic.gov.au/dataset/gtfs-schedule

------------------------------------------------------------------------

## 必要なもの

以下が必要です：

-   GTFS Schedule データセット（Transport Victoria OpenData より取得）
-   Transport Victoria OpenData の API キー

------------------------------------------------------------------------

## セットアップ手順

1.  GTFS Schedule データセットをダウンロードし、解凍します。\
    解凍後、1〜11の番号付きフォルダが含まれていることを確認してください。

2.  フォルダ2（Metropolitan Train Lines）内の `google_transit.zip`
    を解凍し、以下のフォルダへ配置します：

        gtfs_metro_trains

    フォルダが存在しない場合は新規作成してください。

3.  サーバーを起動します：

        uvicorn startup:app --reload

4.  Transport Victoria OpenData から自身の API キーを取得し、以下のファイルに保存します：

        api_key.txt

    （Pythonファイルと同じディレクトリに配置してください）

5.  再度、以下を実行します：

        uvicorn startup:app --reload

6.  システムが起動し、ダッシュボードは30秒ごとに自動更新されます。

------------------------------------------------------------------------

## プロジェクト構成

    Project Folder
    ├── gtfs_metro_trains/
    │   └── ...
    ├── frontend/
    │   └── index.html
    ├── gtfs.db
    ├── gtfs_query.py
    ├── current_trips.py
    ├── startup.py
    └── api_key.txt

-   `gtfs_metro_trains/` - GTFSデータセット（フォルダ2）から抽出したテキストファイル
-   `gtfs.db` - `gtfs_metro_trains`内のデータから生成されたSQLiteデータベース
-   `api_key.txt` - Transport Victoria の API キーを保存するファイル