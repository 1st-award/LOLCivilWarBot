# -*- coding: utf-8 -*-
import asyncio
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
# 롤 토큰
lol_token = "**"
'''

# Heroku
# 구글 스프레드 시트 연결
scopes = ['https://spreadsheets.google.com/feeds',
          'https://www.googleapis.com/auth/drive']
json_creds = os.getenv("GOOGLE_KEYS")
creds_dict = json.loads(json_creds)
creds_dict["private_key"] = creds_dict["private_key"].replace("\\\\n", "\n")
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
gc = gspread.authorize(creds)
server_doc = gc.open_by_url(os.environ["SERVER_URL"])
worksheet_list = ["serverInformation", "serverLog", "lolUserInformation"]
server_worksheet, log_worksheet, lol_worksheet = list(map(lambda x: server_doc.worksheet(x), worksheet_list))


# 시간 얻기
async def get_date():
    now = datetime.datetime.now()
    return now.strftime('%Y-%m-%d')


async def get_time():
    now = datetime.datetime.now()
    return now.strftime('%H:%M:%S')


# 길드에 들어 올 때
async def guild_join(guild):
    server_worksheet.insert_row([str(guild.owner.id), str(guild.text_channels[0].id), '0'], 2)


# 명령어 성공 했을 때
async def log(message_type, executed_command, guild_name, guild_id, author, author_id):
    log_worksheet.insert_row(
        [message_type, await get_date(), await get_time(), executed_command, guild_name, guild_id, author, author_id],
        2)


# 소환사 검색
async def search_summoner(lol_nickname, user_id):
    # 'lol_nickname'에 _가 있으면 공백으로 대체
    lol_nickname = lol_nickname.replace('_', ' ')
    URL = "https://kr.api.riotgames.com/lol/summoner/v4/summoners/by-name/" + lol_nickname
    res = requests.get(URL, headers={"X-Riot-Token": os.environ["LOL_TOKEN"]})
    # res = requests.get(URL, headers={"X-Riot-Token": lol_token})
    # Normal
    if res.status_code == 200:
        return res.json()
    # Not Found Summoner
    elif res.status_code == 404:
        return discord.Embed(title="존재하지 않는 소환사", description=f"<@{user_id}> 존재하지 않는 소환사 입니다.", color=0xFF0000)
    # Need Regenerate
    elif res.status_code == 403:
        return discord.Embed(title="토큰 재인증 필요", description="개발자가 개을러서 재인증을 하지 않았습니다.\n"
                                                            "버튼을 눌러 재인증을 알려주세요!", color=0xFF0000)


# 롤 정보 등록
async def set_lol_info(user_id, lol_nickname, ability):
    # Duplicate Registration
    result_is_sign_up = await is_sign_up(user_id)
    if isinstance(result_is_sign_up, int):
        return discord.Embed(title="중복 등록", description=f"<@{user_id}> 이미 등록되어 있는 유저입니다.", color=0xFF0000)

    # 소환사 검색에서 소환사의 정보가 있으면 google_spread에 유저를 등록
    result_search_summoner = await search_summoner(lol_nickname, user_id)
    if not isinstance(result_search_summoner, discord.embeds.Embed):
        # 'lol_nickname'에 _있으면 공백으로 대체
        lol_nickname = lol_nickname.replace('_', ' ')
        lol_worksheet.insert_row([str(user_id), str(lol_nickname), str(ability), 0, 0], 2)
        return discord.Embed(title="등록 완료",
                             description=f"<@{user_id}> 등록이 완료되었습니다.",
                             colour=discord.Colour.green())
    else:
        return result_search_summoner


# 등록 되어있는지 확인하기 (ture: return col_num false: return 등록 요구 embed)
async def is_sign_up(user_id):
    try:
        user = lol_worksheet.find(str(user_id))
        if isinstance(user, gspread.models.Cell):
            split_col = str(user).split()
            split_col = split_col[1].split('R')
            split_col = split_col[1].split('C')
            return int(split_col[0])
        else:
            return discord.Embed(title="등록 요구",
                                 description=f"<@{user_id}>님은 등록이 되어있지 않은 유저입니다.\n`!등록`을 먼저 해주세요.", color=0xFF0000)
    except Exception:
        return discord.Embed(title="등록 요구",
                             description=f"<@{user_id}>님은 등록이 되어있지 않은 유저입니다.\n`!등록`을 먼저 해주세요.", color=0xFF0000)


# 등록 되어있는 롤 유저 정보 삭제하기 (true: return 1 false: col_num(None))
async def delete_lol_info(user_id):
    col_num = await is_sign_up(user_id)
    if isinstance(col_num, discord.embeds.Embed):
        return col_num
    else:
        lol_worksheet.delete_row(col_num)
        return 1


# 스프레드시트 롤 정보 불러오기
async def get_ability_score(user_list):
    ability_dic = {}
    user_id = lol_worksheet.col_values(1)
    user_ability = lol_worksheet.col_values(3)
    for user in user_list:
        ability_dic[user] = int(user_ability[user_id.index(str(user))])
    return ability_dic


# 롤 개인 토큰이 초당 20 request, 2분당 100 request, 아직까진 쓰기에 무리가 있음
'''# 최근 10 게임 승/패 검색
async def count_win_defeat(user_ppuid):
    # 게임 정보 찾기
    class SearchGame:
        def __init__(self, stop):
            self.count = 0
            self.stop = stop

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.count < self.stop:
                # 각 매치 당 승, 패 검색
                EACH_MATCH_URL = "https://asia.api.riotgames.com/lol/match/v5/matches/" + match_info[self.count]
                each_match_res = requests.get(EACH_MATCH_URL, headers={"X-Riot-Token": os.environ["LOL_TOKEN"]})
                # each_match_res = requests.get(EACH_MATCH_URL, headers={"X-Riot-Token": lol_token})
                self.count += 1
                return each_match_res.json()
            else:
                raise StopAsyncIteration

    # 게임 정보에서 유저와 같은 아이디를 찾아서 승/패 count하기
    class CountWinDefeat:
        def __init__(self, stop):
            self.count = 0
            self.stop = stop

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.count < self.stop:
                if each_match_info["info"]["participants"][self.count]["puuid"] == user_ppuid:
                    self.count += 1
                    if each_match_info["info"]["participants"][self.count]["win"]:
                        return 1
                    else:
                        return -1
                else:
                    self.count += 1
            else:
                raise StopAsyncIteration

    # 최근 게임 10개 검색
    win = defeat = 0
    MATCH_URL = "https://asia.api.riotgames.com/lol/match/v5/matches/by-puuid/" + user_ppuid + "/ids?start=0&count=10"
    match_res = requests.get(MATCH_URL, headers={"X-Riot-Token": os.environ["LOL_TOKEN"]})
    # match_res = requests.get(MATCH_URL, headers={"X-Riot-Token": lol_token})
    match_info = match_res.json()
    async for each_match_info in SearchGame(10):
        async for game_result in CountWinDefeat(len(each_match_info["info"]["participants"])):
            # 한 게임에 유저를 찾지 못했을 때 None을 Return 하므로 break를 각각의 if문에 넣어줘야한다
            if game_result == 1:
                win += 1
                break
            elif game_result == -1:
                defeat += 1
                break
    return win, defeat'''


# 스프레드 시트에 있는 정보 가져오기
async def get_lol_worksheet_information(user_id_col):
    # 요청한 유저의 디스코드 id를 이용해서 유저의 행 가져오기
    user_info = lol_worksheet.row_values(user_id_col)
    # 롤 닉네임 / 승 / 패 return
    return user_info[1], user_info[3], user_info[4], user_info[2]


# 롤 정보 불러오기
async def get_lol_info(user_id):
    user_id_col = await is_sign_up(user_id)
    # 만약 유저를 찾을 수 없을 때(return이 등록 요구일 때) embed를 return
    if isinstance(user_id_col, discord.Embed):
        return user_id_col
    # lol_nickname = lol_worksheet.acell('B' + str(user_id_col)).value
    # 스프레드 시트 정보 가져오기
    lol_nickname, win, defeat, ability = await get_lol_worksheet_information(user_id_col)
    # 유저 기본 정보 검색 (프로필, 레벨, puuid)
    lol_info = await search_summoner(lol_nickname, user_id)
    # 정상적으로 유저 서칭이 되었을 때 (return 200을 받앗을 때)
    if isinstance(lol_info, dict):
        user_profile_icon = lol_info["profileIconId"]
        user_level = lol_info["summonerLevel"]
        # user_ppuid = lol_info["puuid"]
        # win, defeat = await count_win_defeat(user_ppuid)
        return [user_profile_icon, lol_nickname, user_level, win, defeat, ability]
    # 정상적으로 값을 찾지 못했을 때 (오류 Embed가 들어왔을 때)
    elif isinstance(lol_info, discord.Embed):
        return lol_info
