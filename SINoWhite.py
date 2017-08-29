import discord
from discord.ext import commands
import random
import codecs
import asyncio
import TimeUtils as tu
import DailyTask as dt
import jisho as js
import EventTracker as et
import json
from numpy.random import permutation

##############
#Bot Config filepath
config_filepath = 'config.json'

##############
#Vars
token = ''
command_prefix = ''
colo_notify = True
description = 'SINoWhite bot for TeaParty'
##############

##############
#Channels
##############
#TeaParty Channels
bot_test_channel = ''
lobby_channel = ''
##############

##############
#SQL vars
#Currently not in use
sql_uri = "localhost"
sql_user = "sinowhite"
sql_pw = "etihwonis"
sql_db = "sinowhite"
##############

#########################################################################################
#Boot up procedure for bot
config = None
with open(config_filepath, 'r') as f:
    config = json.load(f)
    print('------')
    print ('Loading config file...')
    token = config['token']
    print ('token:', token)
    command_prefix = config['command_prefix']
    print ('command_prefix:', command_prefix)
    colo_notify = config['colo_notify']
    print ('colo_notify:', colo_notify)
    bot_test_channel = config['bot_test_channel']
    print ('bot_test_channel:', bot_test_channel)
    lobby_channel = config['lobby_channel']
    print ('lobby_channel:', lobby_channel)
    print('------')

bot = commands.Bot(command_prefix=command_prefix, description=description)
tracker = None

#########################################################################################
#Dev-only commands (hidden)
@bot.command(description='Set flag for whether to notify people about colo or not', hidden=True)
async def __notify_flag(flag:bool):
    global colo_notify
    if flag:
        colo_notify = True
        await bot.say('Flag is turned on')
    else:
        colo_notify = False
        await bot.say('Flag is turned off')
        
    time_stamp = tu.time_now()
    print (time_stamp + " DEV Flag update: colo_notify = " + str(colo_notify))

@bot.command(description='Backup variables to json', hidden=True)
async def __backup():
    dump = json.dumps({'token':token,
                         'command_prefix':command_prefix,
                         'bot_test_channel':bot_test_channel,
                         'lobby_channel':lobby_channel,
                         'colo_notify':colo_notify})
    with open(config_filepath + '.bak', 'w') as f:
        f.write(dump)
        f.close()

    time_stamp = tu.time_now()
    print (time_stamp + " DEV Backup Performed")
    await bot.say('Backup complete')

#########################################################################################
#Notifications module

async def notifymsg(channel_id, msg, caller_func_name, delete=True, useEmbed=True):
    """
    Sends a notification message to channel
    providing calling function for logging purposes
    """
    channel = bot.get_channel(channel_id)
    if(channel is None):
        print ("CHANNEL ERROR! See " + caller_func_name)
    else:
        sent_msg = None
        if useEmbed:
            embed_msg = discord.Embed()
            embed_msg.title = msg
            sent_msg = await bot.send_message(channel, embed=embed_msg)
        else:
            sent_msg = await bot.send_message(channel, content=msg)
        
        time_stamp = tu.time_now()
        print (time_stamp + " INFO Message with id " + sent_msg.id + " sent to channel " + channel.name + ": " + msg)

        #Deletes messsage after 30mins if flag is turned on
        if(delete):
            print (time_stamp + " INFO Message with id " + sent_msg.id + " scheduled for delete after 30mins")
            await asyncio.sleep(1800)
            await bot.delete_message(sent_msg)
            delete_time_stamp = tu.time_now()
            print (delete_time_stamp + " INFO Message sent to channel " + channel.name + " with id " + sent_msg.id + " deleted")
            sent_msg = None

async def pingtabsmsg():
    if colo_notify:
        await notifymsg(lobby_channel, '<@253362110975836160> It\'s colo time <:blobhyperthink:347369958302547968>', 'pingtabsmsg()', delete=False, useEmbed=False)
    else:
        time_stamp = tu.time_now()
        print (time_stamp + ' INFO ' +'pingtabsmsg() not fired because colo_notify flag is turned off')

