import os
import json
import discord
import importlib
import random
import rooftop_helper
from datetime import datetime, timedelta


# read creds
with open(os.getcwd()+'\\credentials\\config.json', 'r') as f:
    creds = json.load(f)

allowlist_channels = ['channel1','channel2', 'channel3']
allowlist_servers = ['server1', 'server2']

# start clock
bot_time = datetime.now()
mi_timer = datetime.now()
mi_threshold = 30
hr_timer = datetime.now()
hr_threshold = 1

# flags
is_initialized = False
contest_is_active = False
betting_is_open = False

# initialize other things
bank = {'default':None}
purse = {'default':None}

# create client
intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

HELP_STRING = '''
Mod Commands:
`>init_server`: initializes bot. if run a second time, reloads the last bank snapshot
`>save`: saves the current bank (doesn't need to be manually run, just for upgrades)
`>update_userlist`: updates everyone's nicknames in the bank
`>gift @player amount`: give a player some number of LatchCoin, can be + or -
`>saltybet_start "title" @player1 @player2`: starts a salty bet!
`>saltybet_close`: closes the betting for the current salty bet
`>saltybet_reopen`: reopens the betting fo the current salty bet
`>saltybet_end @winner`: ends the current salty bet, and pays out the victors!

Regular Commands:
`>balance`: check your current LatchCoin balance
`>leaderboard`: View the LatchCoin high scores
`>transfer @player amount`: Transfer LatchCoin to another player
`>bet @player amount`: During a salty bet, places a bet for a contestent! Be careful you only get one bet!
'''
  
# on log in event
@client.event
async def on_ready():
    rooftop_helper.uprint(f'Logged in as {client.user}')


