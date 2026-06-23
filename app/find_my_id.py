import tweepy
import os

client = tweepy.Client(
    bearer_token=os.environ.get("BEARER_TOKEN"),
    consumer_key=os.environ.get("API_KEY"),
    consumer_secret=os.environ.get("API_KEY_SECRET"),
    access_token=os.environ.get("ACCESS_TOKEN"),
    access_token_secret=os.environ.get("ACCESS_TOKEN_SECRET")
)

try:
    response = client.get_me()
    if response.data:
        print(f"ユーザーID: {response.data.id}")
    else:
        print("エラー")
except Exception as e:
    print(e)