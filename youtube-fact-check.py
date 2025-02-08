#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
import time

client = OpenAI()
LLM_MODEL = "gpt-4o"

def extract_video_id(url):
    """
    YouTube の URL から動画ID (11文字) を抽出する関数。
    例: https://www.youtube.com/watch?v=VIDEO_ID または https://youtu.be/VIDEO_ID
    """
    pattern = r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    else:
        return None

def fetch_transcript(video_id):
    """
    youtube_transcript_api を利用して、指定した動画ID のトランスクリプトを取得する。
    複数のエントリがある場合は、テキストを結合して返す。
    """
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([entry["text"] for entry in transcript_list])
        return transcript_text
    except Exception as e:
        print("トランスクリプト取得エラー:", str(e))
        return None

def summarize_transcript(transcript):
    """
    OpenAI API を利用して、トランスクリプトからファクトチェックすべき主な主張／論点を抽出する。
    プロンプトで要約（主張抽出）の指示を与える。
    """
    messages = [
        { 
            "role": "system", 
            "content": "You are a great transcript writer." 
        },
        { 
            "role": "user", 
            "content": f"""以下のYouTube動画のトランスクリプトから、主な主張や論点においてファクトチェックすべき点を箇条書きで英語で抽出してください。
            ** などの太字は使わないでください。
            Google Fact Check APIに文字列を渡しやすい形式にしてください。
            
            以下はYouTubeのトランスクリプトです
            \n\n{transcript}\n\n"""
        }
    ]

    try:
        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=0.6,
            max_tokens=5000
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        print("OpenAI API 要約エラー:", str(e))
        return None

def check_facts(query, google_api_key):
    """
    Google Fact Check Tools API を利用して、ファクトチェックを行う。
    各主張を個別に処理し、不要な記号・改行を除去。
    主張が長い場合はOpenAI APIで主要なキーワードを抽出して、クエリ文字列を短縮する。
    """
    # クエリの各行を主張として分割（空行を除外）
    claims = [line.strip() for line in query.strip().splitlines() if line.strip()]
    all_results = []
    
    for claim in claims:
        # 箇条書きの記号（'-', '•', '*'）などを削除
        claim_clean = re.sub(r'^[-•*]\s*', '', claim)
        # 特殊文字（例：'**'）を削除
        claim_clean = re.sub(r'\*\*', '', claim_clean)
        
        # 主張が長すぎる場合、キーワード抽出を試みる
        if len(claim_clean) > 2000:
            try:
                response = client.chat.completions.create(
                    model=LLM_MODEL,
                    messages=[{
                        "role": "user",
                        "content": f"Extract 3-5 main keywords from this claim in English: {claim_clean}"
                    }],
                    temperature=0.3,
                )
                keywords = response.choices[0].message.content.strip()
                # キーワードに置き換えて検索クエリとする
                claim_search = keywords
            except Exception as e:
                print(f"キーワード抽出エラー（{claim_clean}）: {str(e)}")
                claim_search = claim_clean[:100]
        else:
            claim_search = claim_clean
        
        # 改行など不要な文字を除去してクエリを整形
        claim_search = claim_search.replace("\n", " ").strip()
        
        url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
        params = {
            "query": claim_search,
            "key": google_api_key,
            "languageCode": "en"  # 明示的に英語で検索
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if "claims" in data and data["claims"]:
                result = f"検索クエリ: {claim_search}\n"
                for fact in data["claims"]:
                    result += f"主張: {fact.get('text', 'なし')}\n"
                    if "claimReview" in fact:
                        for review in fact["claimReview"]:
                            result += f"評価: {review.get('textualRating', 'なし')}\n"
                            result += f"出典: {review.get('url', 'なし')}\n"
                all_results.append(result)
            else:
                # all_results.append(f"クエリ「{claim_search}」に関するファクトチェック情報は見つかりませんでした。")
                pass
                
        except Exception as e:
            all_results.append(f"エラー（{claim_search}）: {str(e)}")
        
        # APIの制限を考慮して少し待機
        time.sleep(1)
    
    return "\n\n".join(all_results) if all_results else "ファクトチェック情報は見つかりませんでした。"

def main():
    # コマンドライン引数から YouTube URL を取得
    if len(sys.argv) < 2:
        print("Usage: python script.py <YouTube URL>")
        sys.exit(1)

    url = sys.argv[1]
    video_id = extract_video_id(url)
    if not video_id:
        print("Error: YouTube URL から動画IDが抽出できませんでした。")
        sys.exit(1)
    print("動画ID:", video_id)

    # YouTube のトランスクリプト取得
    transcript = fetch_transcript(video_id)
    if not transcript:
        print("エラー: トランスクリプトの取得に失敗しました。")
        sys.exit(1)
    print("トランスクリプトの取得に成功しました。")

    # OpenAI API の設定
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("エラー: OPENAI_API_KEY 環境変数が設定されていません。")
        sys.exit(1)

    # トランスクリプトから要約／主張抽出
    summary = summarize_transcript(transcript)
    if not summary:
        print("エラー: 要約／主張抽出に失敗しました。")
        sys.exit(1)
    print("抽出された主張／論点:\n", summary)

    # Google Fact Check API の設定（環境変数 "YOUTUBE_API_KEY" に正しいキーが保存されている前提）
    google_api_key = os.getenv("YOUTUBE_API_KEY")
    if not google_api_key:
        print("エラー: YOUTUBE_API_KEY 環境変数が設定されていません。")
        sys.exit(1)

    # 抽出結果に対するファクトチェックを実施
    fact_check_result = check_facts(summary, google_api_key)
    print("ファクトチェック結果:\n", fact_check_result)

if __name__ == "__main__":
    main()
