import tweepy
import random
import pathlib
import os
import logging
from datetime import datetime

SCRIPT_PATH = pathlib.Path(__file__).parent
TXT_PATH = SCRIPT_PATH.parent/"txt"

# ログファイルの設定
LOG_FILE = TXT_PATH / "twitter_bot.log"

# ログの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()  # コンソールにも出力
    ]
)
logger = logging.getLogger(__name__)


# 最後に返信したツイートIDを記録するファイル
LAST_ID_FILE = TXT_PATH/"last_id.txt"

# 最後に定期ツイートをした日時を記録するファイル
LAST_TWEET_TIME_FILE = TXT_PATH/"last_tweet_time.txt"

# 定期ツイートを実行する時間帯（0時のみ）
SCHEDULED_HOURS = [0]

# 認証処理
client = tweepy.Client(
    bearer_token=os.environ.get("BEARER_TOKEN"),
    consumer_key=os.environ.get("API_KEY"),
    consumer_secret=os.environ.get("API_KEY_SECRET"),
    access_token=os.environ.get("ACCESS_TOKEN"),
    access_token_secret=os.environ.get("ACCESS_TOKEN_SECRET")
)

# API(画像アップロード用)
auth_v1 = tweepy.OAuth1UserHandler(
    os.environ.get("API_KEY"),
    os.environ.get("API_KEY_SECRET"),
    os.environ.get("ACCESS_TOKEN"),
    os.environ.get("ACCESS_TOKEN_SECRET")
)
api_v1 = tweepy.API(auth_v1)

# 最後に返信したツイートIDをファイルから読み込む
def read_last_id():
    if not os.path.exists(LAST_ID_FILE):
        return None
    with open(LAST_ID_FILE, 'r') as f:
        last_id = f.read().strip()
        return int(last_id) if last_id else None

# 最後のツイートIDをファイルに書き込む
def write_last_id(tweet_id):
    with open(LAST_ID_FILE, 'w') as f:
        f.write(str(tweet_id))
        
# 最後に定期ツイートをした日時を取得する
def read_last_tweet_time():
    if not os.path.exists(LAST_TWEET_TIME_FILE):
        return None
    with open(LAST_TWEET_TIME_FILE, 'r') as f:
        last_time = f.read().strip()
        return last_time

# 最後に定期ツイートをした日時を書き込む
def write_last_tweet_time(time_str):
    with open(LAST_TWEET_TIME_FILE, 'w') as f:
        f.write(time_str)

# 自分のユーザーID取得
def get_my_user_id():
    try:
        response = client.get_me()
        if response.data:
            me = response.data
            return me.id
        else:
            logger.error("自分のユーザーIDを取得できませんでした。")
            return None
    except Exception as e:
        logger.error(f"ユーザーID取得エラー: {e}")
        return None

