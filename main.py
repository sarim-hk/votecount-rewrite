import discord
from discord import NotFound
from discord.ext import commands
from karma_card.createcard import create_card
import sqlite3
import help_cmds


KEY = open("keys.txt", "r").readline().split("=")[1]

debug_mode = False
bot = commands.Bot(command_prefix="$")
bot.remove_command("help")

conn = sqlite3.connect("votecount.db")
c = conn.cursor()
print("Database initialised")

sql_query = f"""
CREATE TABLE IF NOT EXISTS user_data (
USER_ID         INTEGER (0, 18),
KARMA_TEMPLATE  TEXT    (0, 20),
KARMA_COLOUR    TEXT    (0, 5),
GIVEN_TEMPLATE  TEXT    (0, 20),
GIVEN_COLOUR    TEXT    (0, 5)
);"""
c.execute(sql_query)


@bot.event
async def on_ready():
    print(f"logged in as {bot.user}")


@bot.event
async def on_guild_join(guild):
    sql_query = f"""
    CREATE TABLE IF NOT EXISTS data_{guild.id} (
    USER_ID   INTEGER (0, 18),
    UPVOTES   INTEGER (0, 8),
    DOWNVOTES INTEGER (0, 8),
    UPVOTES_GIVEN   INTEGER (0, 8),
    DOWNVOTES_GIVEN INTEGER (0, 8),
    BLACKLISTED INTEGER (0, 1)
    );"""
    c.execute(sql_query)

    sql_query = f"""
    CREATE TABLE IF NOT EXISTS settings_{guild.id} (
    UPVOTE_ID   STRING (0, 56),
    RT_ID   STRING (0, 56),
    DOWNVOTE_ID STRING (0, 56)
    );"""
    c.execute(sql_query)

    for channel in guild.text_channels:
        if channel.permissions_for(guild.me).send_messages:
            await channel.send("Hello! To get started, type out your desired reaction emotes as such:\n$setup <:upvote:452121917462151169> <:downvote:451890347761467402> <:rt:451882250884218881>\nIf you don't have an RT emote, just replace it with 'NONE'")
            break


@commands.has_permissions(administrator=True)
@bot.command()
async def debug(ctx):
    global debug_mode
    try:
        status = ctx.message.content.split(" ")[1]
    except IndexError:
        await ctx.message.channel.send(f"Debug mode is {debug_mode}")
    if status == "0":
        debug_mode = False
        await ctx.message.channel.send("Debug mode disabled")
    elif status == "1":
        debug_mode = True
        await ctx.message.channel.send("Debug mode enabled")


@commands.has_permissions(administrator=True)
@bot.command()
async def setup(ctx):
    upvote_id = ctx.message.content.split(" ")[1]
    downvote_id = ctx.message.content.split(" ")[2]
    rt_id = ctx.message.content.split(" ")[3]

    sql_query = f"DELETE FROM settings_{ctx.guild.id}"
    c.execute(sql_query)
    conn.commit()

    sql_query = f"""
    INSERT INTO settings_{ctx.guild.id}
    VALUES('{upvote_id}', '{rt_id}', '{downvote_id}'
    );"""
    c.execute(sql_query)
    conn.commit()

    await ctx.message.channel.send("Your reaction emotes have successfully been set!")


@commands.has_permissions(administrator=True)
@bot.command()
async def blacklist_add(ctx):
    if len(ctx.message.content.split(" ")) == 2:
        user_id = int(ctx.message.content.split(" ")[1].replace("<@", "").replace(">", "").replace("!", ""))
        sql_query = f"""
        UPDATE data_{ctx.message.guild.id}
        SET BLACKLISTED = 1
        WHERE USER_ID = {user_id}
        """
        c.execute(sql_query)
        conn.commit()
        await ctx.message.channel.send("User has been added to the blacklist.")


@commands.has_permissions(administrator=True)
@bot.command()
async def blacklist_remove(ctx):
    if len(ctx.message.content.split(" ")) == 2:
        user_id = int(ctx.message.content.split(" ")[1].replace("<@", "").replace(">", "").replace("!", ""))
        sql_query = f"""
        UPDATE data_{ctx.message.guild.id}
        SET BLACKLISTED = 0
        WHERE USER_ID = {user_id}
        """
        c.execute(sql_query)
        conn.commit()
        await ctx.message.channel.send("User has been removed from the blacklist.")


@commands.has_permissions(administrator=True)
@bot.command()
async def blacklist_view(ctx):
    message_string = ""
    sql_query = f"""
    SELECT USER_ID
    FROM data_{ctx.message.guild.id}
    WHERE BLACKLISTED = 1
    """
    c.execute(sql_query)
    user_data = c.execute(sql_query).fetchall()
    if debug_mode is True: print(user_data)

    for user_id in user_data:
        user = await bot.fetch_user(user_id[0])
        message_string += f"{user.name}#{user.discriminator}\n"

    try:
        await ctx.message.channel.send(message_string)
    except discord.errors.HTTPException:
        await ctx.message.channel.send("Blacklist is empty!")


