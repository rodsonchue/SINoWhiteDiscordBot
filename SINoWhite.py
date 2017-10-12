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
from shutil import copyfile
import os.path

##############
# Cogs
import Danbooru
cogs = ["Danbooru"]

##############
#Bot Config filepath
config_filepath = 'config.json'

##############
#Vars
token = ''
command_prefix = ''
colo_notify = True
description = 'SINoWhite bot for TeaParty'
trackedEvents = {}
locked_roles = []
colo_join = {}
colo_cached_names = {}
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
#Boot up procedure for bot (Before login)

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
    
    if 'trackedEvents' in config:
        for eventName, timeLst in config['trackedEvents'].items():
            eventTimeLst = []
            for hr, mins in timeLst:
                eventTimeLst.append(tu.TimeOfDay(hr, mins))
                
            trackedEvents[eventName] = eventTimeLst
        
        print ('trackedEvents: ' + ', '.join('{}'.format(key) for key in trackedEvents.keys()))
    else:
        print ('Warning: trackedEvents field missing from config!')


    if 'locked_roles' in config:
        locked_roles = config['locked_roles']
        print ('locked_roles: ' + ', '.join('{}'.format(role) for role in locked_roles))
    else:
        print ('Warning: No locked_roles set')

    if 'colo_join' in config:
        colo_join = config['colo_join']
        print ('colo_join: ', colo_join)
    else:
        print ('Warning: No colo_join set')

bot = commands.Bot(command_prefix=command_prefix, description=description)
print('------')

print ('Loading cogs')
for cog in cogs:
    try:
        bot.load_extension(cog)
        print ("\t" + cog + " cog loaded")
    except Exception as e:
        exc = '{}: {}'.format(type(e).__name__, e)
        print('Failed to load extension {}\n{}'.format(cog, exc))
print('------')

############################
#For tracker module
print('Seting up Tracker...')
tracker = et.EventTracker()
for eventName, eventTimeLst in trackedEvents.items():
    tracker.addEvent(eventName, eventTimeLst);
print('Tracker ready')
print('------')

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

async def doBackup():
    
    dump = json.dumps({'token':token,
                         'command_prefix':command_prefix,
                         'bot_test_channel':bot_test_channel,
                         'lobby_channel':lobby_channel,
                         'colo_notify':colo_notify,
                       'trackedEvents':trackedEvents,
                       'locked_roles':locked_roles,
                       'colo_join':colo_join}, cls=tu.TodEncoder)
    
    with open(config_filepath + '.bak', 'w') as f:
        f.write(dump)
        f.close()

    time_stamp = tu.time_now()
    print (time_stamp + " DEV Backup Performed\nDump:", dump)

async def useBackup():
    if not os.path.isfile(config_filepath+'.bak'):
        time_stamp = tu.time_now()
        print (time_stamp + " DEV No backup found!")
        await doBackup()
        
    copyfile(config_filepath+'.bak', config_filepath)
    time_stamp = tu.time_now()
    print (time_stamp + " DEV Overwrite config with backup ")

@bot.command(description='Backup variables to json', hidden=True)
async def __backup():
    await doBackup()
    sent_msg =  await bot.say('Backup complete')

    #Delete msg after 5s
    await asyncio.sleep(5)
    await bot.delete_message(sent_msg)

@bot.command(description='Use backup json for next bootup', hidden=True)
async def __useBackup():
    await useBackup()
    sent_msg =  await bot.say('Using backup for next bootup')

    #Delete msg after 5s
    await asyncio.sleep(5)
    await bot.delete_message(sent_msg)

async def reset_participation():
    # Resets everyone's attendance, assume to be not participating
    for userid in colo_join:
        colo_join[userid] = False

    time_stamp = tu.time_now()
    print (time_stamp + " DEV Reset Colo Participation")

    await doBackup()

@bot.command(description='Resets all colo participation status', hidden=True)
async def __resetcolo():
    await reset_participation()

    sent_msg =  await bot.say('Colo Participation Reset')
    time_stamp = tu.time_now()

    #Delete msg after 5s
    await asyncio.sleep(5)
    await bot.delete_message(sent_msg)
    

@bot.command(description='Clears the cache for user nicknames', hidden=True)
async def __clearcachednames():
    colo_cached_names.clear()
    
    sent_msg =  await bot.say('Colo Cached Names cleared')
    time_stamp = tu.time_now()
    print (time_stamp + " DEV Cleared Colo Cache ")

    #Delete msg after 5s
    await asyncio.sleep(5)
    await bot.delete_message(sent_msg)
    

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
    await notifymsg(lobby_channel, 'Fafnir Raid is up!', 'fafnirmsg()')

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

