# -*- coding: utf-8 -*-
import datetime
import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials

'''
# PC
# 구글 스프레드 시트 연결
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
]
# gc = gspread.service_account(filename='google api 설정 하면서 내려 받아진 파일명')
gc = gspread.service_account(filename='discordlolcivilwar.json')
# 스프레스시트 문서 가져오기
server_doc = gc.open_by_url(
    'https://docs.google.com/spreadsheets/d/1ApYrdcjAM-b3Zd9vSKjDfdFSNyK_4AiTrGFwCognK48/edit?usp=sharing')
# 시트 선택하기
server_worksheet = server_doc.worksheet('serverInformation')
log_worksheet = server_doc.worksheet('serverLog')

'''

# Heroku
# 구글 스프레드 시트 연결
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/drive',
]
json_creds = os.getenv("GOOGLE_KEYS")
creds_dict = json.loads(json_creds)
creds_dict["privatekey"] = creds_dict["private_key"].replace("\\\\n", "\n")
credentials = ServiceAccountCredentials.from_json_keyfile_name(creds_dict, scope)
gc = gspread.authorize(credentials)
coin_server_url = os.getenv("SERVER_URL")
# 스프레스시트 문서 가져오기
server_doc = gc.open_by_url(coin_server_url)
# 시트 선택하기
server_worksheet = server_doc.worksheet('serverInformation')
log_worksheet = server_doc.worksheet('serverLog')
lol_worksheet = server_doc.worksheet('lolUserInformation')


# 시간 얻기
def date():
    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d')


def time():
    now = datetime.datetime.now()
    return now.strftime('%H:%M:%S')


# 길드에 들어 올 때
def guild_join(guild):
    server_count = int(server_worksheet.acell('J1').value)
    server_worksheet.insert_row([str(guild.owner.id), str(guild.text_channels[0].id), '0'], server_count)
    server_worksheet.update_acell('J1', server_count + 1)


# 롤 정보 등록
def set_lol_info(user_id, lol_id, ability):
    result = is_sign_up(user_id)
    if result == 1:
        return "이미 등록되어있는 유저입니다."
    else:
        count_line = int(lol_worksheet.acell('J1').value)
        lol_worksheet.insert_row([str(user_id), str(lol_id), str(ability)], count_line)
        server_worksheet.update_acell('J1', count_line + 1)
        return " 등록이 완료되었습니다."


# 등록 되어있는지 확인하기
def is_sign_up(user_id):
    try:
        if lol_worksheet.find(str(user_id)):
            return 1
    except gspread.exceptions.CellNotFound:
        return 0


# 롤 정보 불러오기
def get_ablity_score(user_list):
    ablity_dic = {}
    user_id = lol_worksheet.col_values(1)
    user_ablity = lol_worksheet.col_values(3)
    for user in user_list:
        ablity_dic[user] = int(user_ablity[user_id.index(str(user))])
    return ablity_dic


# 명령어 성공 했을 때
def log(type, executed_command, guild_name, guild_id, author, author_id):
    count_server = int(log_worksheet.acell('J1').value)
    log_worksheet.insert_row(
        [type, date(), time(), executed_command, guild_name, guild_id, author, author_id], count_server)
    log_worksheet.update_acell('J1', count_server + 1)
