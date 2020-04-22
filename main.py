# import discord
from discord.ext import commands
import sqlite3
# import os
# from karma_card.createcard import create_card


KEY = open("keys.txt", "r").readline().split("=")[1]
bot = commands.Bot(command_prefix="$")
conn = sqlite3.connect("votecount.db")
c = conn.cursor()


@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")


@bot.event
async def on_guild_join(guild):
    server_id = str(guild.id)

    sql_query = f"""
    CREATE TABLE IF NOT EXISTS data_{server_id} (
    USER_ID   INTEGER (0, 18),
    UPVOTES   INTEGER (0, 8),
    DOWNVOTES INTEGER (0, 8)
    );"""
    c.execute(sql_query)

    sql_query = f"""
    CREATE TABLE IF NOT EXISTS settings_{server_id} (
    UPVOTE_ID   STRING (0, 56),
    RT_ID   STRING (0, 56),
    DOWNVOTE_ID STRING (0, 56)
    );"""
    c.execute(sql_query)

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send("Hello! To get started, type out your desired reaction emotes as such:\n$setup <:upvote:452121917462151169> <:rt:451882250884218881> <:downvote:451890347761467402>")
            break


@commands.has_permissions(administrator=True)
@bot.command()
async def setup(ctx):
    upvote_id = ctx.message.content.split(" ")[1]
    downvote_id = ctx.message.content.split(" ")[2]
    rt_id = ctx.message.content.split(" ")[3]
    print(upvote_id, downvote_id, rt_id)

    sql_query = f"DELETE FROM settings_{ctx.guild.id}"
    c.execute(sql_query)
    conn.commit()

    sql_query = f"""
    INSERT INTO settings_{ctx.guild.id}
    VALUES('{upvote_id}', '{rt_id}', '{downvote_id}'
    );"""
    c.execute(sql_query)
    conn.commit()


bot.run(KEY)
