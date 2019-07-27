from flask import Flask, request, abort, render_template
from datetime import datetime
import datetime as dt
import os
import json
import base64
import urllib.parse
import requests

from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
)


CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

# CHANNEL_ACCESS_TOKEN = "7efMffmVz5flkbMB63dFXX7eEarxWEq13mhorgzMwH9ih9DWlQ6mf40CKGOrs8cmmh7MyiTAjH4mtNFobdG/kO7o1VShglxkdXyCKrM5honZJX7zGuYfIXgJ824d5NDZDgGe0rcvqzj5iiyffh1591GUYhWQfeY8sLGRXgo3xvw="
# CHANNEL_SECRET = "23ae6680c77a3a9b04fb2513db16bf85"

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(CHANNEL_SECRET)

app = Flask(__name__)

# ↓ Added code
# kintone Settings
URL = "https://devksmpdi.cybozu.com/k/v1/record.json" # change your URL
APPID = 18 # change your App ID
API_TOKEN = "Yx5d9zcm1fCet8V07cJjRbaN6e0dJjD2LbcFRAxN" # change your Token

@app.route('/')
def do_get():
    return "Hello, from flask!"

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    print("Request body: " + body)

    try:
        # Parse JSON without SDK for LINE Things event
        events = json.loads(body)
        for event in events["events"]:
            if "things" in event:
                handle_things_event(event)
            else:
                message = parser.parse(body, signature)[0]
                handle_message(message)
    except InvalidSignatureError:
        print("Invalid signature. Please check your channel access token/channel secret.")
        abort(400)

    return 'OK'

def handle_things_event(event):
    if event["things"]["type"] != "scenarioResult":
        return
    if event["things"]["result"]["resultCode"] != "success":
        app.logger.warn("Error result: %s", event)
        return

    # send message of payload
    try:
        payload = base64.b64decode(event["things"]["result"]["bleNotificationPayload"])
        tempelature = int.from_bytes(payload, 'big') / 100.0
        # line_bot_api.reply_message(event["replyToken"], TextSendMessage(text="値を受け取ったよ %s" % (tempelature)))
        # ↓ Added Post Data Code
        post_kintone(URL, APPID, API_TOKEN, tempelature)
    except KeyError:
        return

    print("Got data: " + str(tempelature))

def handle_message(event):
    if event.type == "message" and event.message.type == "text":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=event.message.text))

# ↓ Added Post Data func
def post_kintone(url, app, api_token, val):
    params = {
        "app": app,
        "record": {
            "num": {
            "value": val
            }
        }
    }
    headers = {"X-Cybozu-API-Token": api_token, "Content-Type" : "application/json"}
    requests.post(url, json=params, headers=headers)

if __name__ == "__main__":
    app.debug = True
    app.run()
