# -*- coding: utf-8 -*-
# @Time : 2024/2/16 15:10
# @Author : MaYun
# @Software: PyCharm

import GameHelper as gh
from GameHelper import GameHelper, play_sound, read_json, write_json, compare_images, subtract_strings
import sys
import random
import time
from collections import defaultdict
from douzero.env.move_detector import get_move_type
import cv2
import numpy as np
from PyQt5 import QtGui, QtWidgets, QtCore
from PyQt5.QtWidgets import QTableWidgetItem, QLabel
from PyQt5.QtGui import QKeyEvent, QIcon
from PyQt5.QtCore import QTime, QEventLoop, Qt, QFile, QTextStream, pyqtSignal, QThread
from MainWindow import Ui_Form

from douzero.env.game import GameEnv
from douzero.evaluation.deep_agent import DeepAgent
import traceback
from Recognition import yolo_detect

import BidModel
import LandlordModel
import FarmerModel

from cnocr import CnOcr

ocr = CnOcr(det_model_name='en_PP-OCRv3_det', rec_model_name='en_PP-OCRv3',
            cand_alphabet="12345678910")

helper = GameHelper()

EnvCard2RealCard = {3: '3', 4: '4', 5: '5', 6: '6', 7: '7', 8: '8', 9: '9', 10: 'T', 11: 'J', 12: 'Q',
                    13: 'K', 14: 'A', 17: '2', 20: 'X', 30: 'D'}

RealCard2EnvCard = {'3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, 'T': 10, 'J': 11, 'Q': 12,
                    'K': 13, 'A': 14, '2': 17, 'X': 20, 'D': 30}

AllCards = ['D', 'X', '2', 'A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3']

AllEnvCard = [3, 3, 3, 3, 4, 4, 4, 4, 5, 5, 5, 5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 8, 9, 9, 9, 9, 10, 10, 10, 10,
              11, 11, 11, 11, 12, 12, 12, 12, 13, 13, 13, 13, 14, 14, 14, 14, 17, 17, 17, 17, 20, 30]


def find_cards(pos: tuple):
    img = helper.Screenshot()
    img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    # img = cv2.imread("3.png")
    img = img[pos[1]:pos[1] + pos[3], pos[0]:pos[0] + pos[2]]
    img, class_list, pos_list = yolo_detect(img)
    if class_list is not None:
        pos_list = [[sublist[0] + pos[0], sublist[1] + pos[1]] + sublist[2:] for sublist in pos_list]
    return img, class_list, pos_list


def find_my_cards():
    img, class_list, pos_list = find_cards((10, 400, 1590, 300))
    if class_list is not None:
        cards = "".join(class_list)
    else:
        cards = ""
    return cards


def find_other_cards(pos: tuple):
    img, class_list, pos_list = find_cards(pos)
    if class_list is not None:
        cards = "".join(class_list)
    else:
        cards = ""
    return cards


def find_three_cards():
    regions = [(450, 36, 125, 55), (325, 36, 125, 55)]
    cards = ""
    for r in regions:
        img, class_list, pos_list = find_cards(r)
        if class_list is not None:
            cards = "".join(class_list)
            break
    return cards


def make_cards_dict(pos: tuple):
    img, class_list, pos_list = find_cards(pos)
    cards_dict = defaultdict(list)
    for key, value in zip(class_list, [sublist for sublist in pos_list]):
        cards_dict[key].append(value)
        # 转换为普通的字典
    cards_dict = dict(cards_dict)
    return cards_dict


def find_closest_number(num, lst):
    closest = lst[0]
    diff = abs(num - closest)
    for i in range(1, len(lst)):
        if abs(num - lst[i]) < diff:
            closest = lst[i]
            diff = abs(num - closest)
    if abs(num - closest) > 10:
        # 距离较远
        return True
    else:
        return False


def click_cards(out_cards):
    tmp_cards = out_cards
    position_list = [0]
    img, class_list, pos_list, = find_cards((10, 400, 1590, 300))
    min_value = 540
    '''for c, p in zip(class_list, pos_list):
        if c in tmp_cards and p[1] < min_value:
            position_list.append(p[0])
            tmp_cards = tmp_cards.replace(c, "", 1)'''

    for card in out_cards:  # 待选的牌
        img, class_list, pos_list, = find_cards((10, 400, 1590, 300))
        if len(class_list) <= 0:
            return
        for c, p in zip(class_list, pos_list):
            if c != card:
                if p[1] < min_value:
                    helper.LeftClick2((p[0] + int(p[2] / 2), p[1] + 100))
            else:
                if find_closest_number(p[0], position_list):
                    if p[1] >= min_value:
                        helper.LeftClick2((p[0] + int(p[2] / 2), p[1] + 100))
                        time.sleep(0.1)
                        position_list.append(p[0])
                        break
                    elif p[1] < min_value:
                        position_list.append(p[0])
                        break

        time.sleep(0.05)

    time.sleep(0.05)
    img, class_list, pos_list, = find_cards((10, 400, 1590, 300))
    if class_list:
        for c, p in zip(class_list, pos_list):
            if p[1] < min_value and find_closest_number(p[0], position_list):
                print(c, p)
                helper.LeftClick2((p[0] + int(p[2] / 2), p[1] + 100))
                time.sleep(0.05)

    time.sleep(0.5)


