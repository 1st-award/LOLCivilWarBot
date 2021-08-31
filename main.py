import discord
import traceback
from discord.ext import commands

# 프로젝트 모듈
from server import *

# 봇 권한 부여
intents = discord.Intents(messages=True, guilds=True, members=True)
bot = commands.Bot(command_prefix='!', intents=intents)
# !도움말을 위한 기존에 있는 help 제거
bot.remove_command('help')

# Cogs Load
for filename in os.listdir("Cogs"):
    if filename.endswith(".py"):
        bot.load_extension(f"Cogs.{filename[:-3]}")


# 봇 준비
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="!도움말"))
    print(f"봇 이름: {bot.user.name}")
    for guilds in bot.guilds:
        print(str(guilds.owner_id))
    print("-" * 30)


# 봇이 길드에 들어갔을 때
@bot.event
async def on_guild_join(guild):
    # from server_send.py
    await guild_join(guild)
    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send('롤 내전 봇이 참여했습니다. 명령어는 !도움말입니다.', delete_after=10.0)
        break


# 명령어가 성공했을 때 로그에 전송
@bot.event
async def on_command_completion(ctx):
    full_command_name = ctx.command.qualified_name
    split = full_command_name.split(" ")
    executed_command = str(split[0])
    # from server_send.py
    await log('INFO', executed_command, ctx.guild.name,
              str(ctx.message.guild.id), str(ctx.message.author), str(ctx.message.author.id))


# 명령어가 실패했을 때 개발자에게 전송
@bot.event
async def on_command_error(ctx, error):
    # Command Not Found
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        command_error = discord.Embed(title="명령어 오류", description="다음과 같은 에러가 발생했습니다.", color=0xFF0000)
        command_error.add_field(name="사용한 명령어:\0" + ctx.message.content,
                                value='`' + ctx.message.content + "`는 없습니다.", inline=False)
        await ctx.send(embed=command_error, delete_after=7.0)
        return

    # embed는 최대 1200자
    # Logical Error
    # traceback_text = ''.join(traceback.format_exception(type(error), error, error.__traceback__))
    class ClickButton(discord.ui.View):
        @discord.ui.button(label="에러 전송하기", style=discord.ButtonStyle.red)
        async def click_send(self, button: discord.ui.Button, interaction: discord.Interaction):
            # 봇 오너
            bot_owner = bot.get_user(276532581829181441)
            button.disabled = True
            button.label = "전송이 완료되었습니다. 감사합니다."
            await interaction.response.edit_message(view=self)
            embed = discord.Embed(title="에러발생 일해라", description="다음과 같은 에러가 발생했습니다.", color=0xFF0000)
            embed.add_field(name="사용한 명령어:\0" + ctx.message.content, value=error, inline=False)
            await bot_owner.send(embed=embed)
            await interaction.delete_original_message()

    critical_error = discord.Embed(title="치명적인 에러", description="치명적인 에러가 발생했습니다! 개발자 일감을 주기 위해 전송 버튼을 눌러주세요!",
                                   color=0xFF0000)
    await ctx.send(embed=critical_error, view=ClickButton())
    # await ctx.send(f"치명적인 에러발생\t사용한 명령어: {ctx.command}\n```py\n{traceback.format_exception(type(error), error,
    # error.__traceback__)}```")

@bot.command(name="로드")
@commands.has_permissions(administrator=True)
async def load_commands(extension):
    # 봇 오너
    bot_owner = bot.get_user(276532581829181441)
    bot.load_extension(f"Cogs.{extension}")
    await bot_owner.send(f":white_check_mark: {extension}을(를) 로드했습니다!")


@bot.command(name="언로드")
@commands.has_permissions(administrator=True)
async def unload_commands(extension):
    # 봇 오너
    bot_owner = bot.get_user(276532581829181441)
    bot.unload_extension(f"Cogs.{extension}")
    await bot_owner.send(f":white_check_mark: {extension}을(를) 언로드했습니다!")


@bot.command(name="리로드")
@commands.has_permissions(administrator=True)
async def reload_commands(extension=None):
    # 봇 오너
    bot_owner = bot.get_user(276532581829181441)
    if extension is None:  # extension이 None이면 (그냥 !리로드 라고 썼을 때)
        for filename in os.listdir("Cogs"):
            if filename.endswith(".py"):
                bot.unload_extension(f"Cogs.{filename[:-3]}")
                bot.load_extension(f"Cogs.{filename[:-3]}")
        await bot_owner.send(":white_check_mark: 모든 명령어를 다시 불러왔습니다!")
    else:
        bot.unload_extension(f"Cogs.{extension}")
        bot.load_extension(f"Cogs.{extension}")
        await bot_owner.send(f":white_check_mark: {extension}을(를) 다시 불러왔습니다!")


bot.run(os.environ["BOT_TOKEN"])
