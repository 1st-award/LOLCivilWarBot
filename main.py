import asyncio
import discord
import random
from discord.ext import commands

# 프로젝트 모듈
from server import *

# 봇 권한 부여
intents = discord.Intents(messages=True, guilds=True, members=True)
bot = commands.Bot(command_prefix='!', intents=intents)
# 롤 내전에 필요한 변수
join_member = []
''' Test member
join_member = [111111111111111111, 33333333333333, 2222222222222222, 44444444444444,
               55555555555555555, 6666666666666, 7777777777777777, 77888888888888888, 999999999999999999]
'''
member_join_msg = []
button_msg = None


# 봇 준비
@bot.event
async def on_ready():
    print(f"봇 이름: {bot.user.name}")
    for guilds in bot.guilds:
        print(str(guilds.owner_id))
    print("-" * 30)


# 봇이 길드에 들어갔을 때
@bot.event
async def on_guild_join(guild):
    # from server_send.py
    guild_join(guild)
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send('롤 내전 봇이 참여했습니다. 명령어는 !help입니다.', delete_after=10.0)
        break


@bot.command(brief="내전을 시작합니다! 준비버튼을 눌러주세요!")  # Create a command inside a cog
async def 내전시작(ctx):
    global member_join_msg, join_member, button_msg
    await ctx.message.delete()
    if button_msg is not None:
        await ctx.send(ctx.message.author.mention + " 이미 내전을 시작했습니다!", delete_after=5.0)
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
            # Already join member use button
            if is_sign_up(interaction.user.id) == 0:
                msg = await interaction.message.channel.send(
                    interaction.user.mention + "님은 등록이 되어있지 않은 유저입니다.\t!등록을 먼저 해주세요.")
                member_join_msg.append(msg)
            elif interaction.user.id in join_member:
                msg = await interaction.message.channel.send(interaction.user.mention + "님은 이미 참여하셨습니다.")
                member_join_msg.append(msg)
            # Maximum 10 user
            elif number + 1 == 10:
                msg = await interaction.message.channel.send(interaction.user.mention + "님이 참여했습니다!")
                appendINFO(msg, interaction.user.id)
                print(interaction.user.id)
                print(interaction.user.mention)
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
                msg = await interaction.message.channel.send(interaction.user.mention + "님이 참여했습니다!")
                appendINFO(msg, interaction.user.id)
                # Make sure to update the message with our updated selves
                await interaction.response.edit_message(view=self)

    button_msg = await ctx.send(content="참가 버튼을 눌러주세요! 한번 참여하면 취소를 못하니 신중하게 눌러 주세요!", view=JoinCivilWar())


@bot.command(brief="내전 참가 중 다른 사람이 버튼을 눌렀거나 불가피한 상황이 생겼을 경우 다시 시작합니다.")
async def 다시(ctx):
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
        await ctx.send(ctx.message.author.mention + " 초기화를 완료했습니다. 처음부터 다시 시작해주세요!", delete_after=10.0)
    except AttributeError:
        await ctx.send(ctx.message.author.mention + " 내전이 시작되지 않았습니다.", delete_after=10.0)
    except discord.ext.errors.CommandInvokeError:
        join_member = []
        member_join_msg = []
        await button_msg.delete()
        button_msg = None
        await ctx.send(ctx.message.author.mention + " 초기화를 완료했습니다. 처음부터 다시 시작해주세요!", delete_after=10.0)


@bot.command(brief="유저 정보를 등록합니다. !등록 [롤 닉네임] [티어]를 입력해주세요! 티어는 롤 티어가 아닌 실력 티어로 0~10사이의 숫자를 입력해 주세요!")
async def 등록(ctx):
    await ctx.message.delete()
    try:
        msg = ctx.message.content.split()
        if 0 <= int(msg[2]) <= 10:
            await ctx.send(ctx.message.author.mention + set_lol_info(ctx.message.author.id, msg[1], msg[2]),
                           delete_after=5.0)
        else:
            await ctx.send("1~10중 하나를 입력해주세요", delete_after=5.0)
    except AttributeError and ValueError:
        await ctx.send(ctx.message.author.mention + " 형식이 잘못되었습니다.", delete_after=5.0)


@bot.command()
async def 참가완료(ctx):
    await ctx.message.delete()
    global member_join_msg
    if len(join_member) != 10:
        await ctx.send("내전이 시작되지 않았거나, 참가 인원이 10명이 아닙니다.", delete_after=5.0)
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
        if 0 <= abs(sum(blue_team_point) / len(blue_team_point) - sum(red_team_point) / len(blue_team_point)) <= 0.25:
            break
    await msg.delete()
    embed = discord.Embed(title="결과", description="블루팀 평균: " + str(sum(blue_team_point) / len(blue_team_point)) +
                                                  "\0레드팀 평균: " + str(sum(red_team_point) / len(blue_team_point)),
                          color=0xffffff)
    for blue in blue_team:
        embed.add_field(name="블루팀", value='<@!' + str(blue) + '>', inline=False)
    embed.add_field(name='=================================', value='=================================', inline=False)
    for red in red_team:
        embed.add_field(name="레드팀", value='<@!' + str(red) + '>', inline=False)

    msg = await ctx.send(embed=embed)
    member_join_msg.append(msg)

bot.run(os.environ["BOT_TOKEN"])
