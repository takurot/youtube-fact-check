# YouTube Fact Check

このスクリプトは、指定された YouTube 動画のトランスクリプトを取得し、OpenAI API を使用してファクトチェックすべき主張を抽出します。その後、Google Fact Check Tools API を利用して、抽出された主張に対するファクトチェック情報を検索します。

## 必要条件

- Python 3.x
- 必要な Python ライブラリ：
  - `requests`
  - `youtube_transcript_api`
  - `openai`
- OpenAI API キー
- Google Fact Check Tools API キー

## 環境変数の設定

スクリプトを実行する前に、以下の環境変数を設定してください：

- `OPENAI_API_KEY`: OpenAI API のキー
- `YOUTUBE_API_KEY`: Google Fact Check Tools API のキー

## インストール

必要な Python ライブラリをインストールします：

pip install requests youtube-transcript-api openai

usage:python youtube-fact-check.py <YouTube URL>

## スクリプトの機能

1. **動画 ID の抽出**: YouTube の URL から動画 ID を抽出します。
2. **トランスクリプトの取得**: `youtube_transcript_api`を使用して、指定された動画のトランスクリプトを取得します。
3. **主張の抽出**: OpenAI API を使用して、トランスクリプトからファクトチェックすべき主張を抽出します。
4. **ファクトチェックの実施**: Google Fact Check Tools API を使用して、抽出された主張に対するファクトチェック情報を検索します。

## 注意事項

- スクリプトは、YouTube のトランスクリプトが利用可能な動画でのみ動作します。
- OpenAI API と Google Fact Check Tools API の使用には、それぞれの API キーが必要です。
- API の使用には料金が発生する場合がありますので、利用規約を確認してください。

## ライセンス

このプロジェクトは MIT ライセンスの下で公開されています。
