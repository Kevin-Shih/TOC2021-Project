from datetime import datetime
from linebot.models.events import PostbackEvent
from transitions.extensions import GraphMachine
from utils import send_text_message, send_button_message, send_time_picker, send_carousel_message
import os
import pickle
import threading
import codecs

# class MachineTimer(threading.Timer):
#     def run(self):
#         while not self.finished.wait(self.interval):
#             self.function(*self.args, **self.kwargs)
            
class TocMachine(GraphMachine):
    def __init__(self, **machine_configs):
        self.machine = GraphMachine(model=self, **machine_configs)
        self.book = None
        self.type = None
        self.date = None
        self.description = None
        self.money = None
    
    def is_backward(self, event):
        text = event.message.text
        return text.lower() == "上一步"
    
    def is_cancel(self, event):
        text = event.message.text
        self.machine.is_state("confirm", self)
        return text.lower() == "取消" or (self.machine.is_state("confirm", self) and text.lower() == "否")
    
    def is_adding(self, event):
        text = event.message.text
        return text.lower() == "新增記帳"

    def is_showing(self, event):
        text = event.message.text
        return text.lower() == "顯示帳本"

    def is_validtype(self, event):
        text = event.message.text
        self.type = event.message.text
        return text.lower() == "支出" or text.lower() =="收入"

    def is_date(self, event):
        if not isinstance(event, PostbackEvent):
            return False
        print(event.postback.params['date'])
        self.date = event.postback.params['date']
        return True
        
    def is_money(self, event):
        if not str(event.message.text).replace('.', '', 1).isdigit():
            print("not num")
            return False
        if not float(event.message.text).is_integer() :
            print("not int")
            return False
        print(int(float(event.message.text)))
        self.money = str(int(float(event.message.text)))
        return True

    def is_confirm(self, event):
        text = event.message.text
        return text.lower() == "是"
    
    def is_add_another(self, event):
        text = event.message.text
        return text.lower() == "再新增一筆"

    def is_not_add_another(self, event):
        text = event.message.text
        return text.lower() == "回主選單"
    
    def is_return2menu(self, event):
        text = event.message.text
        return text.lower() == "回主選單"

    def on_enter_user_menu(self, event):
        print(event.source.user_id)
        self.book = codecs.open(os.path.join('./users', event.source.user_id), 'a+', 'utf-8')
        reply_token = event.reply_token
        send_button_message(reply_token, "歡迎回到財務管家!", "請選擇功能", ["新增記帳", "顯示帳本"], thumbnail_image_url="https://306c-2001-b011-d802-d4a2-bd05-1efb-60c0-f5b2.ngrok.io/account_icon")

    def on_enter_type(self, event):
        reply_token = event.reply_token
        send_button_message(reply_token,"新增的帳目類型", "請選擇帳目類型為支出或收入?", ["支出", "收入", "取消"])
    
    def on_enter_date(self, event):
        reply_token = event.reply_token
        send_time_picker(reply_token, "選擇帳目日期", f"選擇這筆{self.type}的日期")

    def on_enter_description(self, event):
        reply_token = event.reply_token
        send_text_message(reply_token, f"請輸入這筆{self.type}的描述")
    
    def on_enter_money(self, event):
        reply_token = event.reply_token
        send_text_message(reply_token, f"請輸入{self.date}\n\"{self.description}\"\n的{self.type}金額 (正整數)")

    def on_enter_confirm(self, event):
        reply_token = event.reply_token
        send_button_message(reply_token,"確認帳目資訊", f"請確認帳目資訊無誤\n類型:{self.type}\n日期:{self.date}\n描述:{self.description}\n金額:{self.money}", ["是", "上一步 (修改)", "否 (捨棄)"], ["是", "上一步", "否"])
    
    def on_enter_add_another(self, event):
        reply_token = event.reply_token
        self.book.write(f'{self.type},{self.date},{self.description},{self.money}\n')
        self.book.flush()
        self.type = self.date = self.description = self.money = None
        send_button_message(reply_token,"成功新增一筆帳目!", "是否繼續新增?", ["再新增一筆", "回主選單"])
    
    def on_enter_show(self,event):
        reply_token = event.reply_token
        self.book.seek(0)
        spend = 0
        income = 0
        spend_y = {}
        income_y = {}
        for line in self.book.readlines():
            type, date, _, money = line.split(',')
            if spend_y.get(date[:4], None) is None:
                spend_y[date[:4]] = 0
                income_y[date[:4]] = 0
            if type == '支出':
                spend_y[date[:4]]+=int(money)
                spend+=int(money)
            elif type == '收入':
                income_y[date[:4]]+=int(money)
                income+=int(money)
        print(spend_y)
        print(income_y)
        self.book.seek(2)
        titles=["帳本總覽"]
        texts=[f'累計餘額:{income-spend}元\n累計支出:{spend}元\n累計收入:{income}元']
        labels=["回主選單"]
        for year in range(datetime.today().year,datetime.today().year-9,-1):
            if spend_y.get(str(year), None) is None:
                continue
            titles.append(f'{year}概況')
            texts.append(f'{year}餘額:{income_y[str(year)]-spend_y[str(year)]}元\n總支出:{spend_y[str(year)]}元\n總收入:{income_y[str(year)]}元')
            labels.append("回主選單")
        print()
        # send_button_message(reply_token,"帳本概況", f'累計餘額:{income-spend}元\n總支出:{spend}元 總收入:{income}元', ["回主選單"])
        send_carousel_message(reply_token, titles, texts, labels)
        
    def on_exit_description(self, event):
        self.description = event.message.text
        print(self.description)

