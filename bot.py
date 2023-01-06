#---------------------------------
# Barl the Beantroller
#---------------------------------
#
# Creator: Ryan Dinubilo
# Creation Date: 3/11/2021
# Current Version: 1.15
#
#
# Changelog ---------------------
# Revision Dates:
# Version 1.12 - 3/12/2021
# See changelog doc
#
#
# Version 1.13 - 3/13/2021
# See changelog doc
#
# Version 1.14 - 3/16/202                                
#
# - See changelog
#
# - Added comments
#
# Version 1.15 - 6/30/2021
#
# - Updated ffmpeg buildpack with heroku buildpacks:add --index 1 https://github.com/jonathanong/heroku-buildpack-ffmpeg-latest.git
# - Removed kitcast ffmpeg buildpack on Heroku

# Import Libraries 
import discord
import os
from dotenv import load_dotenv
from discord.ext import commands
import pandas as pd
from googleapiclient.discovery import build
import pprint
import itertools
import re
import requests
import datetime
from airtable import Airtable
import pprint
import random
from random import randint
from discord.utils import get
from discord import FFmpegPCMAudio
import youtube_dl
from youtube_dl import YoutubeDL
import asyncio
from async_timeout import timeout
from functools import partial
import sys

#Set the bot command prefix to be "!". All commands are in the form !cmdname
bot = commands.Bot(command_prefix="!")

