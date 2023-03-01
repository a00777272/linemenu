import os
import requests
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from flask import Flask, request, abort

app = Flask(__name__)

# 設定 Channel Access Token 和 Channel Secret
line_bot_api = LineBotApi(os.environ.get("CHANNEL_ACCESS_TOKEN"))
handler = WebhookHandler(os.environ.get("CHANNEL_SECRET"))

# 設定 Google Map API 金鑰
google_map_api_key = os.environ.get("GOOGLE_MAP_API_KEY")

def search_location(query):
    # 使用 Google Map API 搜尋位置
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={query}&key={google_map_api_key}"
    res = requests.get(url)
    data = res.json()

    # 取得搜尋結果中的第一筆資訊
    if data['status'] == 'OK':
        place = data['results'][0]
        name = place['name']
        address = place['formatted_address']
        lat = place['geometry']['location']['lat']
        lng = place['geometry']['location']['lng']
        url = f"https://www.google.com/maps/search/?api=1&query={lat},{lng}"
        message = f"{name}\n{address}\n{url}"
    else:
        message = "抱歉，找不到相關的店家"
    return message

@app.route("/callback", methods=["POST"])
def callback():
    # 取得 X-Line-Signature 訊息頭
    signature = request.headers["X-Line-Signature"]

    # 取得請求內容
    body = request.get_data(as_text=True)

    # 處理訊息
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "OK"

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    query = event.message.text
    message = search_location(query)
    reply_message = TextSendMessage(text=message)
    try:
        line_bot_api.reply_message(event.reply_token, reply_message)
    except LineBotApiError as e:
        print(e.status_code)
        print(e.error.message)
        print(e.error.details)

if __name__ == "__main__":
    app.run()