# on message event
@client.event
async def on_message(message):
    global bot_time
    global mi_timer
    global hr_timer
    global is_initialized
    global contest_is_active
    global betting_is_open
    global bank
    global purse
    
    # skip our own messages
    if message.author == client.user or message.author.bot:
        rooftop_helper.uprint('bot user message, skipping.')
        return
    
    contents_lower = message.content.lower()

    # imster eg
    if contents_lower.startswith('>') or contents_lower.startswith('grid'):
        eg_found = await rooftop_helper.imster_egg(message)

    # limit channel for testing
    if str(message.channel) in allowlist_channels:

        # help
        if contents_lower == '>help':
            await message.channel.send(HELP_STRING)

        # server initialize
        if contents_lower == '>init_server':
            if await rooftop_helper.verify_admin_user(message):
                bank = await rooftop_helper.initialize_server(message)
                is_initialized = True
                bot_time = datetime.now()
                await message.delete()
        else:

            # user message update
            if is_initialized:

                # for dev only
                #if await rooftop_helper.verify_admin_user(message):
                rooftop_helper.uprint(contents_lower)

                # static user options post init
                implemented_functions = ['>leaderboard', '>transfer', '>balance']
                if any(i in contents_lower for i in implemented_functions):
                    bank = await rooftop_helper.command_factory_init(message, bank)

                # mod options
                if contents_lower.startswith('>save'):
                    if await rooftop_helper.verify_admin_user(message):
                        this_server = '_'.join(str(message.guild).split(' '))
                        json_path = os.getcwd()+'\\data\\balances_'+this_server+'.json'
                        rooftop_helper.write_bank_to_disk(bank, json_path)
                        await message.channel.send('Bank saved successfully.')
                        await message.delete()
                elif contents_lower.startswith('>update_userlist'):
                    if await rooftop_helper.verify_admin_user(message):
                        bank = rooftop_helper.update_user_list(message, bank)
                        await message.channel.send('Userlist updated sucessfully.')
                        await message.delete()
                elif contents_lower.startswith('>snapshot_leaderboard'):
                    if await rooftop_helper.verify_admin_user(message):
                        await rooftop_helper.print_leaderboard(message, bank)
                        await message.channel.send('Leaderboard snapshot saved.')
                        await message.delete()
                elif contents_lower.startswith('>saltybet_start'):
                    # start a bet
                    if await rooftop_helper.verify_admin_user(message):
                        if contest_is_active:
                            await message.channel.send('A contest is currently underway, please end it with `.saltybet_end @PlayerName`')
                        else:
                            purse = await rooftop_helper.begin_salty_bet(message, bank)
                            contest_is_active = True
                            betting_is_open = True
                        await message.delete()

                elif contents_lower.startswith('>saltybet_close'):
                    # close betting
                    if await rooftop_helper.verify_admin_user(message):
                        if contest_is_active and betting_is_open:
                            await message.channel.send(':Latchcoin: **BETTING IS CLOSED!** :Latchcoin:')
                            await rooftop_helper.show_current_bets(message, bank, purse)
                            betting_is_open = False
                        elif contest_is_active:
                            await message.channel.send('Betting has already been closed, use `.saltybet_reopen` to reopen betting')
                        else:
                            await message.channel.send('There is not currently a contest underway, please start one with `.saltybet_start`')
                        await message.delete()

                elif contents_lower.startswith('>saltybet_reopen'):
                    # reopen betting
                    if await rooftop_helper.verify_admin_user(message):
                        if contest_is_active and betting_is_open:
                            await message.channel.send('Betting is already open, you can end betting with `.saltybet_close`, or end the contest with `saltybet_end @PlayerName`')
                        elif contest_is_active:
                            await message.channel.send(':Latchcoin: **BETTING IS REOPENED! :Latchcoin:**')
                            betting_is_open = True
                        else:
                            await message.channel.send('There is not currently a contest underway, please start one with `.saltybet_start`')
                        await message.delete()

                elif contents_lower.startswith('>saltybet_end'):
                    try:
                        target_player = contents_lower.split(' ')[1]
                    except:
                        target_player = ''
                    for i in ['<','>','!','@']:
                        target_player = target_player.replace(i, '')
                    # end a contest
                    if await rooftop_helper.verify_admin_user(message):
                        if contest_is_active and target_player not in purse.keys():
                            await message.channel.send('That user is not in the current bet, please select a winner.')
                        elif contest_is_active:
                            await message.channel.send(':Latchcoin: **THE SALTY BET HAS ENDED! PRIZES HAVE BEEN DISTRIBUTED.** :Latchcoin:')
                            bank = await rooftop_helper.end_salty_bet(message, bank, purse)
                            contest_is_active = False
                            betting_is_open = False

                            purse = {}
                        else:
                            await message.channel.send('There is not currently a contest underway, please start one with `.saltybet_start`')
                        await message.delete()

                elif contents_lower.startswith('>gift'):
                    # gift coins to users 
                    if await rooftop_helper.verify_admin_user(message):
                        bank = await rooftop_helper.gift_user(message, bank)
                    elif await rooftop_helper.is_banker(message):
                        bank = await rooftop_helper.gift_user(message, bank)
                elif contents_lower.startswith('>massgift'):
                    # gift coins to multiple users 
                    if await rooftop_helper.verify_admin_user(message):
                        bank = await rooftop_helper.gift_multiple_users(message, bank)
                    elif await rooftop_helper.is_banker(message):
                        bank = await rooftop_helper.gift_multiple_users(message, bank)
                
                # generic user options during contests
                elif contents_lower.startswith('>bet'):
                    if contest_is_active and betting_is_open:
                        bank, purse = await rooftop_helper.place_bet(message, bank, purse)
                    else:
                        await message.channel.send(f'{message.author.mention} Cool your jets, Jack, betting is closed.')
                #elif contents_lower.startswith('>meme'):
                    #bank = await rooftop_helper.get_meme(message, bank)

                user_record = bank[str(message.author.id)]
                user_record['last_post_time'] = str(datetime.now())
                bank[str(message.author.id)] = user_record
    
    #global message ok
    if contents_lower.startswith('>8ball'):
        await rooftop_helper.magic_ball(message)
        
    # tick updates
    if datetime.now() - hr_timer > timedelta(hours=hr_threshold):
        bank = await rooftop_helper.hr_update(message, bank, hr_timer)
        hr_timer = datetime.now()

    if datetime.now() - mi_timer > timedelta(minutes=mi_threshold):
        await rooftop_helper.mi_update(message, bank)
        mi_timer = datetime.now()
    
    importlib.reload(rooftop_helper)

client.run(creds['bot_token'])