@bot.command()
async def customise(ctx):
    if len(ctx.message.content.split(" ")) == 4:
        card_type = ctx.message.content.split(" ")[1].lower()
        template_name = ctx.message.content.split(" ")[2].lower()
        dark_light = ctx.message.content.split(" ")[3].lower()

        if card_type != "karma" and card_type != "given":
            await ctx.message.channel.send("Incorrect card type.")
            return
        elif dark_light != "dark" and dark_light != "light":
            await ctx.message.channel.send("Incorrect colour type.")
            return
    else:
        embed = help_cmds.help("$help customise", ctx.message)
        await ctx.message.channel.send(embed=embed)
        return

    sql_query = f"SELECT * FROM user_data WHERE USER_ID = {ctx.message.author.id}"
    user_data = c.execute(sql_query).fetchone()

    if user_data is None:
        if card_type == "karma":
            sql_query = f"""INSERT INTO user_data
                        (USER_ID, KARMA_TEMPLATE, KARMA_COLOUR, GIVEN_TEMPLATE, GIVEN_COLOUR)
                        VALUES ({ctx.message.author.id}, "{template_name}", "{dark_light}", "space", "light"
                        );"""
            c.execute(sql_query)
            conn.commit()

        elif card_type == "given":
            sql_query = f"""INSERT INTO user_data
                        (USER_ID, KARMA_TEMPLATE, KARMA_COLOUR, GIVEN_TEMPLATE, GIVEN_COLOUR)
                        VALUES ({ctx.message.author.id}, "blacksea", "dark", "{template_name}", "{dark_light}"
                        );"""
            c.execute(sql_query)
            conn.commit()
    else:
        if card_type == "karma":
            sql_query = f"""UPDATE user_data
                        SET KARMA_TEMPLATE = "{template_name}",
                            KARMA_COLOUR = "{dark_light}"
                        WHERE USER_ID = {ctx.message.author.id}
            """
            c.execute(sql_query)
            conn.commit()
        
        elif card_type == "given":
            sql_query = f"""UPDATE user_data
                        SET GIVEN_TEMPLATE = "{template_name}",
                            GIVEN_COLOUR = "{dark_light}"
                        WHERE USER_ID = {ctx.message.author.id}
            """
            c.execute(sql_query)
            conn.commit()


@bot.command()
async def help(ctx):
    try:
        embed, img = help_cmds.help(ctx.message.content.lower(), ctx.message, img=None)
    except Exception:
        embed = help_cmds.help(ctx.message.content.lower(), ctx.message, img=None)
        img = None
        
    if img is None:
        await ctx.message.channel.send(embed=embed)
    else:
        await ctx.message.channel.send(embed=embed, file=img)
    return


@bot.command()
async def karma(ctx):
    if len(ctx.message.content.split(" ")) == 1:
        user_id = ctx.message.author.id
        username = ctx.message.author.name
        avatar = ctx.message.author.avatar_url
    elif len(ctx.message.content.split(" ")) == 2:
        user_id = int(ctx.message.content.split(" ")[1].replace("<@", "").replace(">", "").replace("!", ""))
        user = ctx.message.guild.get_member(user_id)
        username = user.name
        avatar = user.avatar_url

    sql_query = f"SELECT KARMA_TEMPLATE, KARMA_COLOUR FROM user_data WHERE USER_ID = {user_id}"
    try:
        karma_template, karma_colour = c.execute(sql_query).fetchone()
    except TypeError:
        karma_template, karma_colour = "space", "light"
    sql_query = f"SELECT * FROM data_{ctx.message.guild.id} WHERE USER_ID = {user_id}"
    user_data = c.execute(sql_query).fetchone()
    if user_data is None:
        user_data = [0, 0, 0]

    create_card(user_data[1], user_data[2], username, avatar, karma_template, karma_colour)
    await ctx.message.channel.send(file=discord.File("card.png"))


