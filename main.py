from flask import Flask, request, abort, render_template
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

# get Token and Secret from token
CHANNEL_ACCESS_TOKEN = os.environ.get('CHANNEL_ACCESS_TOKEN')
CHANNEL_SECRET = os.environ.get('CHANNEL_SECRET')

line_bot_api = LineBotApi(CHANNEL_ACCESS_TOKEN)
parser = WebhookParser(CHANNEL_SECRET)

app = Flask(__name__)

# check server working
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
                event = parser.parse(body, signature)[0]
                handle_message(event)
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
        line_bot_api.reply_message(event["replyToken"], TextSendMessage(text="値を受け取ったよ %s" % (tempelature)))
    except KeyError:
        return
        
    print("Got data: " + str(tempelature))

def handle_message(event):
    if event.type == "message" and event.message.type == "text":
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=event.message.text))


if __name__ == "__main__":
    app.debug = True
    app.run()