async def fenrirmsg():
    await notifymsg(lobby_channel, 'Fenrir Raid is up!', 'fenrirmsg()')

async def fenrirtask():
    #1:30 JST
    task = dt.DailyTask(fenrirmsg, "fenrirmsg() 1:30 JST", tu.TimeOfDay(16, 30))
    await task.start()
    #8:30 JST
    task = dt.DailyTask(fenrirmsg, "fenrirmsg() 8:30 JST", tu.TimeOfDay(23, 30))
    await task.start()
    #12:00 JST
    task = dt.DailyTask(fenrirmsg, "fenrirmsg() 12:00 JST", tu.TimeOfDay(3, 0))
    await task.start()
    #20:30 JST
    task = dt.DailyTask(fenrirmsg, "fenrirmsg() 20:30 JST", tu.TimeOfDay(11, 30))
    await task.start()
    #23:30 JST
    task = dt.DailyTask(fenrirmsg, "fenrirmsg() 23:30 JST", tu.TimeOfDay(14, 30))
    await task.start()

async def ogremsg():
    await notifymsg(lobby_channel, 'Ogre Raid is up!', 'ogremsg()')

async def ogretask():
    #1:30 JST
    task = dt.DailyTask(ogremsg, "ogremsg() 1:30 JST", tu.TimeOfDay(16, 30))
    await task.start()
    #8:30 JST
    task = dt.DailyTask(ogremsg, "ogremsg() 8:30 JST", tu.TimeOfDay(23, 30))
    await task.start()
    #12:00 JST
    task = dt.DailyTask(ogremsg, "ogremsg() 12:00 JST", tu.TimeOfDay(3, 0))
    await task.start()
    #20:30 JST
    task = dt.DailyTask(ogremsg, "ogremsg() 20:30 JST", tu.TimeOfDay(11, 30))
    await task.start()
    #23:30 JST
    task = dt.DailyTask(ogremsg, "ogremsg() 23:30 JST", tu.TimeOfDay(14, 30))
    await task.start()

async def spidermsg():
    await notifymsg(lobby_channel, 'Spider Raid is up!', 'spidermsg()')

async def spidertask():
    #1:30 JST
    task = dt.DailyTask(spidermsg, "spidermsg() 1:30 JST", tu.TimeOfDay(16, 30))
    await task.start()
    #8:30 JST
    task = dt.DailyTask(spidermsg, "spidermsg() 8:30 JST", tu.TimeOfDay(23, 30))
    await task.start()
    #12:00 JST
    task = dt.DailyTask(spidermsg, "spidermsg() 12:00 JST", tu.TimeOfDay(3, 0))
    await task.start()
    #20:30 JST
    task = dt.DailyTask(spidermsg, "spidermsg() 20:30 JST", tu.TimeOfDay(11, 30))
    await task.start()
    #23:30 JST
    task = dt.DailyTask(spidermsg, "spidermsg() 23:30 JST", tu.TimeOfDay(14, 30))
    await task.start()

async def completedailymsg():
    await notifymsg(lobby_channel, 'Remember to claim your daily cleaning ticket!', 'completedailymsg()', delete=False, useEmbed=True)
    await reset_participation()
    
async def completedailytask():
    task = dt.DailyTask(completedailymsg, "completedailymsg() 23:40 JST", tu.TimeOfDay(14, 40))
    await task.start()

#########################################################################################
#Bot warm up procedure
firstBoot = True
    
@bot.event
async def on_ready():
    print('------')
    print(tu.time_now() + ' Logged in as')
    print('Username: ' + bot.user.name)
    print('Bot Id: ' + bot.user.id)
    print('------')

    global firstBoot
    if firstBoot:
        #######################
        #Notifications go here
        #######################

        print('Seting up Scheduled Notifications...')

        #Active
        #await fafnirtask()
        #await fenrirtask()
        #await ogretask()
        await spidertask()
        await dailyexptask()
        await completedailytask()
        await pingtabstask()
        
        print('All Scheduled Notifications Queued')

        print('------')
        
        firstBoot = False

#########################################################################################
#General
@bot.command(description='Can\'t decide on something? Let me decide for you.')
async def choose(*choices : str):
    """
    Choose between multiple choices
    """
    if len(choices) > 1:
        await bot.say(":thinking: how about "+ random.choice(choices) + " ?")
    else:
        await bot.say("?")

