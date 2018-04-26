import discord
import asyncio
import requests
import client_token
from threading import Lock

lock = Lock()

death_types = ["FALLEN", "SWARMED", "IMPALED", "GORED", "INFESTED", "OPENED", "PURGED",
               "DESECRATED", "SACRIFICED", "EVISCERATED", "ANNIHILATED", "INTOXICATED", "ENVENOMATED",
               "INCARNATED", "DISCARNATED", "BARBED"]


def to_uint_64(i, offset):
    return int.from_bytes(i[offset:offset+8], byteorder='little', signed=False)


def to_int_64(i, offset):
    return int.from_bytes(i[offset:offset+8], byteorder='little', signed=True)


def to_uint_32(i, offset):
    return int.from_bytes(i[offset:offset+4], byteorder='little', signed=False)


def to_int_32(i, offset):
    return int.from_bytes(i[offset:offset+4], byteorder='little', signed=True)


def to_int_16(i, offset):
    return int.from_bytes(i[offset:offset+2], byteorder='little', signed=True)


class Leaderboard:
    leaderboard_data = ""

    deaths_global = 0
    kills_global = 0
    time_global = 0
    gems_global = 0
    shots_hit_global = 0
    shots_fired_global = 0
    players = 0
    entries = []
    top_100 = []
    old_top_100 = []

    def __init__(self):
        self.update('0')

    def update(self, _offset):
        if _offset == '0':
            self.old_top_100 = self.top_100

        post_values = dict(user='0', level='survival', offset=_offset)

        req = requests.post("http://dd.hasmodai.com/backend15/get_scores.php", post_values)
        self.leaderboard_data = req.content

        self.deaths_global      = to_uint_64(self.leaderboard_data, 11)
        self.kills_global       = to_uint_64(self.leaderboard_data, 19)
        self.time_global        = to_uint_64(self.leaderboard_data, 35) / 10000
        self.gems_global        = to_uint_64(self.leaderboard_data, 43)
        self.shots_hit_global   = to_uint_64(self.leaderboard_data, 51)
        self.shots_fired_global = to_uint_64(self.leaderboard_data, 27)
        self.players            = to_int_32(self.leaderboard_data, 75)

        entry_count = to_int_16(self.leaderboard_data, 59)
        rank_iterator = 0
        byte_pos = 83
        if _offset == '0':
            self.top_100 = []
        self.entries = []
        while(rank_iterator < entry_count):
            entry = Entry()
            username_length = to_int_16(self.leaderboard_data, byte_pos)
            username_bytes = bytearray(username_length)
            byte_pos += 2
            for i in range(byte_pos, byte_pos + username_length):
                username_bytes[i-byte_pos] = self.leaderboard_data[i]

            byte_pos += username_length

            entry.username = username_bytes.decode("utf-8")
            entry.rank = to_int_32(self.leaderboard_data, byte_pos)
            entry.userid = to_int_32(self.leaderboard_data, byte_pos + 4)
            entry.time = to_int_32(self.leaderboard_data, byte_pos + 8) / 10000
            entry.kills = to_int_32(self.leaderboard_data, byte_pos + 12)
            entry.gems = to_int_32(self.leaderboard_data, byte_pos + 24)
            entry.shots_hit = to_int_32(self.leaderboard_data, byte_pos + 20)
            entry.shots_fired = to_int_32(self.leaderboard_data, byte_pos + 16)
            if entry.shots_fired == 0:
                entry.shots_fired = 1
            entry.death_type = death_types[to_int_16(self.leaderboard_data, byte_pos + 28)]
            entry.time_total = to_uint_64(self.leaderboard_data, byte_pos + 56) / 10000
            entry.kills_total = to_uint_64(self.leaderboard_data, byte_pos + 40)
            entry.gems_total = to_uint_64(self.leaderboard_data, byte_pos + 64)
            entry.deaths_total = to_uint_64(self.leaderboard_data, byte_pos + 32)
            entry.shots_hit_total = to_uint_64(self.leaderboard_data, byte_pos + 72)
            entry.shots_fired_total = to_uint_64(self.leaderboard_data, byte_pos + 48)
            if entry.shots_fired_total == 0:
                entry.shots_fired_total = 1

            byte_pos += 84

            if _offset == '0':
                self.top_100.append(entry)
            self.entries.append(entry)

            rank_iterator += 1

    def print_range(self, start, end):
        self.update()
        out = ""
        for i in range(start-1, end):
            out += str(self.entries[i]) + "\n\n"
        return out

    def print_range_compact(self, start, end):
        self.update()
        out = "```"
        for i in range(start-1, end):
            out += "#{} {} ({})".format(self.entries[i].rank, self.entries[i].username,
                    self.entries[i].time)
            out += "\n"
        return out + "```"

    def __str__(self):
        return "{} {} {:,.4f}s {} {}".format(self.deaths_global, self.kills_global, self.time_global, self.gems_global, self.players)