async def pingtabstask():
    task = dt.DailyTask(pingtabsmsg, 'Ping tabs for colo', tu.TimeOfDay(13, 55))
    await task.start()

async def dailyexpmsg():
    await notifymsg(lobby_channel, 'Daily EXP dungeons are up!', 'dailyexpmsg()')

async def dailyexptask():
    #1:00 JST
    task = dt.DailyTask(dailyexpmsg, "dailyexpmsg() 1:00 JST", tu.TimeOfDay(16, 0))
    await task.start()
    #7:30 JST
    task = dt.DailyTask(dailyexpmsg, "dailyexpmsg() 7:30 JST", tu.TimeOfDay(22, 30))
    await task.start()
    #12:00 JST
    task = dt.DailyTask(dailyexpmsg, "dailyexpmsg() 12:00 JST", tu.TimeOfDay(3, 0))
    await task.start()
    #19:30 JST
    task = dt.DailyTask(dailyexpmsg, "dailyexpmsg() 19:30 JST", tu.TimeOfDay(10, 30))
    await task.start()
    #22:30 JST
    task = dt.DailyTask(dailyexpmsg, "dailyexpmsg() 22:30 JST", tu.TimeOfDay(13, 30))
    await task.start()

async def fafnirmsg():
    await notifymsg(lobby_channel, 'Fafnir Dungeon is up!', 'fafnirmsg()')

async def fafnirtask():
    #1:30 JST
    task = dt.DailyTask(fafnirmsg, "fafnirmsg() 1:30 JST", tu.TimeOfDay(16, 30))
    await task.start()
    #8:30 JST
    task = dt.DailyTask(fafnirmsg, "fafnirmsg() 8:30 JST", tu.TimeOfDay(23, 30))
    await task.start()
    #12:00 JST
    task = dt.DailyTask(fafnirmsg, "fafnirmsg() 12:00 JST", tu.TimeOfDay(3, 0))
    await task.start()
    #20:30 JST
    task = dt.DailyTask(fafnirmsg, "fafnirmsg() 20:30 JST", tu.TimeOfDay(11, 30))
    await task.start()
    #23:30 JST
    task = dt.DailyTask(fafnirmsg, "fafnirmsg() 23:30 JST", tu.TimeOfDay(14, 30))
    await task.start()

async def completedailymsg():
    await notifymsg(lobby_channel, 'Remember to complete your daily missions!', 'completedailymsg()')

async def completedailytask():
    task = dt.DailyTask(completedailymsg, "completedailymsg() 23:20 JST", tu.TimeOfDay(14, 20))
    await task.start()

#########################################################################################

@bot.event
async def on_ready():
    print(tu.time_now() + ' Logged in as')
    print('Username: ' + bot.user.name)
    print('Bot Id: ' + bot.user.id)
    print('------')

    #######################
    #Notifications go here
    #######################

    print('Seting up Scheduled Notifications...')

    #Active
    await fafnirtask()
    await dailyexptask()
    await completedailytask()
    await pingtabstask()
    
    print('All Scheduled Notifications Queued')

    #######################
    #Tracker module
    #######################

    print('Seting up Tracker...')
    
    global tracker
    tracker = et.EventTracker()
    eventlist_exp = [tu.TimeOfDay(16, 0),\
                 tu.TimeOfDay(22, 30),\
                 tu.TimeOfDay(3, 0),\
                 tu.TimeOfDay(10, 30),\
                 tu.TimeOfDay(13, 30)]
    tracker.addEvent('exp', eventlist_exp)
    
    eventlist_fafnir = [tu.TimeOfDay(16, 30),\
                 tu.TimeOfDay(23, 30),\
                 tu.TimeOfDay(3, 0),\
                 tu.TimeOfDay(11, 30),\
                 tu.TimeOfDay(14, 30)]
    tracker.addEvent('fafnir', eventlist_fafnir)
    

    print('Tracker ready')
    print('------')

