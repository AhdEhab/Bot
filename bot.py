import discord
from discord.ext import commands
import sqlite3
import os

# --- Bot Setup ---

intents = discord.Intents.default()
intents.message_content = True  # ✅ Enable this!

bot = commands.Bot(command_prefix='/', intents=intents)

# --- Database Setup ---
conn = sqlite3.connect('study_groups.db')
c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS groups (group_name TEXT, user_id INTEGER, user_name TEXT, points INTEGER)''')
conn.commit()

# --- Commands ---

@bot.command()
async def create_group(ctx, group_name):
    await ctx.send(f"📁 Group `{group_name}` created! Others can now join using `/join_group {group_name} YourName`.")

@bot.command()
async def join_group(ctx, group_name, user_name):
    c.execute("SELECT * FROM groups WHERE group_name=? AND user_id=?", (group_name, ctx.author.id))
    if c.fetchone():
        await ctx.send("⚠️ You’re already in this group.")
    else:
        c.execute("INSERT INTO groups VALUES (?, ?, ?, ?)", (group_name, ctx.author.id, user_name, 0))
        conn.commit()
        await ctx.send(f"✅ `{user_name}` joined `{group_name}`!")

@bot.command()
async def done(ctx, group_name):
    c.execute("SELECT * FROM groups WHERE group_name=? AND user_id=?", (group_name, ctx.author.id))
    if c.fetchone():
        c.execute("UPDATE groups SET points = points + 10 WHERE group_name=? AND user_id=?", (group_name, ctx.author.id))
        conn.commit()
        await ctx.send("✅ Nice job! You earned 10 points!")
    else:
        await ctx.send("❌ You’re not in this group.")

@bot.command()
async def leaderboard(ctx, group_name):
    c.execute("SELECT user_name, points FROM groups WHERE group_name=? ORDER BY points DESC", (group_name,))
    rows = c.fetchall()
    if rows:
        leaderboard_text = "\n".join([f"**{i+1}. {name}** – {points} pts" for i, (name, points) in enumerate(rows)])
        await ctx.send(f"🏆 **Leaderboard for {group_name}**:\n{leaderboard_text}")
    else:
        await ctx.send("❌ No members found in this group.")

@bot.command()
async def my_score(ctx, group_name):
    c.execute("SELECT user_name, points FROM groups WHERE group_name=? AND user_id=?", (group_name, ctx.author.id))
    row = c.fetchone()
    if row:
        await ctx.send(f"📊 `{row[0]}` has **{row[1]}** points in `{group_name}`.")
    else:
        await ctx.send("❌ You’re not in this group.")

@bot.command()
async def list_members(ctx, group_name):
    c.execute("SELECT user_name FROM groups WHERE group_name=?", (group_name,))
    rows = c.fetchall()
    if rows:
        names = ", ".join([name[0] for name in rows])
        await ctx.send(f"👥 Members of `{group_name}`: {names}")
    else:
        await ctx.send("❌ Group not found or has no members.")

@bot.command()
async def reset_scores(ctx, group_name):
    if ctx.author.guild_permissions.administrator:
        c.execute("UPDATE groups SET points = 0 WHERE group_name=?", (group_name,))
        conn.commit()
        await ctx.send(f"🔄 Scores in `{group_name}` have been reset.")
    else:
        await ctx.send("⛔ You need to be an admin to reset scores.")

@bot.command()
async def set_points(ctx, group_name, member: discord.Member, points: int):
    if ctx.author.guild_permissions.administrator:
        c.execute("UPDATE groups SET points = ? WHERE group_name = ? AND user_id = ?", (points, group_name, member.id))
        conn.commit()
        await ctx.send(f"🛠️ Set `{member.display_name}`'s points to {points} in `{group_name}`.")
    else:
        await ctx.send("⛔ Only admins can set points manually.")

@bot.command()
async def medhat(ctx):
    help_text = (
        "**🤖 Study Bot Commands Overview**\n"
        "Here’s what I can do:\n\n"
        "📁 `/create_group [GroupName]` – Start a new study group.\n"
        "👥 `/join_group [GroupName] [YourName]` – Join an existing group.\n"
        "✅ `/done [GroupName]` – Report that you've completed a task (earns you 10 points).\n"
        "🏆 `/leaderboard [GroupName]` – See who’s leading the group in points.\n"
        "📊 `/my_score [GroupName]` – Check your own score.\n"
        "🧑‍🤝‍🧑 `/list_members [GroupName]` – List group members.\n"
        "🔄 `/reset_scores [GroupName]` – (Admin) Reset everyone’s points.\n"
        "🛠️ `/set_points [GroupName] @user [Points]` – (Admin) Manually adjust someone’s score.\n"
    )
    await ctx.send(help_text)

# --- Run the Bot ---
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
 