class UserSearch:
    user_search_data = ""
    entries = []

    def search(self, user):

        post_values = dict(search=user)

        req = requests.post("http://dd.hasmodai.com/backend16/get_user_search_public.php", post_values)
        self.user_search_data = req.content

        entry_count = to_int_16(self.user_search_data, 11)
        rank_iterator = 0
        byte_pos = 19
        self.entries = []
        while(rank_iterator < entry_count):
            entry = Entry()
            username_length = to_int_16(self.user_search_data, byte_pos)
            username_bytes = bytearray(username_length)
            byte_pos += 2
            for i in range(byte_pos, byte_pos + username_length):
                username_bytes[i-byte_pos] = self.user_search_data[i]

            byte_pos += username_length

            entry.username = username_bytes.decode("utf-8")
            entry.rank = to_int_32(self.user_search_data, byte_pos)
            entry.userid = to_int_32(self.user_search_data, byte_pos + 4)
            entry.time = to_int_32(self.user_search_data, byte_pos + 12) / 10000
            entry.kills = to_int_32(self.user_search_data, byte_pos + 16)
            entry.gems = to_int_32(self.user_search_data, byte_pos + 28)
            entry.shots_hit = to_int_32(self.user_search_data, byte_pos + 24)
            entry.shots_fired = to_int_32(self.user_search_data, byte_pos + 20)
            if entry.shots_fired == 0:
                entry.shots_fired = 1
            entry.death_type = death_types[to_int_16(self.user_search_data, byte_pos + 32)]
            entry.time_total = to_uint_64(self.user_search_data, byte_pos + 60) / 10000
            entry.kills_total = to_uint_64(self.user_search_data, byte_pos + 48)
            entry.gems_total = to_uint_64(self.user_search_data, byte_pos + 68)
            entry.deaths_total = to_uint_64(self.user_search_data, byte_pos + 36)
            entry.shots_hit_total = to_uint_64(self.user_search_data, byte_pos + 76)
            entry.shots_fired_total = to_uint_64(self.user_search_data, byte_pos + 52)
            if entry.shots_fired_total == 0:
                entry.shots_fired_total = 1

            byte_pos += 88

            self.entries.append(entry)

            rank_iterator += 1


class Entry:
    username = ""
    userid = 0
    rank = 0
    time = 0
    kills = 0
    gems = 0
    shots_hit = 0
    shots_fired = 0
    death_type = ""
    time_total = 0
    kills_total = 0
    gems_total = 0
    deaths_total = 0
    shots_hit_total = 0
    shots_fired_total = 0

    def __str__(self):
        out = "username: {}\n".format(self.username) +\
        "rank: {:,}\n".format(self.rank) +\
        "time: {:.4f}\n".format(self.time) +\
        "kills: {:,}\n".format(self.kills) +\
        "gems: {:,}\n".format(self.gems) +\
        "death_type: {}\n".format(self.death_type) +\
        "time_total: {:,.4f} ".format(self.time_total) +\
        "({:,.2f} days)\n".format(self.time_total / 86400) +\
        "kills_total: {:,}\n".format(self.kills_total) +\
        "gems_total: {:,}\n".format(self.gems_total) +\
        "deaths_total: {:,}".format(self.deaths_total)
        return out

    def __eq__(self, other):
        try:
            return (self.rank, self.time, self.kills) == (other.rank, other.time,
                    other.kills)
        except AttributeError:
            return NotImplemented