#########################################################################################
#General
@bot.command(description='Can\'t decide on something? Let me decide for you.')
async def choose(*choices : str):
    """Choose between multiple choices."""
    if len(choices) > 1:
        await bot.say(":thinking: how about "+ random.choice(choices) + " ?")
    else:
        await bot.say("?")

@bot.command(description='Find out when a member joined the server.')
async def joined(member : discord.Member):
    await bot.say('{0.name} joined on {0.joined_at}'.format(member))

#########################################################################################
#Jisho module
@bot.command(pass_context=True, description='*Only shows the top result to avoid cluttering the chat too much')
async def jisho(ctx, *, query : str):
    """Consult the jisho.org dictionary"""
    result = await js.j2e(query)
    result_limit = 1

    #logging
    print(tu.time_now() + ' jisho - ' + str(len(result)) + ' result(s) for query: ' + query)
    
    embed = discord.Embed()
    embed.title = str(len(result)) + ' result(s)'
    if(len(result) > result_limit): embed.title += ' showing only the best result'
    text = ''

    if (len(result) == 0):
        text += 'Query was: ' + query
        text += '\nCheck if something is missing?'
    
    counter = 1
    for hits in result:
        if(counter > result_limit): break
        if(counter != 1):
            text += '\n'

        #Primary Yomikata
        japanese = hits.japanese
        main_reading = japanese[0]
        if('word' in main_reading):
            text += '**'+main_reading['word']+'**'
            text += ' ('+main_reading['reading']+')'
        else:
            text += '**'+main_reading['reading']+'**'
            
        text += '\n'
        japanese.pop(0)

        #Definition(s)
        definitions = hits.definitions
        defn_counter = 1
        for definition in definitions:
            text += str(defn_counter) + ". "
            idx = 1
            for value in definition:
                if(idx != 1):
                    text += ', '
                text += value
                idx = idx + 1
            text += '\n'
            defn_counter = defn_counter + 1

        #Other Yomikata
        other_counter = 1
        if(len(japanese) > 0):
            text += 'Other forms: '
        for other_reading in japanese:
            if(other_counter > 1):
                text += ', '
            if('word' in other_reading):
                text += other_reading['word']
                text += ' ('+other_reading['reading']+')'
            else:
                text+= other_reading['reading']
            
        counter = counter + 1
    embed.description = text
        
    await bot.send_message(ctx.message.channel, embed=embed)

#########################################################################################
#Event-specific
@bot.command(pass_context=False)
async def exp():
    """
    Find out when the next event window opens
    """
    hours, minutes = tracker.nextEventTime('exp')
    if hours > 0:
        await bot.say(str(hours)+' hrs and '+str(minutes) +'mins till start of next exp window')
    else:
        await bot.say(str(minutes) +'mins till start of next exp window')

@bot.group(pass_context=True, description='Available options: fafnir, midgard, ogre')
async def raid(ctx):
    """
    Check Raid timings
    """
    if ctx.invoked_subcommand is None:
        await bot.say('**' + command_prefix + 'help raid** for options')

@raid.command(pass_context=True)
async def fafnir(ctx):
    title = 'Fafnir Time Slots'
    msg = ''

    if tracker.hasEvent('fafnir'):
        eventTimes = tracker.getEvent('fafnir')
        
        for eventTime in eventTimes:
            msg += '\n\t' + eventTime.toJST(ctx)

        msg += '\n'

        hours, minutes = tracker.nextEventTime('fafnir')
        if hours > 0:
            msg += str(hours)+' hrs and '+str(minutes) +'mins till start of next window'
        else:
            msg +=str(minutes) +'mins till start of next window'

        embed_msg = discord.Embed()
        embed_msg.title = title
        embed_msg.description = msg
        await bot.send_message(ctx.message.channel, embed=embed_msg)
    else:
        await notify_msg(ctx.message.channel, "Sorry, an error has occured.", delete=True, useEmbed=True)



