import os
import sys
import pickle

from flask import Flask, jsonify, request, abort, send_file
from dotenv import load_dotenv
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, ConfirmTemplate
from linebot.models.events import PostbackEvent
from linebot.models.template import Template

from fsm import TocMachine
from utils import send_text_message

load_dotenv()


machine = {}
def add_machine(machine,user_id):
    machine[user_id]=TocMachine(
        states=["greeting","user_menu", "show", "type", "date", "description", "money", "confirm", "add_another"],
        transitions=[
            {
                "trigger": "advance",
                "source": "greeting",
                "dest": "user_menu",
            },
            {
                "trigger": "advance",
                "source": "user_menu",
                "dest": "show",
                "conditions": "is_showing",
            },
            {
                "trigger": "advance",
                "source": "user_menu",
                "dest": "type",
                "conditions": "is_adding",
            },
            {
                "trigger": "advance",
                "source": "type",
                "dest": "date",
                "conditions": "is_validtype",
            },
            {
                "trigger": "advance",
                "source": "date",
                "dest": "description",
                "conditions": "is_date",
            },
            {
                "trigger": "advance",
                "source": "description",
                "dest": "money",
                "unless": ["is_cancel","is_backward"]
            },
            {
                "trigger": "advance",
                "source": "money",
                "dest": "confirm",
                "conditions": "is_money",
            },
            {
                "trigger": "advance",
                "source": "confirm",
                "dest": "add_another",
                "conditions": "is_confirm",
            },
            {
                "trigger": "advance",
                "source": "add_another",
                "dest": "type",
                "conditions": "is_add_another",
            },
            {
                "trigger": "advance",
                "source": "add_another",
                "dest": "user_menu",
                "conditions": "is_not_add_another",
            },
            {
                "trigger": "advance",
                "source": "show",
                "dest": "user_menu",
                "conditions": "is_return2menu"
            },
            {
                "trigger": "backward",
                "source": "confirm",
                "dest": "money",
                "conditions": "is_backward"
            },
            {
                "trigger": "backward",
                "source": "money",
                "dest": "description",
                "conditions": "is_backward"
            },
            {
                "trigger": "backward",
                "source": "description",
                "dest": "date",
                "conditions": "is_backward"
            },
            {
                "trigger": "backward",
                "source": "date",
                "dest": "type",
                "conditions": "is_backward"
            },
            {"trigger": "cancel", "source": ["type", "date", "description", "money", "confirm"], "dest": "user_menu","conditions": "is_cancel"},
        ],
        initial="greeting",
        auto_transitions=False,
        show_conditions=True,
        ignore_invalid_triggers=True
    )

add_machine(machine, 'for-fsm')
app = Flask(__name__, static_url_path="")


# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)


@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue

        line_bot_api.reply_message(
            event.reply_token, TextSendMessage(text=event.message.text)
        )

    return "OK"


@app.route("/webhook", methods=["POST"])
def webhook_handler():
    signature = request.headers["X-Line-Signature"]
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info(f"Request body: {body}")

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    for event in events:
        if isinstance(event, MessageEvent):
            if not isinstance(event.message, TextMessage):
                continue
            if not isinstance(event.message.text, str):
                continue
            if machine.get(event.source.user_id, None) is None:
                add_machine(machine, event.source.user_id)
            print(f"\nFSM STATE: {machine[event.source.user_id].state}")
            print(f"REQUEST BODY: \n{body}")
            response = machine[event.source.user_id].advance(event)
            if response == False:
                response = machine[event.source.user_id].backward(event)
                if response == False:
                    response = machine[event.source.user_id].cancel(event)
                    if response == False:
                        send_text_message(event.reply_token, "格式錯誤，請重新輸入")
        elif isinstance(event, PostbackEvent):
            print(f"\nFSM STATE: {machine[event.source.user_id].state}")
            print(f"REQUEST BODY: \n{body}")
            response = machine[event.source.user_id].advance(event)
            if response == False:
                send_text_message(event.reply_token, "請選擇有效日期")
    return "OK"


@app.route("/show-fsm", methods=["GET"])
def show_fsm():
    machine['for-fsm'].get_graph().draw("./img/show-fsm.png", prog="dot", format="png")
    return send_file("./img/show-fsm.png", mimetype="image/png")

@app.route("/account_icon", methods=["GET"])
def send_img():
    return send_file("./img/account_icon.png", mimetype="image/png")

if __name__ == "__main__":
    port = os.environ.get("PORT", 8000)
    app.run(host="0.0.0.0", port=port, debug=True)
