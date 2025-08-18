import tweepy
import random
import pathlib
import api_key as api

# 認証処理
client = tweepy.Client(
    consumer_key=api.API_KEY,
    consumer_secret=api.API_KEY_SECRET,
    access_token=api.ACCESS_TOKEN,
    access_token_secret=api.ACCESS_TOKEN_SECRET
)

# ツイートする名言を取得する
script_path = pathlib.Path(__file__).resolve()
root = script_path.parent.parent
txt_file_path = root/"txt"/"tweet_word.txt"

try:
    with open(txt_file_path, 'r', encoding='utf-8') as file:
        tweet_list = [line.strip() for line in file if line.strip()]
except FileNotFoundError:
    print(f"エラー: {txt_file_path}が見つかりません。")
    tweet_list = []

if tweet_list:
    tweet_text = random.choice(tweet_list)

    # ツイート
    try:
        response = client.create_tweet(text=tweet_text)
        print("ツイートが成功しました！")

    except tweepy.TweepyException as e:
        print(f"ツイートの投稿中にエラーが発生しました: {e}")
else:
    print("tweet_word.txtが空です。")