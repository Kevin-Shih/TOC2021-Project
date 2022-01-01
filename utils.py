import os
from datetime import datetime, timedelta
from linebot import LineBotApi, WebhookParser
from linebot.models import TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageTemplateAction, DatetimePickerAction, CarouselTemplate, actions
from linebot.models.template import CarouselColumn

channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)


def send_text_message(reply_token, text):
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(reply_token, TextSendMessage(text=text))
    return "OK"
    
def send_time_picker(reply_token, template_title, template_text):  #label, text should be array likeand has same len
    line_bot_api = LineBotApi(channel_access_token)
    line_bot_api.reply_message(  
        reply_token,
        TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                title=template_title,
                text=template_text,
                actions = [
                    DatetimePickerAction(
                        label="選擇日期",
                        data="date",
                        mode="date",
                        initial=datetime.today().date().isoformat(),
                        max=(datetime.today()+timedelta(days=90)).date().isoformat(),
                        min=(datetime.today()-timedelta(days=90)).date().isoformat()
                    ),
                    MessageTemplateAction(
                        label = "上一步",
                        text = "上一步"
                    ),
                    MessageTemplateAction(
                        label = "取消",
                        text = "取消"
                    )
                ]
            )
        )
    )
    
def send_button_message(reply_token, template_title, template_text, labels, texts = None, thumbnail_image_url = None):  #label, text should be array likeand has same len
    if texts is None:
        texts = labels
    assert len(labels) == len(texts)
    line_bot_api = LineBotApi(channel_access_token)
    actions = []
    for label, text in zip(labels, texts): #設定buttons
        actions.append(
            MessageTemplateAction(
                label = label,
                text = text
            )
        )
    line_bot_api.reply_message(
        reply_token,
        TemplateSendMessage(
            alt_text='Buttons template',
            template=ButtonsTemplate(
                title=template_title,
                text=template_text,
                actions = actions,
                thumbnail_image_url = thumbnail_image_url,
                image_aspect_ratio="square",
                image_size="contain"
            )
        )
    )
    
def send_carousel_message(reply_token, template_title, template_text, labels):
    assert len(template_title) == len(labels)
    line_bot_api = LineBotApi(channel_access_token)
    columns=[]
    for label, title, text in zip(labels,template_title, template_text):
        columns.append(
            CarouselColumn(
                title = title, 
                text = text,
                actions = [MessageTemplateAction(label,label)]
            )
        )
    line_bot_api.reply_message(
        reply_token,
        TemplateSendMessage(
            alt_text='Carousel template',
            template=CarouselTemplate(
                columns=columns
            )
        )
    )
    return