@bot.command()
async def given(ctx):
    if len(ctx.message.content.split(" ")) == 1:
        user_id = ctx.message.author.id
        username = ctx.message.author.name
        avatar = ctx.message.author.avatar_url
    elif len(ctx.message.content.split(" ")) == 2:
        user_id = int(ctx.message.content.split(" ")[1].replace("<@", "").replace(">", "").replace("!", ""))
        user = ctx.message.guild.get_member(user_id)
        username = user.name
        avatar = user.avatar_url

    sql_query = f"SELECT GIVEN_TEMPLATE, GIVEN_COLOUR FROM user_data WHERE USER_ID = {user_id}"
    try:
        given_template, given_colour = c.execute(sql_query).fetchone()
    except TypeError:
        given_template, given_colour = "blacksea", "dark"

    sql_query = f"SELECT * FROM data_{ctx.message.guild.id} WHERE USER_ID = {user_id}"
    user_data = c.execute(sql_query).fetchone()
    if user_data is None:
        user_data = [0, 0, 0, 0, 0]

    create_card(user_data[3], user_data[4], username, avatar, given_template, given_colour)
    await ctx.message.channel.send(file=discord.File("card.png"))


@bot.event
async def on_raw_reaction_add(payload):
    upvoted, downvoted = 0, 0
    channel = bot.get_channel(payload.channel_id)
    try:
        msg = await channel.fetch_message(payload.message_id)
    except NotFound:
        if debug_mode is True: print("\n\nMessage not found.")
        return
    except Exception as e:
        if debug_mode is True: print(f"Unknown error.\n{e}")
        return
    if debug_mode is True: print("Message fetched.")

    # checks to see if it's a reaction on their own message
    if payload.user_id == msg.author.id:
        return
    if debug_mode is True: print("Not the same user.")

    # checks to see if reactor (person who reacted) is in blacklist
    sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {payload.user_id}"
    user_data = c.execute(sql_query).fetchone()
    try:
        if user_data[5] == 1:
            if debug_mode is True: print("USER IS BLACKLISTED.")
            return
    except TypeError:
        pass  # user doesnt exist in db, so cannot be in blacklist

    # gets server emotes and decides if it was an upvote or downvote
    sql_query = f"SELECT * FROM settings_{payload.guild_id}"
    server_emotes = c.execute(sql_query).fetchone()
    if str(payload.emoji) == server_emotes[0] or str(payload.emoji) == server_emotes[1]:
        upvoted = 1
    elif str(payload.emoji) == server_emotes[2]:
        downvoted = 1
    else:
        if debug_mode is True: print("SERVER EMOTES:", server_emotes, type(server_emotes[1]))
        if debug_mode is True: print("EMOTE USED:", str(payload.emoji), type(str(payload.emoji)))
        return
    if debug_mode is True: print("SERVER EMOTES:", server_emotes)
    if debug_mode is True: print("UPVOTED:", upvoted, "DOWNVOTED:", downvoted)

    # gets user data for the user who got reacted on
    sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {msg.author.id}"
    user_data = c.execute(sql_query).fetchone()
    if debug_mode is True: print("USER DATA:", user_data)
    if debug_mode is True: print("IF NONE, SPOT WILL BE ADDED")

    # if there is no user data, add a spot for them in the database
    if user_data is None:
        sql_query = f"""INSERT INTO data_{msg.guild.id}
                    (USER_ID, UPVOTES, DOWNVOTES, UPVOTES_GIVEN, DOWNVOTES_GIVEN, BLACKLISTED)
                    VALUES ({msg.author.id}, 0, 0, 0, 0, 0
                    );"""
        c.execute(sql_query)
        conn.commit()
        if debug_mode is True: print("EMPTY SPOT ADDED FOR MSG AUTHOR")

    # update their data, now that it definitely exists
    sql_query = f"""
    UPDATE data_{payload.guild_id}
    SET UPVOTES = UPVOTES + {upvoted},
        DOWNVOTES = DOWNVOTES + {downvoted}
    WHERE USER_ID = {msg.author.id}
    """
    c.execute(sql_query)
    conn.commit()
    if debug_mode is True: print("DATA UPDATED FOR MSG AUTHOR")

    # gets user data for the user who reacted
    sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {payload.user_id}"
    user_data = c.execute(sql_query).fetchone()

    # if there is no user data, add a spot for them in the database
    if user_data is None:
        sql_query = f"""
        INSERT INTO data_{msg.guild.id}
        (USER_ID, UPVOTES, DOWNVOTES, UPVOTES_GIVEN, DOWNVOTES_GIVEN, BLACKLISTED)
        VALUES({payload.user_id}, 0, 0, 0, 0, 0
        );"""
        c.execute(sql_query)
        conn.commit()
        if debug_mode is True: print("EMPTY SPOT ADDED FOR REACTOR")

    sql_query = f"""
    UPDATE data_{msg.guild.id}
    SET UPVOTES_GIVEN = UPVOTES_GIVEN + {upvoted},
        DOWNVOTES_GIVEN = DOWNVOTES_GIVEN + {downvoted}
    WHERE USER_ID = {payload.user_id}
    """
    c.execute(sql_query)
    conn.commit()
    if debug_mode is True: print("DATA UPDATED FOR MSG REACTOR")

    if debug_mode is True:
        sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {msg.author.id}"
        user_data = c.execute(sql_query).fetchone()
        print("AUTHOR DATA:", user_data)

        sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {payload.user_id}"
        user_data = c.execute(sql_query).fetchone()
        print("REACTOR DATA:", user_data)