@bot.command()
async def joined(member : discord.Member):
    """
    Find out when a member joined the server
    """
    await bot.say('{0.name} joined on {0.joined_at}'.format(member))

async def findRoleInServer(ctx, role_name):
    roles = ctx.message.server.roles

    skip = True
    for role in roles:
        if skip:
            skip = False
        elif role_name.lower() == role.name.lower():
            return role
    return None

@bot.command(pass_context=True)
async def addrole(ctx, *role_name : str):
    """
    Add a role to yourself
    """
    role = await findRoleInServer(ctx, ' '.join(role_name))

    if role is None:
        await bot.say ("Role not found.")
    elif role in ctx.message.author.roles:
        await bot.say ("You already have the role.")
    else:
        try:
            await bot.add_roles(ctx.message.author, role)
            await bot.say("Role added!")
        except discord.Forbidden:
            await bot.say("I do not have permisssion to add that role.")

@bot.command(pass_context=True)
async def removerole(ctx, *role_name : str):
    """
    Remove a role from yourself
    """
    role = findRoleInServer(ctx, ' '.join(role_name))

    if role is None:
        await bot.say ("Role not found.")
    elif role not in ctx.message.author.roles:
        await bot.say ("You don't have this role.")
    else:
        try:
            await bot.remove_roles(ctx.message.author, role)
            await bot.say("Role removed.")
        except discord.Forbidden:
            await bot.say("I do not have permisssion to remove that role.")

@bot.command(pass_context=True)
async def rolelist(ctx):
    """
    Lists all the roles
    """
    roles = ctx.message.server.roles

    role_names = []
    skip = True
    for role in roles:
        if skip:
            skip = False
        else:
            role_names.append(role.name)

    await bot.say("Roles: " + ', '.join(role_names))

@bot.command(pass_context=True)
async def join(ctx):
    """
    Indicate that you are participating in the colosseum for the day
    """
    userid = ctx.message.author.id
    
    server = discord.utils.find(lambda s: s.id == '342171098168688640', bot.servers)
    if server:
        member = discord.utils.find(lambda m: m.id == userid, server.members)
        if member:
            alias = member.name
            if member.nick is not None:
                alias = member.nick
                
            colo_join[userid] = True
            await bot.say(alias + " is joining us for colo today")
            
            time_stamp = tu.time_now()
            print (time_stamp + "INFO User " + alias + " colo_join = True")
            return

    await bot.say('An unknown error has occured.')

@bot.command(pass_context=True)
async def unjoin(ctx):
    """
    Indicate that you are not participating in the colosseum for the day
    """
    userid = ctx.message.author.id
    
    server = discord.utils.find(lambda s: s.id == '342171098168688640', bot.servers)
    if server:
        member = discord.utils.find(lambda m: m.id == userid, server.members)
        if member:
            alias = member.name
            if member.nick is not None:
                alias = member.nick
                
            colo_join[member.id] = False
            await bot.say(alias + " is **not** joining us for colo today")
            
            time_stamp = tu.time_now()
            print (time_stamp + "INFO User " + alias + " colo_join = False")
            return

    await bot.say('An unknown error has occured.')

@bot.command(pass_context=True)
async def colo(ctx):
    participants = []
    nonParticipants = []
    time_stamp = tu.time_now()
    for userid, isParticipating in colo_join.items():
        alias = None
        if userid in colo_cached_names:
            alias = colo_cached_names[userid]
        else:
            server = discord.utils.find(lambda s: s.id == '342171098168688640', bot.servers)
            if server:
                member = discord.utils.find(lambda m: m.id == userid, server.members)
                if member:
                    alias = member.name
                    if member.nick is not None:
                        alias = member.nick
                else:
                    print (time_stamp + 'ERROR Member with id ' + userid + ' not found in server')
            else:
                print (time_stamp + 'ERROR Cannot find server with id 342171098168688640')

            # Alternate search method, is slower but just incase the above fails
            if alias is None:
                member = await bot.get_user_info(userid)
                alias = member.name

            colo_cached_names[userid] = alias
        
        if isParticipating:
            participants.append(alias)
        else:
            nonParticipants.append(alias)

    await bot.say("Participating: " + str(len(participants)) + '\n\t' + ", ".join(participants) +'\n\n' + \
                  "Not Participating: " + str(len(nonParticipants)) + '\n\t' + ", ".join(nonParticipants))