def ocr_cards_num(pos: tuple):
    img = helper.Screenshot()
    img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
    img = img[pos[1]:pos[1] + pos[3], pos[0]:pos[0] + pos[2]]
    result = ocr.ocr(img)
    cards_num = 0
    if len(result) > 0:
        result = result[0]['text']
        if result.isdigit():
            cards_num = int(result)
    return cards_num


def haveAnimation(waitTime=0.1):
    regions = [(560, 140, 560 + 30, 140 + 30)]  # 动画位置
    img = helper.Screenshot()
    lastImg = img
    for i in range(2):
        time.sleep(waitTime)
        img = helper.Screenshot()
        for region in regions:
            if compare_images(img.crop(region), lastImg.crop(region)):
                return True
        lastImg = img
    return False


class Worker(QThread):
    auto_game = pyqtSignal(int)  # Automatic start
    hand_game = pyqtSignal(int)  # Human start
    init_interface = pyqtSignal(int)  # Initialize interface
    player_display = pyqtSignal(int)  # Player Display
    state_display = pyqtSignal(str)  # 游戏状态显示
    stop = pyqtSignal(int)
    bid_display = pyqtSignal(str)  # 叫牌score
    three_cards_display = pyqtSignal(str)  # Three cards display
    winrate_display = pyqtSignal(str)  # Winrate Display
    pre_cards_display = pyqtSignal(str)  # 显示AI推荐出牌
    my_cards_display = pyqtSignal(str)  # 自己牌显示
    left_cards_display = pyqtSignal(str)  # 显示上家的牌
    right_cards_display = pyqtSignal(str)  # 显示下家的牌
    recorder_display = pyqtSignal(str)  # 记牌器
    write_threshold = pyqtSignal(int)  # 阈值写入json

    def __init__(self):
        super(Worker, self).__init__()
        self.my_played_cards_real = None
        self.bid_thresholds = None
        self.stop_sign = False
        self.winrate = None
        self.other_played_cards_real = None
        self.auto_sign = None
        self.RunGame = None
        self.env = None
        self.play_order = None
        self.other_hands_cards_str = None
        self.user_hand_cards_env = None
        self.user_hand_cards_real = None
        self.user_position = None
        self.user_position_code = None
        self.three_cards_env = None
        self.three_cards_real = None
        self.card_play_data_list = None
        self.other_hand_cards = None
        self.other_played_cards_env = None
        self.my_played_cards_env = None

        self.MyHandCardsPos = (10, 400, 1590, 300)  # 我的截图区域
        self.LPlayedCardsPos = (260, 180, 380, 150)  # 左边出牌截图区域
        self.RPlayedCardsPos = (640, 180, 380, 150)  # 右边出牌截图区域
        self.MPlayedCardsPos = (260, 330, 760, 150)  # 我的出牌截图区域

        self.LandlordCardsPos = (450, 36, 125, 55)  # 地主底牌截图区域
        self.LPassPos = (284, 172, 122, 56)  # 左边不出截图区域
        self.RPassPos = (894, 172, 122, 56)  # 右边不出截图区域
        self.MPassPos = (234, 469, 122, 57)  # 我的不出截图区域

        self.PassBtnPos = (90, 340, 1160, 190)  # 要不起截图区域
        self.GeneralBtnPos = (90, 340, 1160, 190)  # 叫地主、抢地主、加倍按钮截图区域
        self.blue_cards_num = [(16, 155, 84, 66), (1176, 155, 84, 66)]  # 加倍阶段上家和下家的手牌数量显示区域
        self.TimerPos = [(290, 310, 80, 80), (910, 310, 80, 80)]  # 左边和右边计显示器区域

        self.model_path_dict = {
            'landlord': "baselines/resnet/resnet_landlord.ckpt",
            'landlord_up': "baselines/resnet/resnet_landlord_up.ckpt",
            'landlord_down': "baselines/resnet/resnet_landlord_down.ckpt"
        }
        LandlordModel.init_model("baselines/resnet/resnet_landlord.ckpt")

    def run(self):
        self.confirm_threshold()
        self.init_interface.emit(1)
        while not self.stop_sign:
            self.detect_start_btn()
            self.before_start()
            self.init_cards()
            time.sleep(3)

    def confirm_threshold(self):
        self.write_threshold.emit(1)
        time.sleep(0.1)
        data = read_json()
        self.bid_thresholds = [float(data['bid1']), float(data['bid2']), float(data['bid3']), float(data['bid4'])]

    def detect_start_btn(self):
        result = helper.LocateOnScreen("once_more", region=(660, 600, 340, 130))
        if result is not None:
            self.RunGame = False
            self.init_interface.emit(1)
            try:
                if self.env is not None:
                    self.env.game_over = True
                    self.env.reset()
            except AttributeError as e:
                traceback.print_exc()
                time.sleep(3)
            time.sleep(3)
            helper.ClickOnImage("once_more", region=(660, 600, 340, 130))
            print("游戏结束")

        result = helper.LocateOnScreen("tuoguan", region=(497, 636, 292, 101))
        if result is not None:
            helper.ClickOnImage("tuoguan", region=(497, 636, 292, 101))

        result = helper.LocateOnScreen("dati", region=(386, 452, 218, 70))
        if result is not None:
            helper.ClickOnImage("dati", region=(386, 452, 218, 70))

        result = helper.LocateOnScreen("confirm", region=(460, 408, 360, 152))
        if result is not None:
            helper.ClickOnImage("confirm", region=(460, 408, 360, 152))

    def before_start(self):
        my_cards = find_my_cards()
        print("未进入游戏", end="")
        while len(my_cards) != 17:
            time.sleep(1)
            print(".", end="")
            my_cards = find_my_cards()
            self.detect_start_btn()
        print("\n在游戏中")
        print(my_cards)
        self.RunGame = True

        score = BidModel.predict_score(my_cards)
        score = round(score, 3)
        print(score)
        self.bid_display.emit("得分: " + str(score))

        click_times = 0
        self.three_cards_real = find_three_cards()
        print("正在叫地主", end="")
        while len(self.three_cards_real) != 3:
            print(".", end="")
            if not self.RunGame:
                break
            time.sleep(0.2)
            my_cards = find_my_cards()
            if self.auto_sign:
                bujiao_btn = helper.LocateOnScreen("bujiao_btn", self.GeneralBtnPos)
                fen1_btn = helper.LocateOnScreen("fen1", self.GeneralBtnPos)
                fen2_btn = helper.LocateOnScreen("fen2", self.GeneralBtnPos)
                fen3_btn = helper.LocateOnScreen("fen3", self.GeneralBtnPos)
                jiabei_btn = helper.LocateOnScreen("jiabei_btn", self.GeneralBtnPos)

                if jiabei_btn is not None and score >= self.bid_thresholds[3]:
                    helper.ClickOnImage("jiabei_btn", self.GeneralBtnPos)

                if click_times < 2:
                    if score <= self.bid_thresholds[0] and bujiao_btn:
                        helper.ClickOnImage("bujiao_btn", self.GeneralBtnPos)
                        print("不叫地主")
                        click_times += 1
                        self.pre_cards_display.emit("不叫地主")
                    elif self.bid_thresholds[0] < score <= self.bid_thresholds[1] and fen1_btn:
                        helper.ClickOnImage("fen1", self.GeneralBtnPos)
                        print("score: 1分")
                        click_times += 1
                        self.pre_cards_display.emit("score: 1分")
                    elif self.bid_thresholds[1] < score <= self.bid_thresholds[2] and fen2_btn:
                        helper.ClickOnImage("fen2", self.GeneralBtnPos)
                        print("score: 2分")
                        click_times += 1
                        self.pre_cards_display.emit("score: 2分")
                    elif score > self.bid_thresholds[2] and fen3_btn:
                        helper.ClickOnImage("fen3", self.GeneralBtnPos)
                        print("score: 3分")
                        click_times += 1
                        self.pre_cards_display.emit("score: 3分")

                else:
                    helper.ClickOnImage("bujiao_btn", self.GeneralBtnPos)
            if len(my_cards) == 0:
                click_times = 0
            self.three_cards_real = find_three_cards()
            self.detect_start_btn()

    def init_cards(self):
        print("进入出牌前阶段")
        # 玩家角色代码：0-地主上家, 1-地主, 2-地主下家
        # self.RunGame = True
        self.user_hand_cards_env = []
        self.my_played_cards_env = []
        self.other_played_cards_env = []
        self.other_hand_cards = []
        self.three_cards_env = []
        self.card_play_data_list = {}
        print("正在识别底牌", end="")
        while len(self.three_cards_real) != 3:
            print(".", end="")
            if not self.RunGame:
                break
            time.sleep(0.2)
            self.three_cards_real = find_three_cards()
            self.detect_start_btn()
        print("\n底牌： ", self.three_cards_real)
        self.three_cards_display.emit("底牌：" + self.three_cards_real)
        self.three_cards_env = [RealCard2EnvCard[c] for c in list(self.three_cards_real)]

        self.user_position_code = self.find_landlord()
        while self.user_position_code is None:
            if not self.RunGame:
                break
            print("正在识别玩家角色")
            time.sleep(0.2)
            self.user_position_code = self.find_landlord()
            self.detect_start_btn()

        self.user_position = ['landlord_up', 'landlord', 'landlord_down'][self.user_position_code]
        print("我的角色：", self.user_position)
        self.player_display.emit(self.user_position_code)

        self.user_hand_cards_real = find_my_cards()
        print(self.user_hand_cards_real)
        if self.user_position_code == 1:
            while len(self.user_hand_cards_real) != 20:
                if not self.RunGame:
                    break
                time.sleep(0.2)
                self.user_hand_cards_real = find_my_cards()
                self.detect_start_btn()
            self.user_hand_cards_env = [RealCard2EnvCard[c] for c in list(self.user_hand_cards_real)]
        else:
            while len(self.user_hand_cards_real) != 17:
                if not self.RunGame:
                    break
                time.sleep(0.2)
                self.user_hand_cards_real = find_my_cards()
                self.detect_start_btn()
            self.user_hand_cards_env = [RealCard2EnvCard[c] for c in list(self.user_hand_cards_real)]
        self.my_cards_display.emit("手牌：" + self.user_hand_cards_real)

        # 整副牌减去玩家手上的牌，就是其他人的手牌,再分配给另外两个角色（如何分配对AI判断没有影响）
        for i in set(AllEnvCard):
            self.other_hand_cards.extend([i] * (AllEnvCard.count(i) - self.user_hand_cards_env.count(i)))
        self.other_hands_cards_str = str(''.join([EnvCard2RealCard[c] for c in self.other_hand_cards]))[::-1]
        self.recorder_display.emit(self.other_hands_cards_str)
        self.card_play_data_list.update({
            'three_landlord_cards': self.three_cards_env,
            ['landlord_up', 'landlord', 'landlord_down'][(self.user_position_code + 0) % 3]:
                self.user_hand_cards_env,
            ['landlord_up', 'landlord', 'landlord_down'][(self.user_position_code + 1) % 3]:
                self.other_hand_cards[0:17] if (self.user_position_code + 1) % 3 != 1 else self.other_hand_cards[17:],
            ['landlord_up', 'landlord', 'landlord_down'][(self.user_position_code + 2) % 3]:
                self.other_hand_cards[0:17] if (self.user_position_code + 1) % 3 == 1 else self.other_hand_cards[17:]
        })

        print("开始对局")
        print("手牌:", self.user_hand_cards_real)
        print("底牌:", self.three_cards_real)

        # 出牌顺序：0-玩家出牌, 1-玩家下家出牌, 2-玩家上家出牌
        self.play_order = 0 if self.user_position == "landlord" else 1 if self.user_position == "landlord_up" else 2

        AI = [0, 0]
        AI[0] = self.user_position
        AI[1] = DeepAgent(self.user_position, self.model_path_dict[self.user_position])
        self.env = GameEnv(AI)
        try:
            self.game_start()
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            traceback.print_tb(exc_tb)
            self.RunGame = False
            self.init_interface.emit(1)
            if self.env is not None:
                self.env.game_over = True
                self.env.reset()

    def game_start(self):
        self.env.card_play_init(self.card_play_data_list)
        print("开始对局")
        self.state_display.emit("游戏开始")
        while not self.env.game_over:
            if not self.RunGame:
                break
            while self.play_order == 0:
                if not self.RunGame:
                    break
                if self.check_order(0) is None:
                    if self.auto_sign:
                        self.my_cards_display.emit("等待AI出牌")
                        action_message, action_list = self.env.step(self.user_position, update=False)
                        score = float(action_message['win_rate'])
                        if "resnet" in self.model_path_dict[self.user_position]:
                            score *= 8
                        hand_cards_str = ''.join(
                            [EnvCard2RealCard[c] for c in self.env.info_sets[self.user_position].player_hand_cards])
                        self.my_cards_display.emit("手牌：" + hand_cards_str[::-1])
                        action_list = action_list[:3]
                        if not self.winrate:
                            self.winrate = 0
                        self.bid_display.emit("得分：" + str(round(float(action_list[0][1]), 3)))
                        self.pre_cards_display.emit(action_message["action"] if action_message["action"] else "pass")
                        action_list_str = " | ".join([ainfo[0] + " = " + ainfo[1] for ainfo in action_list])
                        print("AI出牌：", action_list_str)
                        self.winrate_display.emit(action_list_str)

                        if action_message["action"] == "":
                            print("出牌:", "Pass", "| 得分:", round(action_message["win_rate"], 4), "| 剩余手牌:",
                                  hand_cards_str)
                            self.env.step(self.user_position, [])

                            pass_btn = helper.LocateOnScreen("pass_btn", region=self.PassBtnPos)
                            yaobuqi = helper.LocateOnScreen("yaobuqi", region=self.GeneralBtnPos)
                            buchu = helper.LocateOnScreen("buchu", region=self.MPassPos)
                            while pass_btn is None and yaobuqi is None and buchu is None:
                                if not self.RunGame or not self.auto_sign:
                                    break
                                pass_btn = helper.LocateOnScreen("pass_btn", region=self.PassBtnPos)
                                yaobuqi = helper.LocateOnScreen("yaobuqi", region=self.GeneralBtnPos)
                                buchu = helper.LocateOnScreen("buchu", region=self.MPassPos)
                                self.detect_start_btn()

                            if pass_btn is not None:
                                helper.ClickOnImage("pass_btn", region=self.PassBtnPos)
                            if yaobuqi is not None:
                                helper.ClickOnImage("yaobuqi", region=self.GeneralBtnPos)
                            if buchu is not None:
                                print("太狠了！ 我要不起")
                        else:
                            print("出牌:", action_message["action"], "| 得分:", round(action_message["win_rate"], 4),
                                  "| 剩余手牌:", hand_cards_str)
                            click_cards(action_message["action"])
                            play_card = helper.LocateOnScreen("play_card", region=self.PassBtnPos)
                            while play_card is None:
                                if not self.RunGame or not self.auto_sign:
                                    break
                                time.sleep(0.2)
                                play_card = helper.LocateOnScreen("play_card", region=self.PassBtnPos)
                                self.detect_start_btn()
                            try:
                                helper.ClickOnImage("play_card", region=self.PassBtnPos)
                            except Exception as e:
                                print("没找到出牌按钮")
                            # print("点击出牌按钮")
                            time.sleep(0.2)
                            play_card = helper.LocateOnScreen("play_card", region=self.PassBtnPos)
                            if play_card is not None:
                                click_cards(action_message["action"])
                                time.sleep(0.5)
                                helper.ClickOnImage("play_card", region=self.PassBtnPos)

                            self.my_played_cards_env = [RealCard2EnvCard[c] for c in list(action_message["action"])]
                            self.my_played_cards_env.sort()
                            self.env.step(self.user_position, self.my_played_cards_env)

                            hand_cards_str = ''.join(
                                [EnvCard2RealCard[c] for c in self.env.info_sets[self.user_position].player_hand_cards])

                            if len(hand_cards_str) == 0:
                                self.RunGame = False
                                self.init_interface.emit(1)
                                try:
                                    if self.env is not None:
                                        self.env.game_over = True
                                        self.env.reset()
                                except AttributeError as e:
                                    traceback.print_exc()
                                    print("程序走到这里")
                                    time.sleep(1)
                                break
                        tip_btn = helper.LocateOnScreen('tip_btn', region=self.GeneralBtnPos)
                        if action_message["action"] == "XD" or tip_btn:
                            my_cards = find_my_cards()
                            while len(my_cards) == 0:
                                if not self.RunGame:
                                    break
                                time.sleep(0.3)
                                my_cards = find_my_cards()
                                self.detect_start_btn()
                            self.play_order = 1
                            self.env.step(self.user_position, [])
                            self.play_order = 2
                            self.env.step(self.user_position, [])
                            self.play_order = 0
                        else:
                            self.play_order = 1

                    else:
                        print("现在是手动模式，请点击出牌")
                        play_sound("music/1.wav")
                        action_message, action_list = self.env.step(self.user_position, update=False)
                        score = float(action_message['win_rate'])
                        if "resnet" in self.model_path_dict[self.user_position]:
                            score *= 8

                        if len(action_list) > 0:
                            action_list = action_list[:3]
                            action_list_str = " | ".join([ainfo[0] + " = " + ainfo[1] for ainfo in action_list])
                            self.winrate_display.emit(action_list_str)
                            if not self.winrate:
                                self.winrate = 0
                            self.bid_display.emit("得分：" + str(round(float(action_list[0][1]), 3)))
                        else:
                            self.winrate_display.emit("没提示，自己出")

                        self.pre_cards_display.emit("等待自己出牌")
                        pass_flag = helper.LocateOnScreen('buchu', region=self.MPassPos)
                        centralCards = find_other_cards(self.MPlayedCardsPos)
                        print("等待自己出牌", end="")
                        while len(centralCards) == 0 and pass_flag is None:
                            if not self.RunGame or self.auto_sign or self.env.game_over:
                                break
                            print(".", end="")
                            time.sleep(0.2)
                            pass_flag = helper.LocateOnScreen('buchu', region=self.MPassPos)
                            centralCards = find_other_cards(self.MPlayedCardsPos)
                            self.detect_start_btn()

                        if pass_flag is None:
                            while True:
                                if not self.RunGame or self.auto_sign:
                                    break
                                centralOne = find_other_cards(self.MPlayedCardsPos)
                                time.sleep(0.3)
                                centralTwo = find_other_cards(self.MPlayedCardsPos)
                                if centralOne == centralTwo and len(centralOne) > 0:
                                    self.my_played_cards_real = centralOne
                                    break
                                self.detect_start_btn()
                        else:
                            self.my_played_cards_real = ""
                        print("\n自己出牌：", self.my_played_cards_real if self.my_played_cards_real else "pass")
                        self.my_played_cards_env = [RealCard2EnvCard[c] for c in list(self.my_played_cards_real)]
                        self.my_played_cards_env.sort()
                        action_message, _ = self.env.step(self.user_position, self.my_played_cards_env)
                        hand_cards_str = ''.join(
                            [EnvCard2RealCard[c] for c in self.env.info_sets[self.user_position].player_hand_cards])
                        self.my_cards_display.emit("手牌：" + hand_cards_str[::-1])

                        print("出牌:", action_message["action"] if action_message["action"] else "Pass", "| 得分:",
                              round(action_message["win_rate"], 4), "| 剩余手牌:", hand_cards_str)
                        self.pre_cards_display.emit(self.my_played_cards_real if self.my_played_cards_real else "pass")

                        if action_message["action"] == "DX":
                            my_cards = find_my_cards()
                            while len(my_cards) == 0:
                                if not self.RunGame:
                                    break
                                time.sleep(0.3)
                                my_cards = find_my_cards()
                                self.detect_start_btn()
                            self.play_order = 1
                            self.env.step(self.user_position, [])
                            self.play_order = 2
                            self.env.step(self.user_position, [])
                            self.play_order = 0
                        else:
                            self.play_order = 1
                    time.sleep(0.2)

                else:
                    print("轮到别人出牌")

                self.detect_start_btn()
            self.detect_start_btn()

            if self.play_order == 1:
                self.right_cards_display.emit("等待下家出牌")
                rightCards = find_other_cards(self.RPlayedCardsPos)
                if len(rightCards) > 0:
                    time.sleep(1)

                order = self.check_order(1)
                pass_flag = helper.LocateOnScreen('buchu', region=self.RPassPos)
                rightCards = find_other_cards(self.RPlayedCardsPos)
                my_cards = find_my_cards()
                print("等待下家出牌", end="")
                while len(rightCards) == 0 and pass_flag is None and len(my_cards) > 0 and order is None:
                    if not self.RunGame:
                        break
                    print(".", end="")
                    time.sleep(0.3)
                    order = self.check_order(1)
                    pass_flag = helper.LocateOnScreen('buchu', region=self.RPassPos)
                    rightCards = find_other_cards(self.RPlayedCardsPos)
                    my_cards = find_my_cards()
                    self.detect_start_btn()
                if order is None:
                    if len(my_cards) == 0:
                        print()
                        print("王炸")
                        self.other_played_cards_real = "DX"

                    elif pass_flag is not None:
                        self.other_played_cards_real = ""

                    else:
                        while True:
                            if not self.RunGame:
                                break
                            rightOne = find_other_cards(self.RPlayedCardsPos)
                            time.sleep(0.2)
                            rightTwo = find_other_cards(self.RPlayedCardsPos)

                            if rightOne == rightTwo and len(rightOne) > 0:
                                self.other_played_cards_real = rightOne
                                break
                            self.detect_start_btn()

                    print("\n下家出牌：", self.other_played_cards_real if self.other_played_cards_real else "pass")
                    print()
                    self.other_played_cards_env = [RealCard2EnvCard[c] for c in list(self.other_played_cards_real)]
                    self.other_played_cards_env.sort()
                    self.env.step(self.user_position, self.other_played_cards_env)
                    self.right_cards_display.emit(
                        self.other_played_cards_real if self.other_played_cards_real else "pass")
                    self.other_hands_cards_str = subtract_strings(self.other_hands_cards_str,
                                                                  self.other_played_cards_real)
                    self.recorder_display.emit(self.other_hands_cards_str)
                    time.sleep(0.2)
                    if self.other_played_cards_real == "DX":
                        my_cards = find_my_cards()
                        while len(my_cards) == 0:
                            if not self.RunGame:
                                break
                            time.sleep(0.3)
                            my_cards = find_my_cards()
                            self.detect_start_btn()
                        self.play_order = 2
                        self.env.step(self.user_position, [])
                        self.play_order = 0
                        self.env.step(self.user_position, [])
                        self.play_order = 1
                    else:
                        self.play_order = 2

            if self.play_order == 2:
                self.left_cards_display.emit("等待上家出牌")
                leftCards = find_other_cards(self.LPlayedCardsPos)
                if len(leftCards) > 0:
                    time.sleep(1)

                order = self.check_order(2)
                pass_flag = helper.LocateOnScreen('buchu', region=self.LPassPos)
                leftCards = find_other_cards(self.LPlayedCardsPos)
                my_cards = find_my_cards()
                print("等待上家出牌", end="")
                while len(leftCards) == 0 and pass_flag is None and len(my_cards) > 0 and order is None:
                    if not self.RunGame:
                        break
                    print(".", end="")
                    time.sleep(0.3)
                    order = self.check_order(2)
                    pass_flag = helper.LocateOnScreen('buchu', region=self.LPassPos)
                    leftCards = find_other_cards(self.LPlayedCardsPos)
                    my_cards = find_my_cards()
                    self.detect_start_btn()

                if order is None:
                    if len(my_cards) == 0:
                        print()
                        print("王炸")
                        self.other_played_cards_real = "DX"

                    elif pass_flag is not None:
                        self.other_played_cards_real = ""

                    else:
                        while True:
                            if not self.RunGame:
                                break
                            leftOne = find_other_cards(self.LPlayedCardsPos)
                            time.sleep(0.2)
                            leftTwo = find_other_cards(self.LPlayedCardsPos)

                            if leftOne == leftTwo and len(leftOne) > 0:
                                self.other_played_cards_real = leftOne
                                break
                            self.detect_start_btn()

                    print("\n上家出牌：", self.other_played_cards_real if self.other_played_cards_real else "pass")
                    self.other_played_cards_env = [RealCard2EnvCard[c] for c in list(self.other_played_cards_real)]
                    self.other_played_cards_env.sort()
                    self.env.step(self.user_position, self.other_played_cards_env)
                    self.left_cards_display.emit(
                        self.other_played_cards_real if self.other_played_cards_real else "pass")
                    self.other_hands_cards_str = subtract_strings(self.other_hands_cards_str,
                                                                  self.other_played_cards_real)
                    self.recorder_display.emit(self.other_hands_cards_str)
                    time.sleep(0.2)
                    if self.other_played_cards_real == "DX":
                        my_cards = find_my_cards()
                        while len(my_cards) == 0:
                            if not self.RunGame:
                                break
                            time.sleep(0.3)
                            my_cards = find_my_cards()
                            self.detect_start_btn()
                        self.play_order = 0
                        self.env.step(self.user_position, [])
                        self.play_order = 1
                        self.env.step(self.user_position, [])
                        self.play_order = 2
                    else:
                        self.play_order = 0

        print("游戏结束")
        print()
        self.init_interface.emit(1)
        time.sleep(1)

    def check_order(self, current_order):
        num1 = ocr_cards_num(self.TimerPos[0])
        num2 = ocr_cards_num(self.TimerPos[1])
        tip_btn = helper.LocateOnScreen("tip_btn", region=self.GeneralBtnPos)
        if current_order == 2:
            cards = find_other_cards(self.LPlayedCardsPos)
            if len(cards) == 0:
                if tip_btn:
                    self.env.step(self.user_position, [])
                    self.play_order = 0
                    return True
                elif num2 != 0:
                    self.env.step(self.user_position, [])
                    self.play_order = 0
                    self.env.step(self.user_position, [])
                    self.play_order = 1
                    return True

        elif current_order == 1:
            cards = find_other_cards(self.RPlayedCardsPos)
            if len(cards) == 0:
                if num1 != 0:
                    self.env.step(self.user_position, [])
                    self.play_order = 2
                    return True
                elif tip_btn:
                    self.env.step(self.user_position, [])
                    self.play_order = 2
                    self.env.step(self.user_position, [])
                    self.play_order = 0
                    return True
        else:
            if tip_btn is None:
                if num2 != 0:
                    self.env.step(self.user_position, [])
                    self.play_order = 1
                    return True
                elif num1 != 0:
                    self.env.step(self.user_position, [])
                    self.play_order = 1
                    self.env.step(self.user_position, [])
                    self.play_order = 2
                    return True

    def find_landlord(self):
        user_position_code = None
        num_left = ocr_cards_num(self.blue_cards_num[0])
        num_right = ocr_cards_num(self.blue_cards_num[1])
        if (num_left == 17 or num_left > 17) and (num_right == 17 or num_right > 17):
            if num_left > 17:
                user_position_code = 2
            elif num_right > 17:
                user_position_code = 0
            elif num_left == 17 and num_right == 17:
                user_position_code = 1
        return user_position_code