@bot.event
async def on_raw_reaction_remove(payload):
    upvoted, downvoted = 0, 0
    channel = bot.get_channel(payload.channel_id)
    try:
        msg = await channel.fetch_message(payload.message_id)
    except NotFound:
        if debug_mode is True: print("\n\nMessage not found.")
        return
    except Exception as e:
        if debug_mode is True: print(f"Unknown error.\n{e}")
        return
    if debug_mode is True: print("Message fetched.")

    # checks to see if it's a reaction on their own message
    if payload.user_id == msg.author.id:
        return
    if debug_mode is True: print("Not the same user.")

    # checks to see if reactor (person who reacted) is in blacklist
    sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {payload.user_id}"
    user_data = c.execute(sql_query).fetchone()
    try:
        if user_data[5] == 1:
            if debug_mode is True: print("USER IS BLACKLISTED.")
            return
    except TypeError:
        pass  # user doesnt exist in db, so cannot be in blacklist

    # gets server emotes and decides if it was an upvote or downvote
    sql_query = f"SELECT * FROM settings_{payload.guild_id}"
    server_emotes = c.execute(sql_query).fetchone()
    if str(payload.emoji) == server_emotes[0] or str(payload.emoji) == server_emotes[1]:
        upvoted = 1
    elif str(payload.emoji) == server_emotes[2]:
        downvoted = 1
    else:
        if debug_mode is True: print("SERVER EMOTES:", server_emotes, type(server_emotes[1]))
        if debug_mode is True: print("EMOTE USED:", str(payload.emoji), type(str(payload.emoji)))
        return
    if debug_mode is True: print("SERVER EMOTES:", server_emotes)
    if debug_mode is True: print("UPVOTED:", upvoted, "DOWNVOTED:", downvoted)

    # gets user data for the user who got reacted on
    sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {msg.author.id}"
    user_data = c.execute(sql_query).fetchone()
    if debug_mode is True: print("USER DATA:", user_data)
    if debug_mode is True: print("IF NONE, SPOT WILL BE ADDED")

    # if there is no user data, add a spot for them in the database
    if user_data is None:
        sql_query = f"""INSERT INTO data_{msg.guild.id}
                    (USER_ID, UPVOTES, DOWNVOTES, UPVOTES_GIVEN, DOWNVOTES_GIVEN, BLACKLISTED)
                    VALUES ({msg.author.id}, 0, 0, 0, 0, 0
                    );"""
        c.execute(sql_query)
        conn.commit()
        if debug_mode is True: print("EMPTY SPOT ADDED FOR MSG AUTHOR")

    # update their data, now that it definitely exists
    sql_query = f"""
    UPDATE data_{payload.guild_id}
    SET UPVOTES = UPVOTES - {upvoted},
        DOWNVOTES = DOWNVOTES - {downvoted}
    WHERE USER_ID = {msg.author.id}
    """
    c.execute(sql_query)
    conn.commit()
    if debug_mode is True: print("DATA UPDATED FOR MSG AUTHOR")

    # gets user data for the user who reacted
    sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {payload.user_id}"
    user_data = c.execute(sql_query).fetchone()

    # if there is no user data, add a spot for them in the database
    if user_data is None:
        sql_query = f"""
        INSERT INTO data_{msg.guild.id}
        (USER_ID, UPVOTES, DOWNVOTES, UPVOTES_GIVEN, DOWNVOTES_GIVEN, BLACKLISTED)
        VALUES({payload.user_id}, 0, 0, 0, 0, 0
        );"""
        c.execute(sql_query)
        conn.commit()
        if debug_mode is True: print("EMPTY SPOT ADDED FOR REACTOR")

    sql_query = f"""
    UPDATE data_{msg.guild.id}
    SET UPVOTES_GIVEN = UPVOTES_GIVEN - {upvoted},
        DOWNVOTES_GIVEN = DOWNVOTES_GIVEN - {downvoted}
    WHERE USER_ID = {payload.user_id}
    """
    c.execute(sql_query)
    conn.commit()
    if debug_mode is True: print("DATA UPDATED FOR MSG REACTOR")

    if debug_mode is True:
        sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {msg.author.id}"
        user_data = c.execute(sql_query).fetchone()
        print("AUTHOR DATA:", user_data)

        sql_query = f"SELECT * FROM data_{msg.guild.id} WHERE USER_ID = {payload.user_id}"
        user_data = c.execute(sql_query).fetchone()
        print("REACTOR DATA:", user_data)


bot.run(KEY)
