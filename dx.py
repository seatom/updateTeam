import base64
import datetime
import os
import requests
import sys
from notify import send

KEY_OF_COOKIE = "Phone"

host = "http://119.91.192.69:9876"

msg = []


def logout(self):
    print("[{0}]: {1}".format(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), self))
    sys.stdout.flush()


def telecom_task(config):
    mobile = config['mobile']
    logout("{} 开始执行任务...".format(mobile))
    h5_headers = get_h5_headers(mobile)
    # 签到
    sign_body = requests.get(url="{}/telecom/getSign".format(host), params={"mobile": mobile}).json()
    sign_ret = requests.post(url="https://wapside.189.cn:9001/jt-sign/api/home/sign", json=sign_body,
                             headers=h5_headers).json()
    if sign_ret['data']['code'] == 1:
        logout("签到成功, 本次签到获得 " + str(sign_ret['data']['coin']) + " 豆")
        msg.append("签到成功, 本次签到获得 " + str(sign_ret['data']['coin']) + " 豆")
    else:
        logout("签到结果 " + sign_ret['data']['msg'])
        msg.append("签到结果 " + sign_ret['data']['msg'])

    # 获取用户中心
    home_info_body = requests.get(url="{}/telecom/getHomeInfoSign".format(host), params={"mobile": mobile}).json()
    home_info_ret = requests.post(url="https://wapside.189.cn:9001/jt-sign/api/home/homeInfo", json=home_info_body,
                                  headers=h5_headers).json()
    new_coin = home_info_ret['data']['userInfo']['totalCoin']
    msg.append("【" + str(mobile) + "】" + "领取完毕, 现有金豆: " + str(new_coin))
    logout("【" + str(mobile) + "】" + "领取完毕, 现有金豆: " + str(new_coin))
    # 喂食
    food(config)

    # 签到7天领取话费
    convert_reward(config)
    msg.append("----------------------------------------------")


def food(config):
    if config['food']:
        mobile = config['mobile']
        msg.append(mobile + " 开始执行喂食...")
        while True:
            food_body = requests.get(url="{}/telecom/getPhoneSign".format(host), params={"mobile": mobile}).json()
            food_ret = requests.post(url="https://wapside.189.cn:9001/jt-sign/paradise/food", json=food_body,
                                     headers=get_h5_headers(mobile)).json()
            logout(food_ret['resoultMsg'])
            msg.append(food_ret['resoultMsg'])
            if food_ret['resoultCode'] != '0':
                break


def convert_reward(config):
    mobile = config['mobile']
    msg.append(mobile + " 开始执行满7天兑换话费...")
    phone_body = requests.get(url="{}/telecom/getPhoneSign".format(host), params={"mobile": mobile}).json()
    activity_ret = requests.post(url="https://wapside.189.cn:9001/jt-sign/reward/activityMsg", json=phone_body,
                                 headers=get_h5_headers(mobile)).json()
    msg.append("你已连续签到 " + str(activity_ret['totalDay']) + " 天")
    logout("你已连续签到 " + str(activity_ret['totalDay']) + " 天")
    if activity_ret['recordNum'] > 0:
        # 可以领取
        reward_id = activity_ret['date']['id']
        params = {
            "mobile": mobile,
            "rewardId": reward_id
        }
        reward_body = requests.get(url="{}/telecom/getConvertReward".format(host), params=params).json()
        reward_ret = requests.post(url="https://wapside.189.cn:9001/jt-sign/reward/convertReward", json=reward_body,
                                   headers=get_h5_headers(mobile)).json()
        if reward_ret['code'] == '0':
            logout(reward_ret['msg'])
            msg.append(reward_ret['msg'])


def get_h5_headers(mobile):
    base64_mobile = str(base64.b64encode(mobile[5:11].encode('utf-8')), 'utf-8').strip(r'=+') + "!#!" + str(
        base64.b64encode(mobile[0:5].encode('utf-8')), 'utf-8').strip(r'=+')
    return {"User-Agent": "CtClient;9.2.0;Android;10;MI 9;" + base64_mobile}


def format_msg():
    str1 = ''
    for item in msg:
        str1 += str(item) + "\r\n"
    return str1


if __name__ == '__main__':
    Phone = os.environ[KEY_OF_COOKIE]
    phoneList = Phone.split("@")
    logout("==========共有 {} 个号码==========".format(len(phoneList)))
    index = 0
    for phoneConfig in phoneList:
        foodBol = False
        if phoneConfig.split("#")[1] == 'True':
            foodBol = True
        phone = str(phoneConfig.split("#")[0])
        logout("第 {} 个号码： {}, 是否喂食： {}".format(index + 1, phone, foodBol))
        config = {"mobile": str(phoneConfig.split("#")[0]), "food": foodBol}
        telecom_task(config)
        index += 1
    content = format_msg()
    send('电信签到', content)