def server_stats(message):
    deaths_global = leaderboard.deaths_global
    kills_global = leaderboard.kills_global
    time_global = leaderboard.time_global
    gems_global = leaderboard.gems_global
    accuracy_global = leaderboard.shots_hit_global / leaderboard.shots_fired_global
    players = leaderboard.players
    msg = '```css\n' + \
            '[Global Time]     {:,}s\n'.format(time_global) +\
            '[Global Kills]    {:,}\n'.format(kills_global) +\
            '[Global Gems]     {:,}\n'.format(gems_global) +\
            '[Global Deaths]   {:,}\n'.format(deaths_global) +\
            '[Global Accuracy] {:,}\n'.format(accuracy_global) +\
            '[Total Players]   {:,}\n'.format(players) +\
            '```'
    return msg


def global_stats():
    leaderboard.update('0')
    embed = discord.Embed(title="Server Stats", color=0x660000)
    embed.add_field(name="Global Time", value="{:,}s".format(leaderboard.time_global), inline=False)
    embed.add_field(name="Global Kills", value="{:,}".format(leaderboard.kills_global), inline=False)
    embed.add_field(name="Global Gems", value="{:,}".format(leaderboard.gems_global), inline=False)
    embed.add_field(name="Global Deaths", value="{:,}".format(leaderboard.deaths_global), inline=False)
    # embed.add_field(name="Global Accuracy",
                    # value="{:,}".format(leaderboard.shots_fired_global/leaderboard.shots_hit_global), inline=False)
    embed.add_field(name="Total Players", value="{:,}".format(leaderboard.players), inline=False)
    return embed


def stats(message):
    split_command = message.content.split()
    if len(split_command) != 2:
        return None
    if split_command[1] == "global":
        return global_stats()
    if not split_command[1].isdigit():
        return None
    rank_choice = int(split_command[1])
    if (rank_choice > leaderboard.players) or (rank_choice < 1):
        return None
    leaderboard.update(rank_choice-1)
    entry = leaderboard.entries[0]
    embed = discord.Embed(title="{} ({})".format(entry.username, entry.userid),
                          description="Rank {:,}".format(entry.rank),
                          color=0x660000)
    embed.add_field(name="Time", value="{:.4f}s".format(entry.time), inline=True)
    embed.add_field(name="Kills", value="{:,}".format(entry.kills), inline=True)
    embed.add_field(name="Gems", value="{:,}".format(entry.gems), inline=True)
    embed.add_field(name="Accuracy", value="{:.2f}".format((entry.shots_hit/entry.shots_fired)*100), inline=True)
    embed.add_field(name="Death Type", value=entry.death_type, inline=True)
    embed.add_field(name="Total Time", value="{:,.4f}s".format(entry.time_total), inline=True)
    embed.add_field(name="Total Time (in days)", value="{:,.2f}".format(entry.time_total / 84600), inline=True)
    embed.add_field(name="Kills Total", value="{:,}".format(entry.kills_total), inline=True)
    embed.add_field(name="Gems Total", value="{:,}".format(entry.gems_total), inline=True)
    embed.add_field(name="Accuracy Total",
                    value="{:.2f}".format((entry.shots_hit_total/entry.shots_fired_total)*100),
                    inline=True)
    embed.add_field(name="Deaths Total", value="{:,}".format(entry.deaths_total), inline=True)
    return embed


def top10():
    leaderboard.update('0')
    embed = discord.Embed(title="Top 10", color=0x660000)
    for i in range(0, 10):
        entry = leaderboard.entries[i]
        embed.add_field(name="{}. {}".format(entry.rank, entry.username),
                        value="{:.4f}s".format(entry.time), inline=False)
    return embed


