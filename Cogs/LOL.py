import asyncio
import random
from discord.ext import commands

# 프로젝트 모듈
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
            # Define the actual button
            # When pressed, this increments the number displayed until it hits 5.
            # When it hits 5, the counter button is disabled and it turns green.
            # note: The name of the function does not matter to the library
            @discord.ui.button(label="참가인원: 0", style=discord.ButtonStyle.blurple)
            async def count(self, button: discord.ui.Button, interaction: discord.Interaction):
                number = int(button.label[-1]) if button.label else 0
                # No Register
                if is_sign_up(interaction.user.id) == None:
                    require_regist = discord.Embed(title="등록 요구",
                                                   description=ctx.message.author.mention + "님은 등록이 되어있지 않은 유저입니다.\n`!등록`을 먼저 해주세요.",
                                                   color=0xFF0000)
                    await interaction.message.channel.send(embed=require_regist, delete_after=5.0)
                # Already join member use button
                elif interaction.user.id in join_member:
                    already_join = discord.Embed(title="중복 참여",
                                                 description=ctx.message.author.mention + "님은 이미 참여하셨습니다.",
                                                 color=0xFF0000)
                    await interaction.message.channel.send(embed=already_join, delete_after=5.0)
                # Maximum 10 user
                elif number + 1 == 10:
                    user_ready = discord.Embed(title="준비 완료", description=ctx.message.author.mention + "님이 참여했습니다!",
                                               color=0x98FB98)
                    msg = await interaction.message.channel.send(embed=user_ready)
                    appendINFO(msg, interaction.user.id)
                    button.style = discord.ButtonStyle.green
                    button.disabled = True
                    button.label = "참가 신청이 종료되었습니다! '!참가완료'를 입력해주세요."
                    # Make sure to update the message with our updated selves
                    await interaction.response.edit_message(view=self)
                    # Delete join message after 30sec
                    await asyncio.sleep(30)
                    for delete_msg in member_join_msg:
                        await delete_msg.delete()
                        # Overrun prevention cool time
                        await asyncio.sleep(0.3)
                # Less than 10 user
                else:
                    button.label = "참가인원: " + str(number + 1)
                    user_ready = discord.Embed(title="준비 완료", description=ctx.message.author.mention + "님이 참여했습니다!",
                                               color=0x98FB98)
                    msg = await interaction.message.channel.send(embed=user_ready)
                    appendINFO(msg, interaction.user.id)
                    # Make sure to update the message with our updated selves
                    await interaction.response.edit_message(view=self)

        start_game = discord.Embed(title="내전 시작",
                                   description="참가 버튼을 눌러주세요! 한번 참여하면 취소를 못하니 신중하게 눌러 주세요!", color=0x6495ED)
        button_msg = await ctx.send(embed=start_game, view=JoinCivilWar())

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
                                        color=0x98FB98)
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
                                        color=0x98FB98)
            await ctx.send(embed=reset_clear, delete_after=10.0)

    @commands.command(name="등록",
                      help="유저 정보를 등록합니다. !등록 [롤 닉네임] [티어]를 입력해주세요!\n티어는 롤 티어가 아닌 실력 티어로 0~10사이의 숫자를 입력해 주세요!",
                      usage="`!등록`\0`롤 닉네임`\0`1~10사이의 실력`")
    async def registration(self, ctx):
        await ctx.message.delete()
        try:
            msg = ctx.message.content.split()
            if 0 <= int(msg[2]) <= 10:
                result = set_lol_info(ctx, ctx.message.author.id, msg[1], msg[2])

                if result.title == "토큰 재인증 필요":
                    author = self.bot.get_user(276532581829181441)

                    class ClickReport(discord.ui.View):
                        @discord.ui.button(label="에러 전송하기", style=discord.ButtonStyle.red)
                        async def click_report(self, button: discord.ui.Button, interaction: discord.Interaction):
                            button.disabled = True
                            button.label = "전송이 완료되었습니다. 감사합니다."
                            await interaction.response.edit_message(view=self)
                            embed = discord.Embed(title="에러발생 일해라", description="롤 토큰 재인증 필요", color=0xFF0000)
                            await author.send(embed=embed)
                            await interaction.delete_original_message()

                    await ctx.send(embed=result, view=ClickReport())
                else:
                    await ctx.send(embed=result, delete_after=5.0)
            # Out Of Range
            else:
                out_of_range = discord.Embed(title="티어 범위 오류", description="1~10중 하나를 입력해주세요", color=0xFF0000)
                await ctx.send(embed=out_of_range, delete_after=5.0)
        except AttributeError and ValueError:
            attribute_error = discord.Embed(title="형식 오류",
                                            description="형식이 잘못되었습니다.\n`!등록`\t`[롤 닉네임]`\t`[티어]`를 입력해주세요!",
                                            color=0xFF0000)
            await ctx.send(embed=attribute_error, delete_after=7.0)

    @commands.command(name="참가완료", help="유저 10명이 채워졌을 때 밸런스를 맞춰 팀을 짜 줍니다.", usage="`!참가완료`")
    async def create_balance_team(self, ctx):
        await ctx.message.delete()
        global member_join_msg
        if len(join_member) != 10:
            not_enough_user = discord.Embed(title="인원 부족 오류", description="내전이 시작되지 않았거나, 참가 인원이 10명이 아닙니다.",
                                            color=0xFF0000)
            await ctx.send(embed=not_enough_user, delete_after=5.0)
            return
        user_dic = get_ablity_score(join_member)
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
            # Get the blue team's ablity
            for ablity in blue_team:
                blue_team_point.append(user_dic.get(ablity))
            # Get the red team's ablity
            for ablity in red_team:
                red_team_point.append(user_dic.get(ablity))
            # Team average difference between 0 and 0.05
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


def setup(bot):
    bot.add_cog(LOL(bot))