class MyPyQT_Form(QtWidgets.QWidget, Ui_Form):
    def __init__(self):
        super(MyPyQT_Form, self).__init__()
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowMinimizeButtonHint |  # 使能最小化按钮
                            QtCore.Qt.WindowStaysOnTopHint |  # 窗体总在最前端
                            QtCore.Qt.WindowCloseButtonHint)
        self.setWindowIcon(QIcon(':/pics/favicon.ico'))
        self.setWindowTitle("JJ斗地主自动  v1.2")
        self.setFixedSize(self.width(), self.height())  # 固定窗体大小
        self.move(20, 20)
        window_pale = QtGui.QPalette()

        self.setPalette(window_pale)
        play_sound("music/2.wav")
        self.setFixedSize(self.width(), self.height())  # 固定窗体大小
        self.move(20, 20)
        window_pale = QtGui.QPalette()

        self.setPalette(window_pale)
        self.HandButton.clicked.connect(self.hand_game)
        self.AutoButton.clicked.connect(self.auto_game)
        self.StopButton.clicked.connect(self.stop)
        self.ResetButton.clicked.connect(self.init_threshold)

        self.read_threshold()
        self.Players = [self.RPlayedCard, self.PredictedCard, self.LPlayedCard]
        self.thread = Worker()
        self.thread.auto_game.connect(self.auto_game)
        self.thread.hand_game.connect(self.hand_game)
        self.thread.init_interface.connect(self.init_interface)
        self.thread.player_display.connect(self.player_display)
        self.thread.state_display.connect(self.state_display)
        self.thread.three_cards_display.connect(self.three_cards_display)
        self.thread.bid_display.connect(self.bid_display)
        self.thread.stop.connect(self.stop)
        self.thread.winrate_display.connect(self.winrate_display)
        self.thread.pre_cards_display.connect(self.pre_cards_display)
        self.thread.left_cards_display.connect(self.left_cards_display)
        self.thread.right_cards_display.connect(self.right_cards_display)
        self.thread.recorder_display.connect(self.cards_recorder)
        self.thread.write_threshold.connect(self.write_threshold)

    def hand_game(self, result):
        helper.ClickOnImage("once_more", region=(660, 600, 340, 130))
        self.thread.auto_sign = False
        self.thread.start()
        self.AutoButton.setStyleSheet('background-color: none;')
        self.HandButton.setStyleSheet('background-color: rgba(255, 85, 255, 0.5);')

    def auto_game(self, result):
        helper.ClickOnImage("once_more", region=(660, 600, 340, 130))
        self.thread.auto_sign = True
        self.thread.start()

        self.AutoButton.setStyleSheet('background-color: rgba(255, 85, 255, 0.5);')
        self.HandButton.setStyleSheet('background-color: none;')

    def stop(self, result):
        print()
        print("停止线程")
        self.thread.terminate()
        self.init_interface(1)
        self.AutoButton.setStyleSheet('background-color: none;')
        self.HandButton.setStyleSheet('background-color: none;')

    def player_display(self, result):
        for player in self.Players:
            player.setStyleSheet('background-color: rgba(0, 255, 0, 0);')
        self.Players[result].setStyleSheet('background-color: rgba(0, 255, 0, 0.5);')

    def init_threshold(self):
        self.bid_lineEdit_1.setText("-0.5")
        self.bid_lineEdit_2.setText("0")
        self.bid_lineEdit_3.setText("0.8")
        self.bid_lineEdit_4.setText("1.15")

        data = {'bid1': self.bid_lineEdit_1.text(), 'bid2': self.bid_lineEdit_2.text(),
                'bid3': self.bid_lineEdit_3.text(), 'bid4': self.bid_lineEdit_4.text()}
        write_json(data)

    def write_threshold(self, result):
        data = {'bid1': self.bid_lineEdit_1.text(), 'bid2': self.bid_lineEdit_2.text(),
                'bid3': self.bid_lineEdit_3.text(), 'bid4': self.bid_lineEdit_4.text()}
        write_json(data)

    def read_threshold(self):
        data = read_json()
        self.bid_lineEdit_1.setText(data['bid1'])
        self.bid_lineEdit_2.setText(data['bid2'])
        self.bid_lineEdit_3.setText(data['bid3'])
        self.bid_lineEdit_4.setText(data['bid4'])

    def init_interface(self, result):
        self.WinRate.setText("评分")
        self.WinRate.setStyleSheet('background-color: none;')
        self.label.setText("游戏状态")
        self.BidWinrate.setText("得分:")
        self.label.setStyleSheet('background-color: none;')
        self.UserHandCards.setText("手牌")
        self.LPlayedCard.setText("上家出牌区域")
        self.RPlayedCard.setText("下家出牌区域")
        self.PredictedCard.setText("AI出牌区域")
        self.ThreeLandlordCards.setText("底牌")
        self.recorder2zero()
        for player in self.Players:
            player.setStyleSheet('background-color: none;')

    def state_display(self, result):
        self.label.setText(result)
        self.label.setStyleSheet('background-color: rgba(255, 0, 0, 0.5);')

    def my_cards_display(self, result):
        self.UserHandCards.setText(result)

    def three_cards_display(self, result):
        self.ThreeLandlordCards.setText(result)

    def bid_display(self, result):
        self.BidWinrate.setText(result)

    def pre_cards_display(self, result):
        self.PredictedCard.setText(result)
        self.PredictedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0.5);')
        self.LPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')
        self.RPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')

    def left_cards_display(self, result):
        self.LPlayedCard.setText(result)
        self.PredictedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')
        self.LPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0.5);')
        self.RPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')

    def right_cards_display(self, result):
        self.RPlayedCard.setText(result)
        self.PredictedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')
        self.LPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0);')
        self.RPlayedCard.setStyleSheet('background-color: rgba(0, 255, 0, 0.5);')

    def winrate_display(self, result):
        self.WinRate.setText(result)
        self.WinRate.setStyleSheet('background-color: rgba(255, 85, 0, 0.4);')

    def cards_recorder(self, result):
        for i in range(15):
            char = AllCards[i]
            num = result.count(char)
            newItem = QTableWidgetItem(str(num))
            newItem.setTextAlignment(Qt.AlignHCenter)
            self.tableWidget.setItem(0, i, newItem)

    def recorder2zero(self):
        for i in range(15):
            newItem = QTableWidgetItem("0")
            newItem.setTextAlignment(Qt.AlignHCenter)
            self.tableWidget.setItem(0, i, newItem)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    main = MyPyQT_Form()
    style_file = QFile("style.qss")
    stream = QTextStream(style_file)
    style_sheet = stream.readAll()
    main.setStyleSheet(style_sheet)
    main.show()
    sys.exit(app.exec_())