def user_search(message):
    user = " ".join(message.content.strip().split()[1:])
    usersearch.search(user)
    number_users_found = len(usersearch.entries)
    if number_users_found == 1:
        entry = usersearch.entries[0]
        embed = discord.Embed(title=entry.username, description="Rank {:,}".format(entry.rank),
                              color=0x660000)
        embed.add_field(name="Time", value="{:.4f}s".format(entry.time), inline=True)
        embed.add_field(name="Kills", value="{:,}".format(entry.kills), inline=True)
        embed.add_field(name="Gems", value="{:,}".format(entry.gems), inline=True)
        embed.add_field(name="Accuracy", value="{:.2f}".format((entry.shots_hit/entry.shots_fired)*100), inline=True)
        embed.add_field(name="Death Type", value=entry.death_type, inline=True)
        embed.add_field(name="Total Time", value="{:,.4f}s".format(entry.time_total), inline=True)
        embed.add_field(name="Total Time (in days)", value="{:,.2f}".format(entry.time_total / 84600), inline=True)
        embed.add_field(name="Kills Total", value="{:,}".format(entry.kills_total), inline=True)
        embed.add_field(name="Gems Total", value="{:,}".format(entry.gems_total), inline=True)
        embed.add_field(name="Accuracy Total",
                        value="{:.2f}".format((entry.shots_hit_total/entry.shots_fired_total)*100),
                        inline=True)
        embed.add_field(name="Deaths Total", value="{:,}".format(entry.deaths_total), inline=True)
        return embed

    sorted_users = sorted(usersearch.entries, key=lambda user: user.rank)[:10]
    embed = discord.Embed(title="Search: \"{}\"".format(user),
                          color=0x660000)
    users = "```\n"
    for entry in sorted_users:
        users += "{:,}:\n{}\n\n".format(entry.rank, entry.username)
    users = users[:-1]
    over100 = ""
    showing = ""
    if number_users_found > 10:
        showing = " (showing 10)"
    if number_users_found == 100:
        over100 = "+"
    users += "```"
    embed.add_field(name="Found {}{} Users{}:".format(str(number_users_found), over100, showing),
                    value=users, inline=False)
    return embed


def new_top_100(entry):
    embed = discord.Embed(title="New Score in Top 100!",
                          description="Congratulations {}!".format(entry.username),
                          color=0x660000)
    embed.add_field(name="Rank", value="{}".format(entry.rank), inline=False)
    embed.add_field(name="Time", value="{}".format(entry.time), inline=False)
    return embed


class LeaderBot(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.loop.create_task(self.check_top_100())

    async def on_ready(self):
        print("Logged in as")
        print(self.user.name)
        print(self.user.id)
        print("---------")

    async def check_top_100(self):
        await self.wait_until_ready()
        channel = discord.Object(id=client_token.dd_channel)
        while not self.is_closed:
            leaderboard.update('0')
            updates = [x for x in leaderboard.top_100 if x not in leaderboard.old_top_100]
            if len(updates) > 0 and len(updates) < 2:
                for entry in updates:
                    await self.send_message(channel, embed=new_top_100(entry))
            await asyncio.sleep(30)

    async def on_message(self, message):
        # per the discord.py docs, this is so to not have the bot respond to itself
        if message.author == self.user:
            return
        # if the bot sees the command !hello we will respond with our msg string
        if message.content.startswith('.stats'):
            embed = stats(message)
            if embed is not None:
                await self.send_message(message.channel, embed=embed)
        if message.content.startswith('.top10'):
            embed = top10()
            await self.send_message(message.channel, embed=embed)
        if message.content.startswith('.search'):
            embed = user_search(message)
            if embed is not None:
                await self.send_message(message.channel, embed=embed)


leaderboard = Leaderboard()
usersearch = UserSearch()
client = LeaderBot()
client.run(client_token.token)
