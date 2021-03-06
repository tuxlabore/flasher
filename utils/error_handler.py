import traceback
from discord.ext import commands
import discord
import datetime
from utils.errors import *
import asyncio


class CommandErrorHandler(commands.Cog):
    """Error handler"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        ignored = commands.CommandNotFound
        error = getattr(error, "original", error)

        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            embed = discord.Embed(
                description="Команда отключена", color=discord.Colour.dark_red()
            )
            return await ctx.send(embed=embed)

        elif isinstance(error, commands.BadArgument):
            ctx.command.reset_cooldown(ctx)
            await ctx.invoke(self.bot.get_command("help"), command=str(ctx.command))
            return

        elif isinstance(error, commands.UserInputError):
            ctx.command.reset_cooldown(ctx)
            await ctx.invoke(self.bot.get_command("help"), command=str(ctx.command))
            return

        await ctx.message.add_reaction("🚫")  # The reaction will be not added for errors upper

        if isinstance(error, commands.NotOwner):

            await ctx.send(
                embed=discord.Embed(
                    timestamp=ctx.message.created_at,
                    description=":warning: Эта команда может быть исполнена только владельцем бота.",
                    color=discord.Colour.dark_red(),
                ).set_footer(text=self.bot.user.name)
            )
            return

        elif isinstance(error, commands.NoPrivateMessage):

            await ctx.send(
                embed=discord.Embed(
                    timestamp=ctx.message.created_at,
                    description=":warning: Эта команда может быть исполнена только на серверах.",
                    color=discord.Colour.dark_red(),
                ).set_footer(text=self.bot.user.name)
            )
            return


        elif isinstance(error, commands.errors.CommandOnCooldown):
            retry_after = str(datetime.timedelta(seconds=int(error.retry_after)))
            await ctx.send(
                embed=discord.Embed(
                    timestamp=ctx.message.created_at,
                    description=f":clock: Вы можете использовать эту комманду через {retry_after}",
                    color=discord.Colour.dark_red(),
                ).set_footer(text=self.bot.user.name)
            )
            return

        elif isinstance(error, commands.errors.MissingPermissions):
            i = 0
            perms = []
            for perm in error.missing_perms:
                i += 1
                p = f"{i}. {perm}"
                if i != len(error.missing_perms):
                    p += ";"
                perms.append(p)
            perms = "\n".join(perms)
            await ctx.send(
                embed=discord.Embed(
                    timestamp=ctx.message.created_at,
                    title="Для исполнения этой комманды вы должны обладать следующими правами:",
                    description=f"```md\n{perms}\n```",
                    color=discord.Colour.dark_red(),
                ).set_footer(text=self.bot.user.name)
            )
            return

        elif isinstance(error, commands.NSFWChannelRequired):
            await ctx.send(
                embed=discord.Embed(
                    timestamp=ctx.message.created_at,
                    description="Эту комманду можно исполнять только в канале с пометкой NSFW",
                    color=discord.Colour.red(),
                ).set_footer(text=self.bot.user.name)
            )
            return

        elif isinstance(error, discord.Forbidden):
            perms = discord.Permissions(error.code)
            needperms = [
                x
                for x in dir(perms)
                if not x.startswith("_")
                if getattr(perms, x) == True
            ]
            strperms = []
            i = 0
            for perm in needperms:
                i += 1
                r = f"{i}. {perm}"
                if i != len(needperms):
                    r += ";"
                strperms.append(r)
            strperms = "\n".join(strperms)

            await ctx.send(
                embed=discord.Embed(
                    timestamp=ctx.message.created_at,
                    title="Боту должны быть предоставлены следующие права для выполнения этой команды:",
                    description=f"```md\n{strperms}\n```",
                    color=discord.Colour.dark_red(),
                ).set_footer(text=self.bot.user.name)
            )
            return

        elif isinstance(error, TooManyTries):
            ctx.command.reset_cooldown(ctx)
            await ctx.send(
                f"> Исполнение команды `{ctx.command.name}` вызваной {ctx.author.mention} было остановлено по причине слишком большого количества попыток ввести аргумент"
            )
            return

        elif isinstance(error, asyncio.TimeoutError):
            ctx.command.reset_cooldown(ctx)
            await ctx.send(
                f"> Исполнение команды `{ctx.command.name}` вызваной {ctx.author.mention} было остановлено по причине слишком большого использованого времени что бы ввести аргумент"
            )
            return

        elif isinstance(error, CanceledByUser):
            ctx.command.reset_cooldown(ctx)
            await ctx.send(
                f"> Исполнение команды `{ctx.command.name}` вызваной {ctx.author.mention} было остановлено автором сообщения"
            )
            return

        elif isinstance(error, PrefixTooLong):
            ctx.command.reset_cooldown(ctx)
            await ctx.send("> Значение префикса не может быть больше чем 7 символов!")
            return


        elif isinstance(error, commands.errors.CheckFailure):                                    # Invokes only if user blacklisted
            await ctx.send('%s, вы находитесь в чёрном списке бота.' % ctx.author.mention,       # (or by admin cog, but commands.NotOwner will be already invoked)
                delete_after=10)

        err = "\n".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        chn = await self.bot.fetch_channel(self.bot.config["bugReportChannel"])

        try:
            await chn.send(
                embed=discord.Embed(
                    title="Вызвана ошибка",
                    description=
                    f"""Комманда: `{ctx.command}`
                    Вызвана в: {ctx.channel} (вызвана {ctx.author})
                    Сообщение: ```\n{ctx.message.content}\n```\nКод ошибки:\n```py\n{err}\n```"""))
        finally:

            try:
                await ctx.send(
                    embed=discord.Embed(
                        title="Кажется я состолкнулся с ошибкой",
                        description=f"Если вы считаете что эта ошибка важная свяжитесь с разработчиком.\n```py\n{err}```",
                        color=discord.Colour.dark_red(),
                    )
                )
            finally:
                pass
        


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
