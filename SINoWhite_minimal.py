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
#Bot Config filepath
config_filepath = 'config.json'

##############
#Vars
token = os.environ['SINOALICE_TOKEN'] 	# Token is taken from computer's env for security
command_prefix = '' 			# Prefix for commands
description = 'SINoWhite Bot' 		# The bot description shown when invoking the help command
trackedEvents = {}			# A list of event types that are tracked. each entity defines a set of start time
locked_roles = []			# List of locked roles that the bot should not be able to assign role to
colo_cached_names = {}			# A cache for colo names, as searching up user names is slow
active_raids = {}			# Stores a list of active raids
raid_info = {}				# Contains raid information such as name, time slots etc.
emoji_aliases={}			# Aliases for all the emojis that can be invoked by the emoji command
base_emoji_map={}			# Stores the basic set of emoji mappings to their image files (aliases not included)
emoji_map={}				# Stores mapping just like base_emoji_map but includes aliases
notify_list_exp=[]			# Stores a list of channels to notify for exp messages
notify_list_raid=[]			# Stores a list of channels to notify for raid messages
notify_list_daily_mission=[]		# Stores a list of channels to notify for daily missions
tracker = None				# Event tracker. Starts uninitialized until bot has fully run up. See LoadTracker()
enable_debug = False			# flag to enable/disable certain messages from showing up in log
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
wolfie_channel = ''
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
        global wolfie_channel
        global trackedEvents
        global locked_roles
        global active_raids
        global raid_info
        global emoji_aliases
        global base_emoji_map
        global emoji_map
        global notify_list_exp
        global notify_list_raid
        global notify_list_daily_mission
        global enable_debug
        
        config = json.load(f)
        print ('------')
        print ('Loading config file...')
        
        command_prefix = config['command_prefix']
        print ('command_prefix:', command_prefix)
        
        bot_test_channel = config['bot_test_channel']
        print ('bot_test_channel:', bot_test_channel)

        lobby_channel = config['lobby_channel']
        print ('lobby_channel:', lobby_channel)

        wolfie_channel = config['wolfie_channel']
        print ('wolfie_channel:', wolfie_channel)
        
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

        if 'notify_list_exp' in config:
            notify_list_exp = config['notify_list_exp']
            print ('notify_list_exp: ' + ', '.join('{}'.format(channel_id) for channel_id in notify_list_exp))
        else:
            print ('INFO: No notify_list_exp in config.')
            print ('WARNING: No messages will be sent for exp messages.')

        if 'notify_list_raid' in config:
            notify_list_raid = config['notify_list_raid']
            print ('notify_list_raid: ' + ', '.join('{}'.format(channel_id) for channel_id in notify_list_raid))
        else:
            print ('INFO: No notify_list_raid in config.')
            print ('WARNING: No messages will be sent for raid messages.')

        if 'notify_list_daily_mission' in config:
            notify_list_daily_mission = config['notify_list_daily_mission']
            print ('notify_list_daily_mission: ' + ', '.join('{}'.format(channel_id) for channel_id in notify_list_daily_mission))
        else:
            print ('INFO: No notify_list_daily_mission in config.')
            print ('WARNING: No messages will be sent for daily mission messages.')

        if 'enable_debug' in config:
            enable_debug = config['enable_debug']
        if enable_debug is True:
            print ('INFO: DEBUG messages are turned ON')
        else:
            print ('INFO: DEBUG messages are turned OFF')

def load_tracker():
    print('Seting up Tracker...')
    global tracker
    tracker = et.EventTracker()
    for eventName, eventTimeLst in trackedEvents.items():
        tracker.addEvent(eventName, eventTimeLst);
    print('Tracker ready')
    print('------')

#load_config()
bot = commands.Bot(command_prefix=command_prefix, description=description)
load_tracker()

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
        #await dailyexptask()
        #await completedailytask()
        #await raidtask("crystalwispmsg", crystalwispmsg)
        #await raidtask("Crystal Wisp", raidmsg, raidname="Crystal Wisp")
        #await schedule_raids()

        #Inactive
        #None
        
        print('All Scheduled Notifications Queued')

        print('------')
        
        firstBoot = False
    else:
        print('Reconnected to discord at ' + tu.time_now())
    
    print ('Connected to the following servers:')
    for server in bot.servers:
       print (server.owner.name + '('+server.owner.id+')', server.name + '('+server.id+')', server.region)
       
       if server.id == "599433741001293945":
           for role in server.roles:
               if role.id == "603603793472651274":
                   await notifymsg("603766502100959252", role.mention + " embed cannot mention role maybe", "Test", useEmbed=False)


    #sent_msg =  await bot.say('Using backup for next bootup')
    #Delete msg after 5min
    #await asyncio.sleep(300)
    #await bot.delete_message(sent_msg)

    #server 599433741001293945
    #role 603603793472651274
    #await notifymsg("603766502100959252", 'SINoWhite is best waifu.', 'Test')


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
