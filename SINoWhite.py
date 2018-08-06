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
from urllib import parse
import psycopg2

##############
# Cogs
import Danbooru
cogs = ["Danbooru"]

##############
#Bot Config filepath
config_filepath = 'config.json'

##############
#Vars
token = os.environ['SINOALICE_TOKEN'] #Token is taken from computer's env for security
command_prefix = ''
description = 'SINoWhite bot for TeaParty'
trackedEvents = {}
locked_roles = []
colo_cached_names = {}
active_raids = {}
raid_info = {}
emoji_aliases={}
base_emoji_map={}
emoji_map={}
tracker = None
##############

##############
# DailyTasks
##############
daily_tasks = {}

##############
#Channels
##############
#TeaParty Channels
bot_test_channel = ''
lobby_channel = ''
##############

##############
#SQL vars
database_url = os.environ['DATABASE_URL'] #URL is taken from computer's env for security
##############

#########################################################################################
#Boot up procedures for bot (Before login)

def load_config():
    config = None
    with open(config_filepath, 'r') as f:
        #All the configurations that are being managed
        global command_prefix
        global bot_test_channel
        global lobby_channel
        global trackedEvents
        global locked_roles
        global active_raids
        global raid_info
        global emoji_aliases
        global base_emoji_map
        global emoji_map
        
        config = json.load(f)
        print ('------')
        print ('Loading config file...')
        
        command_prefix = config['command_prefix']
        print ('command_prefix:', command_prefix)
        
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
            print ('WARNING: trackedEvents field missing from config!')


        if 'locked_roles' in config:
            locked_roles = config['locked_roles']
            print ('locked_roles: ' + ', '.join('{}'.format(role) for role in locked_roles))
        else:
            print ('WARNING: No locked_roles set')

        if 'active_raids' in config:
            active_raids = config['active_raids']
            print ('active_raids: ' + ', '.join('{}'.format(raid) for raid in active_raids.keys()))
        else:
            print ('INFO: No active_raids')

        if 'raid_info' in config:
            raid_info = config['raid_info']
            print ('raid_info: ' + ', '.join('{}'.format(raid) for raid in raid_info.keys()))
        else:
            print ("WARNING: No raid_info available")

        if 'emoji' in config:
            base_emoji_map = config['emoji']
            emoji_map = base_emoji_map.copy()
        if 'emoji_alias' in config:
            emoji_aliases = config['emoji_alias']
            for emoji, aliases in emoji_aliases.items():
                for alias in aliases:
                    emoji_map[alias] = emoji_map[emoji]

        print ('emoji_map: ' + ', '.join('{}'.format(emoji_key) for emoji_key in emoji_map.keys()))

def load_cogs():
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

def load_tracker():
    print('Seting up Tracker...')
    global tracker
    tracker = et.EventTracker()
    for eventName, eventTimeLst in trackedEvents.items():
        tracker.addEvent(eventName, eventTimeLst);
    print('Tracker ready')
    print('------')

load_config()
bot = commands.Bot(command_prefix=command_prefix, description=description)
load_cogs()
load_tracker()

#########################################################################################
#Dev-only commands (hidden)

def getDump():
    return json.dumps({'command_prefix':command_prefix,
                       'bot_test_channel':bot_test_channel,
                       'lobby_channel':lobby_channel,
                       'trackedEvents':trackedEvents,
                       'locked_roles':locked_roles,
                       'active_raids':active_raids,
                       'raid_info':raid_info,
                       'emoji':base_emoji_map,
                       'emoji_alias':emoji_aliases}, sort_keys=True, indent=4, cls=tu.TodEncoder)

async def updateConf():
    dump = getDump()
    
    with open(config_filepath, 'w') as f:
        f.write(dump)
        f.close()

    time_stamp = tu.time_now()
    print (time_stamp + " DEV Config Changed\nDump:", dump)

async def doBackup():
    
    dump = getDump()
    
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
    # Resets everyone's attendance, assume not indicated

    conn = getDatabaseConn(database_url)
    cur = conn.cursor()
    cur.execute('UPDATE public.colo_status SET status = 0')
    conn.commit()
    cur.close()
    conn.close()

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

@bot.command(description='Modify raid_info', hidden=True)
async def __raid_info(raidname, name, raidtype, img_url):
    raid_obj = {}
    raid_obj['name'] = name
    raid_obj['type'] = raidtype
    raid_obj['img_url'] = img_url
    
    global raid_info
    raid_info[raidname] = raid_obj

    #Save to file
    await updateConf()
    await bot.say("Conf Updated")

@bot.command(description='Add to active_raid and trigger', hidden=True)
async def __raid_add(name, displayname, time_set):
    if tracker.hasEvent(time_set):
        eventTimes = tracker.getEvent(time_set)

        raid_tasks = []
        for eventTime in eventTimes:
            task = dt.DailyTask(raidmsg, displayname+" Raid @ "+eventTime.toJST(), eventTime, raidname=displayname)
            await task.start()
            raid_tasks.append(task)
                
            daily_tasks[name] = raid_tasks

        await bot.say("Raid " + name + " Scheduled for " + time_set)
    else:
        print (tu.time_now() + " ERROR Unable to schedule " + name + " as " + time_set + " is missing from tracker")
        await bot.say("ERROR Unable to schedule " + name + " as " + time_set + " is missing from tracker")

    new_active_raid = {}
    new_active_raid["name"] = displayname
    new_active_raid["type"] = time_set
    active_raids[name] = new_active_raid
    
    
    #Save to file
    await updateConf()
    await bot.say("Conf Updated")