#########################################################################################
#Dice rolling
@bot.command()
async def roll(N=10, M=1):
    """
    Generates M random integers in the range 1 to N
    """
    result = ', '.join(str(random.randint(1, N)) for r in range(M))
    await bot.say('Roll result: ' + result)

@bot.command()
async def rollz(N=10, M=1):
    """
    Generates M random integers in the range 0 to N
    """
    result = ', '.join(str(random.randint(0, N)) for r in range(M))
    await bot.say('Roll result: ' + result)

@bot.command(pass_context=True)
async def randp(ctx, *names : str):
    """
    Generates a random permutation of the inputs
    """
    permutation_result = permutation(len(names))
    reply = 'Result:'
    for i in range(len(names)):
        reply += '\n\t' + str(i+1) + '. ' + names[permutation_result[i]]

    await bot.say(reply)

#########################################################################################
#Emotes
@bot.group(pass_context=True, description='See emote options by invoking the help command')
async def emote(ctx):
    """
    Use Emotes
    """
    if ctx.invoked_subcommand is None:
        await bot.say('**' + command_prefix + 'help emote** for options')

@emote.command(pass_context=True)
async def thanks(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp001s.png')

@emote.command(pass_context=True)
async def unavoidable(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp002s.png')

@emote.command(pass_context=True)
async def yoroshiku(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp003s.png')

@emote.command(pass_context=True)
async def damn(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp004s.png')

@emote.command(pass_context=True)
async def weak(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp005s.png')

@emote.command(pass_context=True)
async def oops(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp006s.png')

@emote.command(pass_context=True)
async def hardcarry(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp007s.png')

@emote.command(pass_context=True)
async def yandere(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp008s.png')

@emote.command(pass_context=True)
async def ok(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp009s.png')

@emote.command(pass_context=True)
async def wants(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp010s.png')

@emote.command(pass_context=True)
async def rekt(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp011s.png')

@emote.command(pass_context=True)
async def oatscurry(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp012s.png')

@emote.command(pass_context=True)
async def rip(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp013s.png')

@emote.command(pass_context=True)
async def sleep(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp014s.png')

@emote.command(pass_context=True)
async def yay(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp015s.png')

@emote.command(pass_context=True)
async def yes(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp016s.png')

@emote.command(pass_context=True)
async def masaka(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp017s.png')

@emote.command(pass_context=True)
async def annoyed(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp018s.png')

@emote.command(pass_context=True)
async def wow(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp019s.png')

@emote.command(pass_context=True)
async def angry(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp020s.png')

@emote.command(pass_context=True)
async def noo(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp021s.png')

@emote.command(pass_context=True)
async def peace(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp022s.png')

@emote.command(pass_context=True)
async def forgetthat(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp023s.png')

@emote.command(pass_context=True)
async def sorry(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp024s.png')

@emote.command(pass_context=True)
async def teehee(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp025s.png')

@emote.command(pass_context=True)
async def guessso(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp026s.png')

@emote.command(pass_context=True)
async def thatsit(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp027s.png')

@emote.command(pass_context=True)
async def wut(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp028s.png')

@emote.command(pass_context=True)
async def cmi(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp029s.png')

@emote.command(pass_context=True)
async def trolol(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp030s.png')

#########################################################################################
#Database
#THERE IS NO DB FOR NOW
#@bot.command()
#async def testdb():
#    """Tests connection to the database"""
#    db = mys.connect(host=sql_uri, user=sql_user, passwd=sql_pw, db=sql_db)
#    if(db):
#       await bot.say("Connection successful")
#    else:
#        await bot.say("Connection failed!")

bot.run(token)