# メンションにおみくじを返信する
def omikuji_reply():
    logger.info(f"メンションチェック開始: ({datetime.now().strftime('%H:%M')})")
    
    my_id = get_my_user_id()
    since_id = read_last_id()
    
    if not my_id:
        logger.error("ユーザーIDが取得できないため、メンションチェックを中止します。")
        return
    
    try:
        # メンション取得
        if since_id:
            mentions = client.get_users_mentions(id=my_id, since_id=since_id, expansions="author_id")
        else:
            mentions = client.get_users_mentions(id=my_id, expansions="author_id")
        
        # メンションデータの確認
        try:
            mention_data = getattr(mentions, 'data', None)
            if not mention_data:
                logger.info("新しいメンションはありませんでした。")
                return
        except:
            logger.info("新しいメンションはありませんでした。")
            return
        
        # 自分のユーザー名を取得
        try:
            me_response = client.get_me()
            my_username = getattr(getattr(me_response, 'data', None), 'username', 'bot')
        except:
            my_username = "bot"
        
        new_id = since_id or 0
        for mention in reversed(mention_data):
            # ツイート本文をチェック（メンション部分を除去して判定）
            text_without_mentions = mention.text.replace(f"@{my_username}", "").strip()
            
            if text_without_mentions == "おみくじ":
                # 作者のユーザー情報を取得
                try:
                    author_info = client.get_user(id=mention.author_id)
                    author_username = getattr(getattr(author_info, 'data', None), 'username', 'unknown')
                except Exception as e:
                    logger.warning(f"ユーザー情報取得エラー: {e}")
                    author_username = "unknown"
                
                # おみくじの結果をランダムに決める
                results = ["大吉", "吉", "凶", "大凶"]
                result_jp = random.choice(results)
                
                # 結果に応じた画像を取得
                result_map = {"大吉": "daikichi", "吉": "kichi", "凶": "kyou", "大凶": "daikyou"}
                image_filename = f"{result_map[result_jp]}.png"
                image_path = pathlib.Path(__file__).parent.parent / "image" / image_filename
                reply_text = f"@{author_username}\n今日の運勢は... 【{result_jp}】だっぴ！"
                
                # 画像をアップロードして返信
                try:
                    if image_path.exists():
                        media = api_v1.media_upload(filename=str(image_path))
                        client.create_tweet(text=reply_text, media_ids=[media.media_id], in_reply_to_tweet_id=mention.id)
                        logger.info(f"@{author_username}におみくじ返信成功！結果: {result_jp}")
                    else:
                        # 画像がない場合はテキストのみで返信
                        client.create_tweet(text=reply_text, in_reply_to_tweet_id=mention.id)
                        logger.info(f"@{author_username}におみくじ返信成功！結果: {result_jp} (画像なし)")
                except Exception as e:
                    logger.error(f"返信中にエラーが起きました: {e}")
            else:
                logger.debug(f"おみくじ以外のメンション: '{text_without_mentions}' - スキップします")
                
            if mention.id > new_id:
                new_id = mention.id
        
        if new_id > (since_id or 0):
            write_last_id(new_id)
            logger.info("最新のメンションIDを保存しました。")
            
    except Exception as e:
        logger.error(f"メンション取得中にエラーが起きました: {e}")
        

# 定期ツイートを行う
def post_scheduled_tweet():
    logger.info("定期ツイート処理開始")
    
    # 重複投稿を避けるため、日付をチェック（毎日0時に1回のみ）
    last_time_str = read_last_tweet_time()
    current_date_str = datetime.now().strftime('%Y-%m-%d')
    
    if last_time_str == current_date_str:
        logger.info("今日は既に定期ツイートを投稿済みです。")
        return
    
    # ツイートする名言を取得する
    script_path = pathlib.Path(__file__).resolve()
    root = script_path.parent.parent
    tweet_file_path = root/"txt"/"tweet_word.txt"

    try:
        with open(tweet_file_path, 'r', encoding='utf-8') as file:
            tweet_list = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        logger.error(f"エラー: {tweet_file_path}が見つかりません。")
        tweet_list = []

    if tweet_list:
        tweet_text = random.choice(tweet_list)
        logger.info(f"選択された名言: {tweet_text[:50]}...")  # 最初の50文字のみログに記録

        # ツイート
        try:
            response = client.create_tweet(text=tweet_text)
            logger.info("定期ツイートが成功しました！")

            # 実行日をファイルに記録
            write_last_tweet_time(current_date_str)
            
        except tweepy.TweepyException as e:
            logger.error(f"ツイートの投稿中にエラーが発生しました: {e}")
    else:
        logger.warning("tweet_word.txtが空です。")
        

if __name__ == "__main__":
    logger.info("Twitter Bot 実行開始")
    
    omikuji_reply()
    
    current_hour = datetime.now().hour
    if current_hour in SCHEDULED_HOURS:
        logger.info(f"定期ツイート時間です（{current_hour}時）")
        post_scheduled_tweet()
    else:
        logger.info(f"定期ツイート時間外です（現在: {current_hour}時）")
    
    logger.info("Twitter Bot 実行終了")