@bot.command(description='Remove from active_raid and terminate', hidden=True)
async def __raid_remove(name):
    if name in daily_tasks:
        print (tu.time_now() + " DEV Awaiting all DailyTask of " + name + " to stop")
        await bot.say("Awaiting all DailyTask of " + name + " to stop")
        
        tasks_to_kill = daily_tasks[name]
        for eaTask in tasks_to_kill:
            try:
                await eaTask.stop()
            except:
                pass
        
        del daily_tasks[name]

    else:
        print (tu.time_now() + " ERROR Unable to remove schedule of " + name + " as it does not exist")
        await bot.say(" ERROR Unable to remove schedule of " + name + " as it does not exist")

    if name in active_raids:
        del active_raids[name]
        
        #Save to file
        await updateConf()
        await bot.say("Conf Updated")
    else:
        print (tu.time_now() + " WARNING " + name + " not in active_raid")
        await bot.say("WARNING " + name + " not in active_raid")
    

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

            #Extra exception catching for situations like message already not existing (manual delete by something else)
            try:
                await bot.delete_message(sent_msg)
                delete_time_stamp = tu.time_now()
                print (delete_time_stamp + " INFO Message sent to channel " + channel.name + " with id " + sent_msg.id + " deleted")
            except discord.Forbidden:
                print (delete_time_stamp + " ERROR Unable to delete message with id " + sent_msg.id + " as bot does not have proper permissions")
            except discord.HTTPException as e:
                print (delete_time_stamp + " WARNING Unable to delete message with id " + sent_msg.id + "\nDetails: " + e.text)
            sent_msg = None

async def dailyexpmsg():
    await notifymsg(lobby_channel, 'Daily EXP dungeons are up!', 'DAILY_EXP_TASK')

async def dailyexptask():
    if tracker.hasEvent('exp'):
        for eventTime in tracker.getEvent('exp'):
            task = dt.DailyTask(dailyexpmsg, "DAILY_EXP_TASK @ "+eventTime.toJST(), eventTime)
            await task.start()

    else:
        print (tu.time_now() + " ERROR Unable to schedule DAILY_EXP_TASK as exp is missing from tracker")

async def raidmsg(*args, **kwargs):
    raidname = ''
    raidlogmsg = '_MISSING_ARGUEMENT_'
    print ("arg[0]:", args[0])
    print ("kwords:", args[1]) # To remove later, DEBUG only
    kwords = args[1] #args and kwargs are stored as a pair for some reason, so args[1] contains the kwargs
    if 'raidname' in kwords:
        raidname = kwords['raidname']
    if 'raidlogmsg' in kwords:
        raidlogmsg = kwords['raidlogmsg']+'_RAID_MSG'
        
    await notifymsg(lobby_channel, raidname + ' Raid is up!', raidlogmsg)

async def completedailymsg():
    await notifymsg(lobby_channel, 'Remember to claim your daily cleaning ticket!', 'completedailymsg()', delete=False, useEmbed=True)
    await reset_participation()
    
async def completedailytask():
    task = dt.DailyTask(completedailymsg, "COMPLETE_DAILY_TASK @ 23:40 JST", tu.TimeOfDay(14, 40))
    await task.start()

async def schedule_raids():
    print ("Scheduling raids...")
    for name, details in active_raids.items():
        if tracker.hasEvent(details["type"]):
            eventTimes = tracker.getEvent(details["type"])

            raid_tasks = []
            for eventTime in eventTimes:
                task = dt.DailyTask(raidmsg, details["name"]+" Raid @ "+eventTime.toJST(), eventTime, raidname=details["name"], raidlogmsg=name.replace(" ","_").upper())
                await task.start()
                raid_tasks.append(task)
                
            daily_tasks[name] = raid_tasks
        else:
            print (tu.time_now() + " ERROR Unable to schedule " + name + " as " + time_set + " is missing from tracker")

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
    role = await findRoleInServer(ctx, ' '.join(role_name))

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

            conn = getDatabaseConn(database_url)
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM public.colo_status WHERE userid = %s', (member.id,))
            result = cur.fetchone()
            if result[0] > 0:
                #Existing entry
                cur.execute('UPDATE public.colo_status SET status = %s WHERE userid = %s', (1, member.id))
            else:
                #Create new entry
                cur.execute('INSERT INTO public.colo_status (status, userid) VALUES (%s, %s)', (1, member.id))

            conn.commit()
            cur.close()
            conn.close()
            
            await bot.say(alias + " is joining us for colo today")
            
            time_stamp = tu.time_now()
            print (time_stamp + " INFO User " + alias + " colo_join = True")
            return

    await bot.say('An unknown error has occured.')