#########################################################################################
#Jisho module
@bot.command(pass_context=True, description='*Only shows the top result to avoid cluttering the chat too much')
async def jisho(ctx, *, query : str):
    """
    Consult the jisho.org dictionary
    """
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
            if('reading' in main_reading):
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
        await bot.say(str(hours)+' hrs and '+str(minutes) +' mins till start of next exp window')
    else:
        await bot.say(str(minutes) +' mins till start of next exp window')

@bot.group(pass_context=True, description='Available options: fafnir, midgard, ogre, spider')
async def raid(ctx):
    """
    Check Raid timings
    """
    if ctx.invoked_subcommand is None:
        await raid_message(ctx, 'Spider Time Slots', 'spider', 'spider()', 'https://pbs.twimg.com/media/DK4d6BQUMAAjdEc.jpg')
        #await bot.say('**' + command_prefix + 'help raid** for options')

async def raid_message(ctx, title, raidName, func_name, image_url=None):
    msg = ''

    if tracker.hasEvent(raidName):
        eventTimes = tracker.getEvent(raidName)
        
        for eventTime in eventTimes:
            msg += '\n' + eventTime.toJST()

        msg += '\n\n'

        hours, minutes = tracker.nextEventTime(raidName)
        if hours > 0:
            msg += str(hours)+' hrs and '+str(minutes) +' mins till start of next window'
        else:
            msg +=str(minutes) +'mins till start of next window'

        embed_msg = discord.Embed()
        embed_msg.title = title
        embed_msg.description = msg
        if image_url is not None:
            embed_msg.set_image(url=image_url)
        await bot.send_message(ctx.message.channel, embed=embed_msg)
    else:
        await notifymsg(ctx.message.channel, "Sorry, an error has occured.", func_name, delete=True, useEmbed=True)
    

@raid.command(pass_context=True)
async def fafnir(ctx):
    await raid_message(ctx, 'Fafnir Time Slots', 'fafnir', 'fafnir()', 'https://sinoalice.wiki/images/c/cd/The_Flaming_Dragon_that_Haunts_the_Abyss.png')

@raid.command(pass_context=True)
async def fenrir(ctx):
    await raid_message(ctx, 'Fenrir Time Slots', 'fenrir', 'fenrir()', 'https://sinoalice.wiki/images/d/d7/The_Nightmare_that_Haunts_the_Hills.jpg')

@raid.command(pass_context=True)
async def ogre(ctx):
    await raid_message(ctx, 'Ogre Time Slots', 'ogre', 'ogre()', 'https://sinoalice.wiki/images/2/2f/The_Nightmare_that_Haunts_the_Forests.png')

@raid.command(pass_context=True)
async def spider(ctx):
    await raid_message(ctx, 'Spider Time Slots', 'spider', 'spider()', 'https://pbs.twimg.com/media/DK4d6BQUMAAjdEc.jpg')

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
@bot.group(pass_context=True, description='See emote options by invoking the help command', aliases=['e','emo'])
async def emote(ctx):
    """
    Use Emotes
    """
    if ctx.invoked_subcommand is None:
        await bot.say('**' + command_prefix + 'help emote** for options')

@emote.command(pass_context=True)
async def thanks(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/en/chatstamp001_es.png')

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
    await bot.send_file(ctx.message.channel, 'emotes/en/chatstamp009_es.png')

@emote.command(pass_context=True)
async def wants(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp010s.png')

@emote.command(pass_context=True)
async def rekt(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp011s.png')

@emote.command(pass_context=True, aliases=['otsukare'])
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

@emote.command(pass_context=True, aliases=['sorrymasen','sumanai'])
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

@emote.command(pass_context=True)
async def cheerup(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp031s.png')

@emote.command(pass_context=True)
async def helpme(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp032s.png')

@emote.command(pass_context=True)
async def congrats(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp033s.png')

@emote.command(pass_context=True)
async def goodluck(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp034s.png')

@emote.command(pass_context=True)
async def pout(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp035s.png')

@emote.command(pass_context=True)
async def creepyhello(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp036s.png')

@emote.command(pass_context=True)
async def byebye(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp037s.png')

@emote.command(pass_context=True)
async def approve(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp038s.png')

@emote.command(pass_context=True)
async def pleasehelp(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp039s.png')

@emote.command(pass_context=True)
async def brb(ctx):
    await bot.send_file(ctx.message.channel, 'emotes/ChatStamp040s.png')

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
