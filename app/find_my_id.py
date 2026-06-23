import tweepy
import api_key as api

client = tweepy.Client(
    bearer_token=api.BEARER_TOKEN,
    consumer_key=api.API_KEY,
    consumer_secret=api.API_KEY_SECRET,
    access_token=api.ACCESS_TOKEN,
    access_token_secret=api.ACCESS_TOKEN_SECRET
)

try:
    response = client.get_me()
    if response.data:
        print(f"ユーザーID: {response.data.id}")
    else:
        print("エラー")
except Exception as e:
    print(e)