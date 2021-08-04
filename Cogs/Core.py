import discord
from discord.ext import commands


class Core(commands.Cog, name="기본 명령어"):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="도움말", help="이 창을 출력합니다.", usage="`!도움말`")
    async def help_command(self, ctx, func=None):
        await ctx.message.delete()
        cog_list = ["기본 명령어", "롤 내전 명령어"]  # Cog 리스트 추가
        if func is None:
            embed = discord.Embed(title="롤 내전 봇 도움말",
                                  description="접두사는 `!` 입니다. 자세한 내용은 `!도움말`\0`명령어`를 입력하시면 됩니다.")  # Embed 생성
            for x in cog_list:  # cog_list에 대한 반복문
                cog_data = self.bot.get_cog(x)  # x에 대해 Cog 데이터를 구하기
                command_list = cog_data.get_commands()  # cog_data에서 명령어 리스트 구하기
                embed.add_field(name=x, value=" ".join([c.name for c in command_list]), inline=True)  # 필드 추가
            await ctx.send(embed=embed, delete_after=60.0)  # 보내기

        else:  # func가 None이 아니면
            command_notfound = True

            for _title, cog in self.bot.cogs.items():  # title, cog로 item을 돌려주는데 title은 필요가 없습니다.
                if not command_notfound:  # False면
                    break  # 반복문 나가기

                else:  # 아니면
                    for title in cog.get_commands():  # 명령어를 아까처럼 구하고 title에 순차적으로 넣습니다.
                        if title.name == func:  # title.name이 func와 같으면
                            cmd = self.bot.get_command(title.name)  # title의 명령어 데이터를 구합니다.
                            embed = discord.Embed(title=f"명령어 : {cmd}", description=cmd.help)  # Embed 만들기
                            embed.add_field(name="사용법", value=cmd.usage)  # 사용법 추가
                            await ctx.send(embed=embed, delete_after=30.0)  # 보내기
                            command_notfound = False
                            break  # 반복문 나가기
                        else:
                            command_notfound = True
            if command_notfound:  # 명령어를 찾지 못하면
                if func in cog_list:  # 만약 cog_list에 func가 존재한다면
                    cog_data = self.bot.get_cog(func)  # cog 데이터 구하기
                    command_list = cog_data.get_commands()  # 명령어 리스트 구하기
                    embed = discord.Embed(title=f"카테고리 : {cog_data.qualified_name}",
                                          description=cog_data.description)  # 카테고리 이름과 설명 추가
                    embed.add_field(name="명령어들",
                                    value=", ".join([c.name for c in command_list]))  # 명령어 리스트 join
                    await ctx.send(embed=embed, delete_after=30.0)  # 보내기
                else:
                    command_error = discord.Embed(title="명령어 오류", description="다음과 같은 에러가 발생했습니다.", color=0xFF0000)
                    command_error.add_field(name="사용한 명령어:\0" + ctx.message.content,
                                            value='`' + ctx.message.content + "`는 없습니다.", inline=False)
                    await ctx.send(embed=command_error, delete_after=7.0)


def setup(bot):
    bot.add_cog(Core(bot))