@bot.command(pass_context=True, aliases=['cmi'])
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
                
            conn = getDatabaseConn(database_url)
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM public.colo_status WHERE userid = %s', (member.id,))
            result = cur.fetchone()
            if result[0] > 0:
                #Existing entry
                cur.execute('UPDATE public.colo_status SET status = %s WHERE userid = %s', (-1, member.id))
            else:
                #Create new entry
                cur.execute('INSERT INTO public.colo_status (status, userid) VALUES (%s, %s)', (-1, member.id))

            conn.commit()
            cur.close()
            conn.close()
            
            await bot.say(alias + " is **not** joining us for colo today")
            
            time_stamp = tu.time_now()
            print (time_stamp + " INFO User " + alias + " colo_join = False")
            return

    await bot.say('An unknown error has occured.')

async def getAlias(userid):
    time_stamp = tu.time_now()
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

    return alias

@bot.command(pass_context=True)
async def colo(ctx):
    participants = []
    nonParticipants = []
    notIndicated = []

    #test
    conn = getDatabaseConn(database_url)
    cur = conn.cursor()
    
    cur.execute('SELECT userid FROM public.colo_status WHERE status > 0')
    result = cur.fetchall()
    for userid in result:
        alias = await getAlias(userid[0])
        participants.append(alias)
        
    cur.execute('SELECT userid FROM public.colo_status WHERE status < 0')
    result = cur.fetchall()
    for userid in result:
        alias = await getAlias(userid[0])
        nonParticipants.append(alias)

    cur.execute('SELECT userid FROM public.colo_status WHERE status = 0')
    result = cur.fetchall()
    for userid in result:
        alias = await getAlias(userid[0])
        notIndicated.append(alias)
        
    cur.close()
    conn.close()

    await bot.say("Participating: " + str(len(participants)) + '\n\t' + ", ".join(participants) +'\n\n' +\
                  "Not Participating: " + str(len(nonParticipants)) + '\n\t' + ", ".join(nonParticipants) +'\n\n' +\
                  "No Indication: " + str(len(notIndicated)) + '\n\t' + ", ".join(notIndicated))
    return

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

@bot.group(pass_context=True, description='Shows details about a particular raid')
async def raid(ctx, raidname="current"):
    """
    Check Raid timings
    """
    if raidname in raid_info:
        raid = raid_info[raidname]
        await raid_message(ctx, raid['name']+' Time Slots', raid['type'], "raid("+raidname+")", raid['img_url'])
    elif raidname is "current":
        for eaRaid in active_raids.keys():
            raid = raid_info[eaRaid]
            await raid_message(ctx, raid['name']+' Time Slots', raid['type'], "raid("+raidname+")", raid['img_url'])
    else:
        await bot.say("Available options: " + ', '.join('{}'.format(key) for key in raid_info.keys()))
    

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
        await notifymsg(ctx.message.channel.id, "Sorry, an error has occured.", func_name, delete=True, useEmbed=True)

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
async def emote(ctx, emoji : str):
    """
    Use Emotes
    """
    if emoji in emoji_map.keys():
        await bot.send_file(ctx.message.channel, emoji_map[emoji])
    else:
        await bot.say("Emoji List:"+ ', '.join('{}'.format(emoji_key) for emoji_key in sorted(emoji_map.keys())))
    
#########################################################################################
#Database helper function
def getDatabaseConn(database_url):
    parse.uses_netloc.append("postgres")
    url = parse.urlparse(database_url)

    conn = psycopg2.connect(
        database=url.path[1:],
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port
    )
    return conn

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
        await dailyexptask()
        await completedailytask()
        #await raidtask("crystalwispmsg", crystalwispmsg)
        #await raidtask("Crystal Wisp", raidmsg, raidname="Crystal Wisp")
        await schedule_raids()

        #Inactive
        #None
        
        print('All Scheduled Notifications Queued')

        print('------')
        
        firstBoot = False

@bot.event
async def on_error(event, *args, **kwargs):
    print(tu.time_now() + " Error " + event)
    
#This is a modified copy of bot.run from discord's default
noKbInterrupt=True
def runbot(bot, *args, **kwargs):
    try:
        bot.loop.run_until_complete(bot.start(*args, **kwargs))
    except KeyboardInterrupt:
        print (tu.time_now() + " ERROR KeyboardInterrupt Exception")
        global noKbInterrupt
        noKbInterrupt=False
    except Exception as e:
        print (tu.time_now() + "ERROR Generic Exception of type " + e.__class__.__name__)
    finally:
        bot.loop.run_until_complete(bot.logout())
        pending = asyncio.Task.all_tasks(loop=bot.loop)
        gathered = asyncio.gather(*pending, loop=bot.loop)
        try:
            gathered.cancel()
            bot.loop.run_until_complete(gathered)

            # we want to retrieve any exceptions to make sure that
            # they don't nag us about it being un-retrieved.
            gathered.exception()
        except:
            pass
        finally:
            bot.loop.close()

#########################################################################################
#Actual Execution of Bot

while noKbInterrupt:
    runbot(bot, token)
    

#bot.run(token)
print (tu.time_now() + " INFO Bot Exit")
