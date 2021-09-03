import asyncio
import random
from discord.ext import commands

# 프로젝트 모듈
import main
from server import *

# 롤 내전에 필요한 변수
join_member = []
''' Test member
join_member = [111111111111111111, 33333333333333, 2222222222222222, 44444444444444,
               55555555555555555, 6666666666666, 7777777777777777, 77888888888888888, 999999999999999999] 
'''
member_join_msg = []
button_msg = None


class LOL(commands.Cog, name="롤 내전 명령어"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="내전시작", help="내전을 시작합니다! 준비버튼을 눌러주세요!", usage="`!내전시작`")
    async def start_join(self, ctx):
        global member_join_msg, join_member, button_msg
        await ctx.message.delete()
        if button_msg is not None:
            already_start = discord.Embed(title="오류 발생",
                                          description=ctx.message.author.mention + "\0이미 내전을 시작했습니다.", color=0xFF0000)
            await ctx.send(embed=already_start, delete_after=5.0)
            return

        def appendINFO(msg_log, member):
            member_join_msg.append(msg_log)
            join_member.append(member)

        class JoinCivilWar(discord.ui.View):
            number = 0

            # Define the actual button
            # When pressed, this increments the number displayed until it hits 5.
            # When it hits 5, the counter button is disabled and it turns green.
            # note: The name of the function does not matter to the library
            @discord.ui.button(label="참가", style=discord.ButtonStyle.red)
            async def count(self, button: discord.ui.Button, interaction: discord.Interaction):
                self.number += 1
                # No Register
                is_sign_up_result = await is_sign_up(ctx.author.id)
                if isinstance(is_sign_up_result, discord.Embed):
                    await interaction.message.channel.send(embed=is_sign_up_result, delete_after=5.0)
                # Already join member use button
                elif interaction.user.id in join_member:
                    already_join = discord.Embed(title="중복 참여",
                                                 description=ctx.message.author.mention + "님은 이미 참여하셨습니다.",
                                                 color=0xFF0000)
                    await interaction.message.channel.send(embed=already_join, delete_after=5.0)
                # Maximum 10 user
                elif self.number == 10:
                    user_ready = discord.Embed(title="준비 완료", description=ctx.message.author.mention + "님이 참여했습니다!",
                                               colour=discord.Colour.green())
                    msg = await interaction.message.channel.send(embed=user_ready)
                    appendINFO(msg, interaction.user.id)
                    button.style = discord.ButtonStyle.green
                    button.disabled = True
                    button.label = "참가 신청이 종료되었습니다! '!참가완료'를 입력해주세요."
                    # Make sure to update the message with our updated selves
                    await interaction.response.edit_message(view=self)
                    start_game.title = "내전 시작!!\t\t현재 참여 인원: 10"
                    start_game.colour = discord.Colour.dark_green()
                    await interaction.edit_original_message(embed=start_game)
                    # Delete join message after 30sec
                    await asyncio.sleep(30)
                    for delete_msg in member_join_msg:
                        await delete_msg.delete()
                        # Overrun prevention cool time
                        await asyncio.sleep(0.3)
                # Less than 10 user
                else:
                    user_ready = discord.Embed(title="준비 완료", description=ctx.message.author.mention + "님이 참여했습니다!",
                                               colour=discord.Colour.green())
                    msg = await interaction.message.channel.send(embed=user_ready)
                    appendINFO(msg, interaction.user.id)
                    # Make sure to update the message with our updated selves
                    await interaction.response.edit_message(view=self)
                    start_game.title = "내전 시작!!\t\t현재 참여 인원: " + str(self.number)
                    await interaction.edit_original_message(embed=start_game)

        start_game = discord.Embed(title="내전 시작!!\t\t현재 참여 인원: 0",
                                   description="참가 버튼을 눌러주세요! 한번 참여하면 취소를 못하니 신중하게 눌러 주세요!",
                                   colour=discord.Colour.blurple())
        button_msg = await ctx.send(embed=start_game, view=JoinCivilWar())

    @commands.command(name="참가완료", help="유저 10명이 채워졌을 때 밸런스를 맞춰 팀을 짜 줍니다.", usage="`!참가완료`")
    async def create_balance_team(self, ctx):
        await ctx.message.delete()
        global member_join_msg
        if len(join_member) != 10:
            not_enough_user = discord.Embed(title="인원 부족 오류", description="내전이 시작되지 않았거나, 참가 인원이 10명이 아닙니다.",
                                            color=0xFF0000)
            await ctx.send(embed=not_enough_user, delete_after=5.0)
            return
        user_dic = await get_ability_score(join_member)
        msg = await ctx.send("팀을 만듭니다...")
        # Create a Bellance Team
        while True:
            blue_team_point = []
            red_team = []
            red_team_point = []
            # Put 5 user in the blue team randomly
            blue_team = random.sample(list(user_dic), 5)
            # Users outside the Blue Team
            for red in user_dic:
                if red not in blue_team:
                    red_team.append(red)
            # Get the blue team's ability
            for ability in blue_team:
                blue_team_point.append(user_dic.get(ability))
            # Get the red team's ability
            for ability in red_team:
                red_team_point.append(user_dic.get(ability))
            # Team average difference between 0 and 0.25
            if 0 <= abs(
                    sum(blue_team_point) / len(blue_team_point) - sum(red_team_point) / len(blue_team_point)) <= 0.25:
                break
        await msg.delete()
        embed = discord.Embed(title="결과", description="블루팀 평균: " + str(sum(blue_team_point) / len(blue_team_point)) +
                                                      "\0레드팀 평균: " + str(sum(red_team_point) / len(blue_team_point)),
                              color=0xffffff)
        for blue in blue_team:
            embed.add_field(name="블루팀", value='<@!' + str(blue) + '>', inline=False)
        embed.add_field(name='=================================', value='=================================',
                        inline=False)
        for red in red_team:
            embed.add_field(name="레드팀", value='<@!' + str(red) + '>', inline=False)

        msg = await ctx.send(embed=embed)
        member_join_msg.append(msg)

    @commands.command(name="다시", help="내전 참가 중 다른 사람이 버튼을 눌렀거나\n불가피한 상황이 생겼을 경우 다시 시작합니다.", usage="`!다시`")
    async def reset_game(self, ctx):
        global join_member, member_join_msg, button_msg
        await ctx.message.delete()
        try:
            for delete_msg in member_join_msg:
                await delete_msg.delete()
                # Overrun prevention cool time
                await asyncio.sleep(0.3)
            join_member = []
            member_join_msg = []
            await button_msg.delete()
            button_msg = None
            reset_clear = discord.Embed(title="초기화 완료",
                                        description=ctx.message.author.mention + "\0초기화를 완료했습니다.\0처음부터 다시 시작해주세요!",
                                        colour=discord.Colour.blurple())
            await ctx.send(embed=reset_clear, delete_after=10.0)
        except AttributeError:
            not_yet_start = discord.Embed(title="초기화 오류", description=ctx.message.author.mention + "\0내전이 시작되지\0않았습니다.",
                                          color=0xFF0000)
            await ctx.send(embed=not_yet_start, delete_after=10.0)
        except discord.ext.errors.CommandInvokeError:
            join_member = []
            member_join_msg = []
            await button_msg.delete()
            button_msg = None
            reset_clear = discord.Embed(title="초기화 완료",
                                        description=ctx.message.author.mention + "\0초기화를 완료했습니다.\0처음부터 다시 시작해주세요!",
                                        colour=discord.Colour.blurple())
            await ctx.send(embed=reset_clear, delete_after=10.0)

    # Get Guild Member Dictionary
    async def get_member_dict(self, guild_id):
        member_dict = {}
        for member in self.bot.get_guild(guild_id).members:
            # 봇이 아니라면 dict 추가
            if not member.bot:
                # 서버 별명이 있다면 별명으로 추가
                if member.nick:
                    member_dict[member.nick] = member.id
                # 없다면 디스코드 별명으로 추가
                else:
                    member_dict[member.name] = member.id
        return member_dict

    # Set UserInfo
    async def set_user_info(self, user_info, member_dict):
        user_info_list = []

        class UserInfo:
            def __init__(self, user_id, user_lol_id, ability):
                self.user_id = user_id
                self.user_lol_id = user_lol_id
                self.ability = ability

        try:
            for i in range(1, len(user_info), 3):
                # 티어 범위가 0 ~ 10일 때 코드 실행
                # user_info[i]: user_id, user_info[i+1]: user_lol_id, user_info[i+2]: ability
                if 0 <= int(user_info[i + 2]) <= 10:
                    # 'user_nick'에 _가 포함되어있으면 공백으로 변환
                    user_info[i] = user_info[i].replace('_', ' ')
                    # 'user_lol_id'에 _가 포함되어있으면 공백으로 변환
                    user_info[i+1] = user_info[i+1].replace('_', ' ')
                    # 'member_dict'에 'user_nick'이 있으면
                    if member_dict[user_info[i]]:
                        user_info_list.append(UserInfo(member_dict[user_info[i]], user_info[i + 1], user_info[i + 2]))
                # 범위 밖이면 범위 오류 return
                else:
                    return discord.Embed(title="티어 범위 오류", description="1~10중 하나를 입력해주세요", color=0xFF0000)
            return user_info_list
        except (KeyError, ValueError):
            return discord.Embed(title="형식 오류", description="닉네임에 공백이 있으면 `_`를 넣어주세요!", color=0xFF0000)

    # LOL INFO Registration
    async def register(self, ctx, register_type):
        try:
            msg = ctx.message.content.split()
            # 등록 2명 이상
            if len(msg) > 3:
                member_dict = await self.get_member_dict(ctx.guild.id)
                register_list = await self.set_user_info(msg, member_dict)
                # 공백 닉네임에 '_'를 안채워 넣엇을 시 발생하는 애러에 대해서 전송 이때 모든 활동 정지
                if isinstance(register_list, discord.Embed):
                    await ctx.send(embed=register_list, delete_after=5.0)
                    return
                result_title = []
                result_description = []
                for member in register_list:
                    result = await set_lol_info(member.user_id, member.user_lol_id, member.ability)
                    if isinstance(result, discord.Embed):
                        if result.title == "토큰 재인증 필요":
                            await main.on_command_error(ctx, "봇 토큰 재인증 필요")
                        else:
                            result_title.append(result.title)
                            result_description.append(result.description)
                register_result = discord.Embed(title="등록 결과", description="다음과 같이 완료되었습니다.",
                                                colour=discord.Colour.blurple())
                # Add result
                member_dict = dict(map(reversed, member_dict.items()))
                for i in range(len(result_title)):
                    user_mention = result_description[i].split(" ")
                    result_description[i] = result_description[i].replace(user_mention[0], member_dict[
                        int(user_mention[0].strip("<@{}>"))])
                    register_result.add_field(name=result_title[i], value=result_description[i])
                await ctx.send(embed=register_result, delete_after=20.0)

            # 등록 한 명
            elif 0 <= int(msg[2]) <= 10:
                result = await set_lol_info(ctx.author.id, msg[1], msg[2])
                if result.title == "토큰 재인증 필요":
                    await main.on_command_error(ctx, "봇 토큰 재인증 필요")
                else:
                    if register_type == "수정" and result.title == "등록 완료":
                        result.title = "수정 완료"
                        result.description = ctx.message.author.mention + '\0수정이 완료되었습니다.'
                    await ctx.send(embed=result, delete_after=5.0)
            # Out Of Range
            else:
                out_of_range = discord.Embed(title="티어 범위 오류", description="1~10중 하나를 입력해주세요", color=0xFF0000)
                await ctx.send(embed=out_of_range, delete_after=5.0)
        except (AttributeError, ValueError, IndexError):
            attribute_error = discord.Embed(title="형식 오류",
                                            description="형식이 잘못되었습니다.\n`!등록`\t`[롤 닉네임]`\t`[티어]`를 입력해주세요!",
                                            color=0xFF0000)
            await ctx.send(embed=attribute_error, delete_after=7.0)

    @commands.command(name="등록",
                      help="유저 정보를 등록합니다. !등록 [롤 닉네임] [티어]를 입력해주세요!\n"
                           "한 명이 여러 명 등록하고 싶을 경우.\n"
                           "!등록 [체널 닉네임1] [롤 닉네임1] [티어1] [체널 닉네임2] [롤 닉네임2] [티어2]\n"
                           "이름에 공백이 포함되어 있는 경우 공백에 `_`를 넣어주세요!\n"
                           "티어는 롤 티어가 아닌 실력 티어로 0~10사이의 숫자를 입력해 주세요!",
                      usage="`!등록`\0`롤 닉네임`\0`1~10사이의 실력`")
    async def registration(self, ctx):
        await ctx.message.delete()
        await self.register(ctx, "등록")

    @commands.command(name="수정", help="`등록`에서 적엇던 정보를 수정합니다.", usage="`!수정`\0`롤 닉네임`\0`1~10사이의 실력`")
    async def modify_lol_info(self, ctx):
        await ctx.message.delete()
        delete_result = await delete_lol_info(ctx.author.id)
        if isinstance(delete_result, discord.Embed):
            await ctx.send(embed=delete_result, delete_after=5.0)
        # delete success
        elif delete_result == 1:
            await self.register(ctx, "수정")

    @commands.command(name="정보", help="내 정보를 불러옵니다.", usage="`!정보`")
    async def my_information(self, ctx):
        await ctx.message.delete()
        user_info = await get_lol_info(ctx.author.id)
        # 서칭 중 에러가 return 됐을 때
        if isinstance(user_info, discord.Embed):
            await ctx.send(embed=user_info, delete_after=5.0)
        else:
            embed = discord.Embed(title=ctx.message.author.nick + "님의 정보", colour=discord.Colour.blurple(),
                                  timestamp=discord.utils.utcnow())
            embed.set_thumbnail(
                url="https://ddragon.leagueoflegends.com/cdn/11.15.1/img/profileicon/" + str(user_info[0]) + ".png")
            embed.set_author(name=ctx.author, icon_url=ctx.author.avatar.url)
            embed.add_field(name="`롤 닉네임`", value=user_info[1])
            embed.add_field(name="`롤 레벨`", value=str(user_info[2]))
            # Dummy embed
            embed.add_field(name="\u200b", value="\u200b")
            # embed.add_field(name="`최근 10게임 승/패`", value=str(user_info[3]) + "승\0" + str(user_info[4]) + "패",
            #                 inline=False)
            embed.add_field(name="`내전 게임 승/패`", value=str(user_info[3]) + "승\0" + str(user_info[4]) + "패")
            embed.add_field(name="`내전 레벨`", value=str(user_info[5]))
            embed.set_footer(icon_url=ctx.bot.user.avatar.url, text=ctx.bot.user)
            view = discord.ui.View()
            item = discord.ui.Button(style=discord.ButtonStyle.link, label="자세한 내용",
                                     url="https://www.op.gg/summoner/userName=" + user_info[1])
            view.add_item(item=item)
            await ctx.send(embed=embed, view=view, delete_after=60.0)


def setup(bot):
    bot.add_cog(LOL(bot))
