# -*- coding: utf-8 -*-
import datetime
import discord
import gspread
import json
import os
import requests
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
lol_worksheet = server_doc.worksheet('lolUserInformation')
'''


# Heroku
# 구글 스프레드 시트 연결
async def sync_spread():
    try:
        scopes = ['https://spreadsheets.google.com/feeds',
                  'https://www.googleapis.com/auth/drive']
        json_creds = os.getenv("GOOGLE_KEYS")
        creds_dict = json.loads(json_creds)
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\\\n", "\n")
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
        gc = gspread.authorize(creds)
        server_doc = gc.open_by_url(
            'https://docs.google.com/spreadsheets/d/1ApYrdcjAM-b3Zd9vSKjDfdFSNyK_4AiTrGFwCognK48/edit?usp=sharing')
        return server_doc

    # 문제가 생기면 에러 로그를 출력합니다.
    except Exception as e:
        -1


# 시간 얻기
async def date():
    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d')


async def time():
    now = datetime.datetime.now()
    return now.strftime('%H:%M:%S')


# 길드에 들어 올 때
async def guild_join(guild):
    server_doc = await sync_spread()
    server_worksheet = server_doc.worksheet('serverInformation')
    server_worksheet.insert_row([str(guild.owner.id), str(guild.text_channels[0].id), '0'], 2)


# 명령어 성공 했을 때
async def log(type, executed_command, guild_name, guild_id, author, author_id):
    server_doc = await sync_spread()
    log_worksheet = server_doc.worksheet('serverLog')
    log_worksheet.insert_row([type, await date(), await time(), executed_command, guild_name, guild_id, author, author_id], 2)


# 롤 정보 등록
async def set_lol_info(ctx, lol_nickname, ability):
    server_doc = await sync_spread()
    lol_worksheet = server_doc.worksheet('lolUserInformation')
    # Duplicate Registration
    if await is_sign_up(ctx) is not None:
        duplicate_registration = discord.Embed(title="중복 등록", description=ctx.message.author.mention +
                                                                          "\0이미 등록되어 있는 유저입니다.", color=0xFF0000)
        return duplicate_registration
    else:
        URL = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + lol_nickname
        # res = requests.get(URL, headers={"X-Riot-Token": os.environ["LOL_TOKEN"]})
        res = requests.get(URL, headers={"X-Riot-Token": 'RGAPI-08e170df-672a-42e9-9d4f-29f645da8006'})
        # Normal
        if res.status_code == 200:
            lol_worksheet.insert_row([str(ctx.message.author.id), str(lol_nickname), str(ability)], 2)
            register_complete = discord.Embed(title="등록 완료",
                                              description=ctx.message.author.mention + '\0등록이 완료되었습니다.',
                                              colour=discord.Colour.green())
            return register_complete
        # Not Found Summoner
        elif res.status_code == 404:
            not_found_user = discord.Embed(title="존재하지 않는 소환사", description=ctx.message.author.mention +
                                                                            "존재하지 않는 소환사 입니다.", color=0xFF0000)
            return not_found_user
        # Need Regenerate
        elif res.status_code == 403:
            need_regenerate = discord.Embed(title="토큰 재인증 필요", description="개발자가 개을러서 재인증을 하지 않았습니다.\n"
                                                                           "버튼을 눌러 재인증을 알려주세요!", color=0xFF0000)
            return need_regenerate


# 등록 되어있는지 확인하기 (ture: return col_num false: return None)
async def is_sign_up(ctx):
    server_doc = await sync_spread()
    lol_worksheet = server_doc.worksheet('lolUserInformation')
    try:
        if lol_worksheet.find(str(ctx.message.author.id)):
            split_col = str(lol_worksheet.find(str(ctx.message.author.id))).split()
            split_col = split_col[1].split('R')
            split_col = split_col[1].split('C')
            return int(split_col[0])
    except gspread.exceptions.CellNotFound:
        return None


# 등록 되어있는 롤 유저 정보 삭제하기 (true: return 1 false: col_num(None))
async def modify_lol_info(ctx):
    server_doc = await sync_spread()
    lol_worksheet = server_doc.worksheet('lolUserInformation')
    col_num = await is_sign_up(ctx)
    if col_num > 0:
        lol_worksheet.delete_row(col_num)
        return 1
    else:
        return col_num


# 스프레드시트 롤 정보 불러오기
async def get_ablity_score(user_list):
    server_doc = await sync_spread()
    lol_worksheet = server_doc.worksheet('lolUserInformation')
    ablity_dic = {}
    user_id = lol_worksheet.col_values(1)
    user_ablity = lol_worksheet.col_values(3)
    for user in user_list:
        ablity_dic[user] = int(user_ablity[user_id.index(str(user))])
    return ablity_dic