## -- Simple Poll functionality
class QuickPoll:
    """"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(pass_context=True)
    async def quickpoll(self, ctx, question, *options: str):
        if len(options) <= 1:
            await self.bot.say('You need more than one option to make a poll!')
            return
        if len(options) > 10:
            await self.bot.say('You cannot make a poll for more than 10 things!')
            return

        if len(options) == 2 and options[0] == 'yes' and options[1] == 'no':
            reactions = ['✅', '❌']
        else:
            reactions = ['1⃣', '2⃣', '3⃣', '4⃣', '5⃣', '6⃣', '7⃣', '8⃣', '9⃣', '🔟']

        description = []
        for x, option in enumerate(options):
            description += '\n {} {}'.format(reactions[x], option)
        embed = discord.Embed(title=question, description=''.join(description))
        react_message = await self.bot.say(embed=embed)
        for reaction in reactions[:len(options)]:
            await self.bot.add_reaction(react_message, reaction)
        embed.set_footer(text='Poll ID: {}'.format(react_message.id))
        await self.bot.edit_message(react_message, embed=embed)

    @commands.command(pass_context=True)
    async def tally(self, ctx, id):
        poll_message = await self.bot.get_message(ctx.message.channel, id)
        if not poll_message.embeds:
            return
        embed = poll_message.embeds[0]
        if poll_message.author != ctx.message.server.me:
            return
        if not embed['footer']['text'].startswith('Poll ID:'):
            return
        unformatted_options = [x.strip() for x in embed['description'].split('\n')]
        opt_dict = {x[:2]: x[3:] for x in unformatted_options} if unformatted_options[0][0] == '1' \
            else {x[:1]: x[2:] for x in unformatted_options}
        # check if we're using numbers for the poll, or x/checkmark, parse accordingly
        voters = [ctx.message.server.me.id]  # add the bot's ID to the list of voters to exclude it's votes

        tally = {x: 0 for x in opt_dict.keys()}
        for reaction in poll_message.reactions:
            if reaction.emoji in opt_dict.keys():
                reactors = await self.bot.get_reaction_users(reaction)
                for reactor in reactors:
                    if reactor.id not in voters:
                        tally[reaction.emoji] += 1
                        voters.append(reactor.id)

        output = 'Results of the poll for "{}":\n'.format(embed['title']) + \
                 '\n'.join(['{}: {}'.format(opt_dict[key], tally[key]) for key in tally.keys()])
        await self.bot.say(output)

def setup(bot):
    bot.add_cog(QuickPoll(bot))

setup(bot)

## Rock Paper Scissors 
#

@bot.command(help="Play with .rps [your choice]")
async def rps(ctx):
    rpsGame = ['rock', 'paper', 'scissors']
    await ctx.send(f"Rock, paper, or scissors? Choose wisely...")

    def check(msg):
        return msg.author == ctx.author and msg.channel == ctx.channel and msg.content.lower() in rpsGame

    user_choice = (await bot.wait_for('message', check=check)).content

    comp_choice = random.choice(rpsGame)
    if user_choice == 'rock':
        if comp_choice == 'rock':
            await ctx.send(f'Well, that was weird. We tied.\nYour choice: 🗿\nMy choice: 🗿')
        elif comp_choice == 'paper':
            await ctx.send(f'Nice try, but I won that time!\nYour choice: 🗿\nMy choice: {comp_choice}')
        elif comp_choice == 'scissors':
            await ctx.send(f"Aw, you beat me. It won't happen again!\nYour choice: 🗿\nMy choice: {comp_choice}")

    elif user_choice == 'paper':
        if comp_choice == 'rock':
            await ctx.send(f'The pen beats the sword? More like the paper beats the rock!\nYour choice: {user_choice}\nMy choice: {comp_choice}')
        elif comp_choice == 'paper':
            await ctx.send(f'Oh, wacky. We just tied. I call a rematch!\nYour choice: {user_choice}\nMy choice: {comp_choice}')
        elif comp_choice == 'scissors':
            await ctx.send(f"Aw man, you actually managed to beat me.\nYour choice: {user_choice}\nMy choice: {comp_choice}")

    elif user_choice == 'scissors':
        if comp_choice == 'rock':
            await ctx.send(f'HAHA! I JUST CRUSHED YOU! I rock!\nYour choice: {user_choice}\nMy choice: {comp_choice}')
        elif comp_choice == 'paper':
            await ctx.send(f'Bruh. >: |\nYour choice: {user_choice}\nMy choice: {comp_choice}')
        elif comp_choice == 'scissors':
            await ctx.send(f"Oh well, we tied.\nYour choice: {user_choice}\nMy choice: {comp_choice}")


# End Rock Paper Scissors



##-----------------------------------------------------------------------------## Youtube Stuff
#
# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ''

ytdlopts = {
    'format': 'bestaudio/best',
    'outtmpl': 'downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = YoutubeDL(ytdlopts)


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get('title')
        self.web_url = data.get('webpage_url')
        self.duration = data.get('duration')

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        embed = discord.Embed(title="", description=f"Queued [{data['title']}]({data['webpage_url']}) [{ctx.author.mention}]", color=discord.Color.green())
        await ctx.send(embed=embed)

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {'webpage_url': data['webpage_url'], 'requester': ctx.author, 'title': data['title']}

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data['requester']

        to_run = partial(ytdl.extract_info, url=data['webpage_url'], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data['url']), data=data, requester=requester)


    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]
        filename = data['title'] if stream else ytdl.prepare_filename(data)
        return filename

class MusicPlayer:
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = ('bot', '_guild', '_channel', '_cog', 'queue', 'next', 'current', 'np', 'volume')

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = .5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(source, loop=self.bot.loop)
                except Exception as e:
                    await self._channel.send(f'There was an error processing your song.\n'
                                             f'```css\n[{e}]\n```')
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(source, after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set))
            embed = discord.Embed(title="Now playing", description=f"[{source.title}]({source.web_url}) [{source.requester.mention}]", color=discord.Color.green())
            self.np = await self._channel.send(embed=embed)
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Music(commands.Cog):
    """Music related commands."""

    __slots__ = ('bot', 'players')

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.send('This command can not be used in Private Messages.')
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.send('Error connecting to Voice Channel. '
                           'Please make sure you are in a valid channel or provide me with one')

        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name='join', aliases=['connect', 'j'], description="connects to voice")
    async def connect_(self, ctx, *, channel: discord.VoiceChannel=None):
        """Connect to voice.
        Parameters
        ------------
        channel: discord.VoiceChannel [Optional]
            The channel to connect to. If a channel is not specified, an attempt to join the voice channel you are in
            will be made.
        This command also handles moving the bot to different channels.
        """
        if not channel:
            try:
                channel = ctx.author.voice.channel
            except AttributeError:
                embed = discord.Embed(title="", description="No channel to join. Please call `!join` from a voice channel.", color=discord.Color.green()) #!
                await ctx.send(embed=embed)
                raise InvalidVoiceChannel('No channel to join. Please either specify a valid channel or join one.')

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Moving to channel: <{channel}> timed out.')
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f'Connecting to channel: <{channel}> timed out.')
        if (random.randint(0, 1) == 0):
            await ctx.message.add_reaction('👍')
        await ctx.send(f'**Joined `{channel}`**')

    @commands.command(name="testplay")
    async def testplay_(self,ctx, *, search: str):
        await ctx.trigger_typing()

        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)

        player.queue._queue.clear()

        vc.stop()

        await player.queue.put(source)


    @commands.command(name='play', aliases=['sing','p', 'yt'], description="streams music")
    async def play_(self, ctx, *, search: str):
        """Request a song and add it to the queue.
        This command attempts to join a valid voice channel if the bot is not already in one.
        Uses YTDL to automatically search and retrieve a song.
        Parameters
        ------------
        search: str [Required]
            The song to search and retrieve using YTDL. This could be a simple search, an ID or URL.
        """
        await ctx.trigger_typing()

        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        # If download is False, source will be a dict which will be used later to regather the stream.
        # If download is True, source will be a discord.FFmpegPCMAudio with a VolumeTransformer.
        source = await YTDLSource.create_source(ctx, search, loop=self.bot.loop, download=False)

        await player.queue.put(source)

        #Grab the record associated with the user you are praising
        record = playcount_airtable.match('Name', 'Barl')
        play_value = record['fields']['playcount'] #Get the value of the playcount field
        number_play = int(play_value) #Convert it to an integer just in case

        total = number_play + 1 #If "botscore" is not provided, incremement by 1
        total_str = str(total) #The new botscore total
        strings = f'I have been playing Youtube music since 6/27/2021. I have streamed {total_str} videos for Bean Life.' #The message to be sent with the updated praise
        fields = {'playcount': total_str} #The fields to be updated in Airtable with the new values
        airtable.update(record['id'], fields) #Updating the airtable record with new praises

    @commands.command(name='pause', description="pauses music")
    async def pause_(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            embed = discord.Embed(title="", description="I am currently not playing anything", color=discord.Color.green())
            return await ctx.send(embed=embed)
        elif vc.is_paused():
            return

        vc.pause()
        await ctx.send("Paused ⏸️")

    @commands.command(name='resume', description="resumes music")
    async def resume_(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)
        elif not vc.is_paused():
            return

        vc.resume()
        await ctx.send("Resuming ⏯️")

    @commands.command(name='skip', description="skips to next song in queue")
    async def skip_(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
    
    @commands.command(name='remove', aliases=['rm', 'rem'], description="removes specified song from queue")
    async def remove_(self, ctx, pos : int=None):
        """Removes specified song from queue"""

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if pos == None:
            player.queue._queue.pop()
        else:
            try:
                s = player.queue._queue[pos-1]
                del player.queue._queue[pos-1]
                embed = discord.Embed(title="", description=f"Removed [{s['title']}]({s['webpage_url']}) [{s['requester'].mention}]", color=discord.Color.green())
                await ctx.send(embed=embed)
            except:
                embed = discord.Embed(title="", description=f'Could not find a track for "{pos}"', color=discord.Color.green())
                await ctx.send(embed=embed)
    
    @commands.command(name='clear', aliases=['clr', 'cl', 'cr'], description="clears entire queue")
    async def clear_(self, ctx):
        """Deletes entire queue of upcoming songs."""

        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        player.queue._queue.clear()
        await ctx.send('**Cleared**')

    @commands.command(name='queue', aliases=['q', 'playlist', 'que'], description="shows the queue")
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if player.queue.empty():
            embed = discord.Embed(title="", description="queue is empty", color=discord.Color.green())
            return await ctx.send(embed=embed)

        seconds = vc.source.duration % (24 * 3600) 
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
        else:
            duration = "%02dm %02ds" % (minutes, seconds)

        # Grabs the songs in the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, int(len(player.queue._queue))))
        fmt = '\n'.join(f"`{(upcoming.index(_)) + 1}.` [{_['title']}]({_['webpage_url']}) | ` {duration} Requested by: {_['requester']}`\n" for _ in upcoming)
        fmt = f"\n__Now Playing__:\n[{vc.source.title}]({vc.source.web_url}) | ` {duration} Requested by: {vc.source.requester}`\n\n__Up Next:__\n" + fmt + f"\n**{len(upcoming)} songs in queue**"
        embed = discord.Embed(title=f'Queue for {ctx.guild.name}', description=fmt, color=discord.Color.green())
        embed.set_footer(text=f"{ctx.author.display_name}", icon_url=ctx.author.avatar_url)

        await ctx.send(embed=embed)

    @commands.command(name='np', aliases=['song', 'current', 'currentsong', 'playing'], description="shows the current playing song")
    async def now_playing_(self, ctx):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(title="", description="I am currently not playing anything", color=discord.Color.green())
            return await ctx.send(embed=embed)
        
        seconds = vc.source.duration % (24 * 3600) 
        hour = seconds // 3600
        seconds %= 3600
        minutes = seconds // 60
        seconds %= 60
        if hour > 0:
            duration = "%dh %02dm %02ds" % (hour, minutes, seconds)
        else:
            duration = "%02dm %02ds" % (minutes, seconds)

        embed = discord.Embed(title="", description=f"[{vc.source.title}]({vc.source.web_url}) [{vc.source.requester.mention}] | `{duration}`", color=discord.Color.green())
        embed.set_author(icon_url=self.bot.user.avatar_url, name=f"Now Playing 🎶")
        await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=['vol', 'v'], description="changes Kermit's volume")
    async def change_volume(self, ctx, *, vol: float=None):
        """Change the player volume.
        Parameters
        ------------
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I am not currently connected to voice", color=discord.Color.green())
            return await ctx.send(embed=embed)
        
        if not vol:
            embed = discord.Embed(title="", description=f"🔊 **{(vc.source.volume)*100}%**", color=discord.Color.green())
            return await ctx.send(embed=embed)

        if not 0 < vol < 101:
            embed = discord.Embed(title="", description="Please enter a value between 1 and 100", color=discord.Color.green())
            return await ctx.send(embed=embed)

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        embed = discord.Embed(title="", description=f'**`{ctx.author}`** set the volume to **{vol}%**', color=discord.Color.green())
        await ctx.send(embed=embed)

    @commands.command(name='fuckouttahere', aliases=["stop", "dc", "disconnect", "bye"], description="stops music and disconnects from voice.")
    async def leave_(self, ctx):
        """Stop the currently playing song and destroy the player.
        !Warning!
            This will destroy the player assigned to your guild, also deleting any queued songs and settings.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = discord.Embed(title="", description="I'm not connected to a voice channel", color=discord.Color.green())
            return await ctx.send(embed=embed)

        if (random.randint(0, 1) == 0):
            await ctx.message.add_reaction('👋')
        await ctx.send('**Successfully disconnected**')

        await self.cleanup(ctx.guild)


bot.add_cog(Music(bot))

## Lofi Command
@bot.command(help = "Automatically queues up a lofi video on youtube")
async def lofi(ctx):
    await ctx.send('!yt lofi')


#### ---------------------------------------------------------------- Things

@bot.event
async def on_ready():
    print('Running!')
    for guild in bot.guilds:
        for channel in guild.text_channels :
            if str(channel) == "general" :
                await channel.send('Bot Activated..')
                await channel.send(file=discord.File('giphy.png'))
        print('Active in {}\n Member Count : {}'.format(guild.name,guild.member_count))

@bot.command(help = "Prints details of Author")
async def whats_my_name(ctx) :
    await ctx.send('Hello {}'.format(ctx.author.name))

@bot.command(help = "Prints details of Server")
async def where_am_i(ctx):
    owner=str(ctx.guild.owner)
    region = str(ctx.guild.region)
    guild_id = str(ctx.guild.id)
    memberCount = str(ctx.guild.member_count)
    icon = str(ctx.guild.icon_url)
    desc=ctx.guild.description
    
    embed = discord.Embed(
        title=ctx.guild.name + " Server Information",
        description=desc,
        color=discord.Color.blue()
    )
    embed.set_thumbnail(url=icon)
    embed.add_field(name="Owner", value=owner, inline=True)
    embed.add_field(name="Server ID", value=guild_id, inline=True)
    embed.add_field(name="Region", value=region, inline=True)
    embed.add_field(name="Member Count", value=memberCount, inline=True)

    await ctx.send(embed=embed)

    members=[]
    async for member in ctx.guild.fetch_members(limit=150) :
        await ctx.send('Name : {}\t Status : {}\n Joined at {}'.format(member.display_name,str(member.status),str(member.joined_at)))
     
        
# TODO : Filter out swear words from messages

@bot.command()
async def tell_me_about_yourself(ctx):
    text = "My name is Barl the Beantroller!\n I was built by Bird Person."
    await ctx.send(text)

################################################################################## - End Youtube Stuff

### Doto check
        # Do stuff here
 
##

#Initialize the Airtable Python wrapper
#
#STOP STORING PASSWORDS IN PLAINTEXT YOU IDIOT
#  
airtable = Airtable('appILX4NST2XuPcJS', 'FuckList', 'keyxGI7Z1HjtiqJWa')   
feelings_airtable = Airtable('appILX4NST2XuPcJS', 'Feelings', 'keyxGI7Z1HjtiqJWa')
goodbot_airtable = Airtable('appILX4NST2XuPcJS', 'GoodBot', 'keyxGI7Z1HjtiqJWa')
playcount_airtable = Airtable('appILX4NST2XuPcJS', 'Music', 'keyxGI7Z1HjtiqJWa')

#Load envrionment variables
#
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')

client = discord.Client()

### ------------------------ Good Bot ------------------------------###

@bot.command()
async def goodbot(ctx):
    #Grab the record associated with the user you are praising
    record = goodbot_airtable.match('Name', 'Barl')
    good_value = record['fields']['botscore'] #Get the value of the botscore field
    number_good = int(good_value) #Convert it to an integer just in case

    total = number_good + 1 #If "botscore" is not provided, incremement by 1
    total_str = str(total) #The new botscore total
    strings = f'Thank you. You have praised me {total_str} times.' #The message to be sent with the updated praise
    fields = {'botscore': total_str} #The fields to be updated in Airtable with the new values
    airtable.update(record['id'], fields) #Updating the airtable record with new praises

    await ctx.channel.send(strings) #Send a message to the channel confirming completion
    await ctx.message.add_reaction('🤖')
    
    return number_good

## ------------------------- End Good Bot --------------------------###

# Logs

@bot.command()
async def playcount(ctx):
    #Grab the record associated with the user you are praising
    record = playcount_airtable.match('Name', 'Barl')
    play_value = record['fields']['playcount'] #Get the value of the playcount field
    number_play = int(play_value) #Convert it to an integer just in case

    strings = f'I have been playing Youtube music since 6/27/2021. I have streamed {number_play} videos for Bean Life.' #The message to be sent with the updated praise

    await ctx.channel.send(strings)

# Send message for Divinity on Saturday
#
@bot.command()
async def divinityReminder(ctx):
    await ctx.channel.send('')
    

# !E command, no explanantion needed
@bot.command()
async def E(ctx):
    await ctx.channel.send('https://i.kym-cdn.com/entries/icons/original/000/026/008/Screen_Shot_2018-04-25_at_12.24.22_PM.png')

@bot.command()
async def e(ctx):
    await ctx.channel.send('https://i.kym-cdn.com/entries/icons/original/000/026/008/Screen_Shot_2018-04-25_at_12.24.22_PM.png')

# !beans command - Summons bean photo
@bot.command()
async def beans(ctx):
    await ctx.channel.send(file=discord.File('C:\\\\Users\\\\radin\\\\Documents\\\\Personal\\\\Beans\\\\beans.jpg'))

# !frijole command - Summons bean photo
@bot.command()
#@commands.is_owner()
async def frijole(ctx):
    await ctx.channel.send(file=discord.File('C:\\\\Users\\\\radin\\\\Documents\\\\Personal\\\\Beans\\\\beans.jpg'))

# !frijole command - Summons bean photo
@bot.command()
#@commands.is_owner()
async def frijoles(ctx):
    await ctx.channel.send(file=discord.File('C:\\\\Users\\\\radin\\\\Documents\\\\Personal\\\\Beans\\\\beans.jpg'))

# !bean command - Summons bean photo
@bot.command()
#@commands.is_owner()
async def bean(ctx):
    await ctx.channel.send(file=discord.File('C:\\\\Users\\\\radin\\\\Documents\\\\Personal\\\\Beans\\\\beans.jpg'))

#
@bot.command()
async def fuckDavebecausehesacapitalistsympathizingbish(ctx):
    await ctx.channel.send(file=discord.File('C:\\\\Users\\\\radin\\\\Documents\\\\Personal\\\\Beans\\\\beandave.png'))

#Fuck/Praise Commands - Adds 1 fuck to the user whose command was invoked
#
# !praiseDave command - Adds any number of praises, default 1, to the Dave record on Airtable

@bot.command()
async def praiseDave(ctx, praises=None):
    #Grab the record associated with the user you are praising
    record = airtable.match('Name', 'Dave')
    praise_value = record['fields']['Praises'] #Get the value of the Praise field
    number_praise = int(praise_value) #Convert it to an integer just in case

    #Conditional for checking if extra praises were added to the command
    if praises:
        try: 
            total = number_praise + int(praises) #Increases the number of praises by "praises" if not empty
        except:
            nonint_error_msg = 'You did not enter a valid number of praises. Try again.' #Error message if "praises" is not a number
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_praise + 1 #If "praises" is not provided, incremement by 1
    total_str = str(total) #The new praises total
    strings = f'Dave has been praised {total_str} times.' #The message to be sent with the updated praise
    fields = {'Praises': total_str} #The fields to be updated in Airtable with the new values
    airtable.update(record['id'], fields) #Updating the airtable record with new praises

    feeling = feelings_airtable.match('Name','Dave')
    feel_value = feeling['fields']['feelingscore']
    number_feel = int(feel_value)
    total_feels = number_feel + 1
    total_feels_str = str(total_feels)
    fields = {'feelingscore': total_feels_str}
    airtable.update(feeling['id'], fields)
    feeling_msg = f'I gained 1 feeling point for you, Dave. My feelings for you are now {total_feels_str}'

    await ctx.channel.send(strings) #Send a message to the channel confirming completion
    await ctx.channel.send(feeling_msg)

    return number_feel
    
async def fuckUser(user, ctx, fucks=None):
    record = airtable.match('Name', user)
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'{user} has been fucked {total_str} times.'
    fields2 = {'Fucks': total_str}
    airtable.update(record['id'], fields2)

    feeling = feelings_airtable.match('Name', {user})
    feel_value = feeling['fields']['feelingscore']
    number_feel = int(feel_value)
    total_feels = number_feel - 1
    total_feels_str = str(total_feels)
    fields = {'feelingscore': total_feels_str}
    airtable.update(feeling['id'], fields)
    feeling_msg = f'I lost 1 feeling point for you, {user}. My feelings for you are now {total_feels_str}'

    await ctx.channel.send(strings)
    await ctx.channel.send(feeling_msg)

    return number_fuck

@bot.event
async def message(message):
    user = 482050383821406208

    user2 = message.author.id

    if user2 == user:

        rand = random.randint(1,5)
        print(rand)

        if rand == 1:
            await message.channel.send('test')

        elif rand == 2:
            return

        elif rand == 3:
            return
        elif rand == 4:
            return
        
@bot.command()
async def testfucks(ctx,  fucks=None):
    await fuckUser(ctx, "Dave", fucks=None)

# !fuckDave command - Adds any number of fucks, default 1, to the fuckDave list  
@bot.command()
async def fuckDave(ctx,  fucks=None):
    record = airtable.match('Name', 'Dave')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'Dave has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)

    return number_fuck

# !fuckAngel command - Adds 1 fuck to the fuckAngel list
@bot.command()
async def fuckAngel(ctx, fucks=None):
    record = airtable.match('Name', 'Angel')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'Angel has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)

    return number_fuck

@bot.command()
async def fuckAsh(ctx, fucks=None):
    record = airtable.match('Name', 'Ash')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'Ash has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)

@bot.command()
async def fuckRyan(ctx, fucks=None):
    record = airtable.match('Name', 'Ryan')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'Ryan has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)

@bot.command()
async def fuckAlex(ctx, fucks=None):
    record = airtable.match('Name', 'Alex')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'Alex has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)

@bot.command()
async def fuckJacob(ctx, fucks=None):
    record = airtable.match('Name', 'Jacob')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'Jacob has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)

@bot.command()
async def fuckCaleb(ctx, fucks=None):
    record = airtable.match('Name', 'Caleb')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'Caleb has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)

@bot.command()
async def fuckJer(ctx, fucks=None):
    record = airtable.match('Name', 'Jer')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'Jer has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)


@bot.command()
async def fuckBarl(ctx, fucks=None):
    record = airtable.match('Name', 'Barl the Beantroller')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'Barl the Beantroller has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)

@bot.command()
async def fuckKobe(ctx, fucks=None):
    record = airtable.match('Name', 'Kobe')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'Kobe has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)

@bot.command()
async def fuckGnin(ctx,  fucks=None):
    record = airtable.match('Name', 'AssMaster69')
    fuck_value = record['fields']['Fucks']
    number_fuck = int(fuck_value)
    if fucks:
        try: 
            total = number_fuck + int(fucks)
        except:
            nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_fuck + 1
    total_str = str(total)
    print(total_str)
    strings = f'AssMaster69 has been fucked {total_str} times.'
    fields = {'Fucks': total_str}
    airtable.update(record['id'], fields)
    await ctx.channel.send(strings)

    return number_fuck

#praise gnin
@bot.command()
async def praiseGnin(ctx, praises=None):
    #Grab the record associated with the user you are praising
    record = airtable.match('Name', 'AssMaster69')
    praise_value = record['fields']['Praises'] #Get the value of the Praise field
    number_praise = int(praise_value) #Convert it to an integer just in case

    #Conditional for checking if extra praises were added to the command
    if praises:
        try: 
            total = number_praise + int(praises) #Increases the number of praises by "praises" if not empty
        except:
            nonint_error_msg = 'You did not enter a valid number of praises. Try again.' #Error message if "praises" is not a number
            await ctx.channel.send(nonint_error_msg)
    else:
        total = number_praise + 1 #If "praises" is not provided, incremement by 1
    total_str = str(total) #The new praises total
    strings = f'AssMaster69 has been praised {total_str} times.' #The message to be sent with the updated praise
    fields = {'Praises': total_str} #The fields to be updated in Airtable with the new values
    airtable.update(record['id'], fields) #Updating the airtable record with new praises

    feeling = feelings_airtable.match('Name','AssMaster69')
    feel_value = feeling['fields']['feelingscore']
    number_feel = int(feel_value)
    total_feels = number_feel + 1
    total_feels_str = str(total_feels)
    fields = {'feelingscore': total_feels_str}
    airtable.update(feeling['id'], fields)
    feeling_msg = f'I gained 1 feeling point for you, AssMaster69. My feelings for you are now {total_feels_str}'

    await ctx.channel.send(strings) #Send a message to the channel confirming completion
    await ctx.channel.send(feeling_msg)

    return number_feel


# Airtable HTTP Requests
#
#Makes a request to Airtable for all records from a single table. Returns data in dictionary format.
def airtableDownload(baseID, tableName):

    #Initialize variables 
    base_id = baseID
    table_name = tableName
    params = ()
    airtable_records = []
    url = f'https://api.airtable.com/v0/{base_id}/{table_name}'
 
    # Define the variable to hold the headers
    api_key = "keyxGI7Z1HjtiqJWa"
    headers = {"Authorization": f"Bearer {api_key}"}

    response = requests.get(url, params=params, headers=headers)
 
    #A while loop that grabs each record in the table and returns it in a dictionary
    run = True
    while run is True:
        response = requests.get(url, params=params, headers=headers)
        airtable_response = response.json()
        airtable_records += (airtable_response['records'])
        if 'offset' in airtable_response:
            run = True
            params = (('offset', airtable_response['offset']),)
        else:
            run = False

    return airtable_records

#Converts the airtable records returned by airtableDownload to a dataframe
def airtableToDataframe(table):
    airtable_rows = []
    for record in table:
        airtable_rows.append(record['fields'])
    df = pd.DataFrame(airtable_rows)
    return df

#The !fuckme command, checks who sent the message and adds that number of fucks. 
# Need to refactor the conditionals (if author == name:) <- seems inefficient
@bot.command()
async def fuckme(ctx, fucks=None):
    ryan = 482050383821406208
    dave = 160597904606756865
    jer = 160589867976228864
    angel = 712495135660965958

    airtable = Airtable('appKjJ6hVmNSd5ewT', 'Table 5', 'key0tCqS8SJPkrhSO')

    author = ctx.author.id

    if author == ryan:
        record = airtable.match('Name', 'Ryan')
        fuck_value = record['fields']['Fucks']
        number_fuck = int(fuck_value)
        if fucks:
            try: 
                total = number_fuck + int(fucks)
            except:
                nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
                await ctx.channel.send(nonint_error_msg)
        else:
            total = number_fuck + 1
        total_str = str(total)
        print(total_str)
        strings = f'You have been fucked {total_str} times.'
        fields = {'Fucks': total_str}
        airtable.update(record['id'], fields)
        await ctx.channel.send(strings)

    elif author == dave:
        record = airtable.match('Name', 'Dave')
        fuck_value = record['fields']['Fucks']
        number_fuck = int(fuck_value)
        if fucks:
            try: 
                total = number_fuck + int(fucks)
            except:
                nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
                await ctx.channel.send(nonint_error_msg)
        else:
            total = number_fuck + 1
        total_str = str(total)
        print(total_str)
        strings = f'You have been fucked {total_str} times.'
        fields = {'Fucks': total_str}
        airtable.update(record['id'], fields)
        await ctx.channel.send(strings)

    elif author == jer:
        record = airtable.match('Name', 'Jer')
        fuck_value = record['fields']['Fucks']
        number_fuck = int(fuck_value)
        if fucks:
            try: 
                total = number_fuck + int(fucks)
            except:
                nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
                await ctx.channel.send(nonint_error_msg)
        else:
            total = number_fuck + 1
        total_str = str(total)
        print(total_str)
        strings = f'You have been fucked {total_str} times.'
        fields = {'Fucks': total_str}
        airtable.update(record['id'], fields)
        await ctx.channel.send(strings)

    elif author == angel:
        record = airtable.match('Name', 'Angel')
        fuck_value = record['fields']['Fucks']
        number_fuck = int(fuck_value)
        if fucks:
            try: 
                total = number_fuck + int(fucks)
            except:
                nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
                await ctx.channel.send(nonint_error_msg)
        else:
            total = number_fuck + 1
        total_str = str(total)
        print(total_str)
        strings = f'You have been fucked {total_str} times.'
        fields = {'Fucks': total_str}
        airtable.update(record['id'], fields)
        await ctx.channel.send(strings)

    elif author == jacob:
        record = airtable.match('Name', 'Jacob')
        fuck_value = record['fields']['Fucks']
        number_fuck = int(fuck_value)
        if fucks:
            try: 
                total = number_fuck + int(fucks)
            except:
                nonint_error_msg = 'You did not enter a valid number of fucks. Try again.'
                await ctx.channel.send(nonint_error_msg)
        else:
            total = number_fuck + 1
        total_str = str(total)
        print(total_str)
        strings = f'You have been fucked {total_str} times.'
        fields = {'Fucks': total_str}
        airtable.update(record['id'], fields)
        await ctx.channel.send(strings)

@bot.command()
async def feelingsJacob(ctx):
        record = feelings_airtable.match('Name', 'Jacob')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Jacob are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Jacob', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Jacob', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Jacob', number_feeling)
            await ctx.channel.send(negative_message)

@bot.command()
async def feelingsMag(ctx):
        record = feelings_airtable.match('Name', 'Mag')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Mag are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Mag', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Mag', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Mag', number_feeling)
            await ctx.channel.send(negative_message)
            
@bot.command()
async def feelingsDave(ctx):
        record = feelings_airtable.match('Name', 'Dave')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Dave are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Dave', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Dave', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Dave', number_feeling)
            await ctx.channel.send(negative_message)

@bot.command()
async def feelingsRyan(ctx):
        record = feelings_airtable.match('Name', 'Ryan')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Ryan are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Ryan', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Ryan', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Ryan', number_feeling)
            await ctx.channel.send(negative_message)

@bot.command()
async def feelingsJer(ctx):
        record = feelings_airtable.match('Name', 'Jer')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Jer are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Jer', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Jer', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Jer', number_feeling)
            await ctx.channel.send(negative_message)

@bot.command()
async def feelingsCaleb(ctx):
        record = feelings_airtable.match('Name', 'Caleb')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Caleb are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Caleb', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Caleb', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Caleb', number_feeling)
            await ctx.channel.send(negative_message)

@bot.command()
async def feelingsAsh(ctx):
        record = feelings_airtable.match('Name', 'Ash')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Ash are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Ash', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Ash', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Ash', number_feeling)
            await ctx.channel.send(negative_message)

@bot.command()
async def feelingsAlex(ctx):
        record = feelings_airtable.match('Name', 'Alex')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Alex are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Alex', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Alex', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Alex', number_feeling)
            await ctx.channel.send(negative_message)

@bot.command()
async def feelingsAngel(ctx):
        record = feelings_airtable.match('Name', 'Angel')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Angel are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Angel', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Angel', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Angel', number_feeling)
            await ctx.channel.send(negative_message)
#Function for getting the correct feeling response from the bot. Feed in a user and the value of the feelingscore
def feeling_response(user, feeling_num):
    if user == 'Ryan':
        if feeling_num == 0:
            neutral = f'I have no strong feelings towards Ryan one way or the other.'
            return neutral
        elif 0 < feeling_num < 50 :
            positive = f'I like Ryan.'
            return positive
        elif feeling_num < 0:
            negative = f'I do not like Ryan very much.'
            return negative 

    if user == 'Jacob':
        if feeling_num == 0:
            neutral = f'I have no strong feelings towards Jacob one way or the other.'
            return neutral
        elif 0 < feeling_num < 50 :
            positive = f'I like Jacob.'
            return positive
        elif feeling_num < 0:
            negative = f'I do not like Jacob very much.'
            return negative 

    if user == 'Dave':
        if feeling_num == 0:
            neutral = f'I have no strong feelings towards Dave one way or the other.'
            return neutral
        elif 0 < feeling_num < 50 :
            positive = f'I like Dave.'
            return positive
        elif feeling_num < 0:
            negative = f'I do not like Dave very much.'
            return negative 

    if user == 'Ash':
        if feeling_num == 0:
            neutral = f'I have no strong feelings towards Ash one way or the other.'
            return neutral
        elif 0 < feeling_num < 50 :
            positive = f'I like Ash.'
            return positive
        elif feeling_num < 0:
            negative = f'I do not like Ash very much.'
            return negative 

    if user == 'Caleb':
        if feeling_num == 0:
            neutral = f'I have no strong feelings towards Caleb one way or the other.'
            return neutral
        elif 0 < feeling_num < 50 :
            positive = f'I like Caleb.'
            return positive
        elif feeling_num < 0:
            negative = f'I do not like Caleb very much.'
            return negative 

    if user == 'Angel':
        if feeling_num == 0:
            neutral = f'I have no strong feelings towards Angel one way or the other.'
            return neutral
        elif 0 < feeling_num < 50 :
            positive = f'I like Angel.'
            return positive
        elif feeling_num < 0:
            negative = f'I do not like Angel very much.'
            return negative 

    if user == 'Jer':
        if feeling_num == 0:
            neutral = f'I have no strong feelings towards Jer one way or the other.'
            return neutral
        elif 0 < feeling_num < 50 :
            positive = f'I like Jer.'
            return positive
        elif feeling_num < 0:
            negative = f'I do not like Jer very much.'
            return negative 

    if user == 'Alex':
        if feeling_num == 0:
            neutral = f'I have no strong feelings towards Alex one way or the other.'
            return neutral
        elif 0 < feeling_num < 50 :
            positive = f'I like Alex.'
            return positive
        elif feeling_num < 0:
            negative = f'I do not like Alex very much.'
            return negative 

@bot.command(pass_context=True)
async def checkfeelings(ctx):
    ryan = 482050383821406208
    dave = 160597904606756865
    jer = 160589867976228864
    angel = 712495135660965958
    jacob = 597489707877793943
    caleb = 173599110853689347
    Alex = 265745906484117505
    ash = 160590856833728522
    
    author = ctx.author.id

    if author == ryan:
        record = feelings_airtable.match('Name', 'Ryan')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Ryan are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Ryan', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Ryan', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Ryan', number_feeling)
            await ctx.channel.send(negative_message)

    #Jacob's feelings
    if author == jacob:
        record = feelings_airtable.match('Name', 'Jacob')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Jacob are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Jacob', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Jacob', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Jacob', number_feeling)
            await ctx.channel.send(negative_message)

    if author == dave:
        record = feelings_airtable.match('Name', 'Dave')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Dave are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Dave', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Dave', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Dave', number_feeling)
            await ctx.channel.send(negative_message)

    if author == caleb:
        record = feelings_airtable.match('Name', 'Caleb')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Caleb are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Caleb', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Caleb', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Caleb', number_feeling)
            await ctx.channel.send(negative_message)

    if author == ash:
        record = feelings_airtable.match('Name', 'Ash')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Ash are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Ash', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Ash', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Ash', number_feeling)
            await ctx.channel.send(negative_message)

    if author == angel:
        record = feelings_airtable.match('Name', 'Angel')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Angel are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Angel', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Angel', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Angel', number_feeling)
            await ctx.channel.send(negative_message)

    if author == jer:
        record = feelings_airtable.match('Name', 'Jer')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Jer are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Jer', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Jer', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Jer', number_feeling)
            await ctx.channel.send(negative_message)

    if author == Alex:
        record = feelings_airtable.match('Name', 'Alex')
        feeling_value = record['fields']['feelingscore']
        number_feeling = int(feeling_value)
        print(number_feeling)
        response = f'My feelings about Alex are currently at {feeling_value}'
        await ctx.channel.send(response)
        if number_feeling == 0:
            neutral_message = feeling_response('Alex', number_feeling)
            await ctx.channel.send(neutral_message)
        elif number_feeling > 0:
            pos_message = feeling_response('Alex', number_feeling)
            await ctx.channel.send(pos_message)
        if number_feeling < 0:
            negative_message = feeling_response('Alex', number_feeling)
            await ctx.channel.send(negative_message)

            
# !checkfucks Command for listing the fuck list
@bot.command(pass_context=True)
async def checkfucks(ctx):
    
    ryan = 482050383821406208
    dave = 160597904606756865
    jer = 160589867976228864
    angel = 712495135660965958

    search = airtable.search('Name', 'Dave')

    user = ctx.author.id 
    #print(ctx.author.id)
    if user == bot.user:
        return
    else:
        fs = airtableDownload("appILX4NST2XuPcJS" , "FuckList")
        df = airtableToDataframe(fs)
        df_noindex = df.to_string(index=False)
        await ctx.channel.send(df_noindex)


@bot.command()
@commands.is_owner()
async def test(ctx):
    embed.add_field(name=f'Ryan', value=f'> Fucks: 69\n> Praise: 3\n>',inline=False)
    await ctx.send(embed=embed)

@bot.command()
@commands.is_owner()
async def spam(ctx):
    my_api_key = "AIzaSyAiOVqM0F9kRZwBNBqsSJK-xfsXiIzOUxc"
    my_cse_id = "99737d1c05b083ef0"

    def google_search(search_term, api_key, cse_id, **kwargs):
        service = build("customsearch", "v1", developerKey=api_key)
        res = service.cse().list(q=search_term, cx=cse_id, **kwargs).execute()
        return res['items']

    results = google_search(
        ctx.message.content[5:], my_api_key, my_cse_id, num=10)
    #for result in results:
    #    pprint.pprint(result)

    first_result = results[0]

    page_map = first_result.get('pagemap')

    images = page_map.get('cse_image')

    print(images)

    urls = []

    for item in range(0,10):
        result = results[item]
        page_map = result.get('pagemap')
        image = page_map.get('cse_image')
        urls.append(image)

    print(urls)
    await ctx.channel.send(urls)

def user_id(user):
    ryan = 482050383821406208
    dave = 160597904606756865
    jer = 160589867976228864
    angel = 712495135660965958
    jacob = 597489707877793943
    caleb = 173599110853689347
    Alex = 265745906484117505
    ash = 160590856833728522

    if user == 'Ryan':
        return ryan
    elif user == 'Dave':
        return dave
    elif user == 'Jer':
        return jer
    elif user == 'Angel':
        return angel
    elif user == 'Jacob':
        return jacob
    elif user == 'Caleb':
        return caleb
    elif user == 'Alex':
        return alex
    elif user == 'Ash':
        return ash

if __name__ == "__main__" :
    bot.run(TOKEN)