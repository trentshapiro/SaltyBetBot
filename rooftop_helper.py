import os
import sys
import json
import math
import discord
import random
import operator
from tabulate import tabulate
from datetime import datetime, timedelta
import reddit_helper

DEFAULT_INITIAL_MONEY = 1000
DEFAULT_TICK_MONEY = 5
MEME_COST = 100

admin_list = ["admin_id_2", "admin_id_1"]

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file)

def get_string_content(message, case):
    if case == 'lower':
        return message.content.lower()
    elif case == 'upper':
        return message.content.upper()
    else:
        return message.content

def read_json(path):
    with open(path) as f:
        return json.load(f)

async def get_emoji(message, emoji_name):
    for i in message.guild.emojis:
        print(i.name)
    return True

async def imster_egg(message):
    msg_contents = get_string_content(message, 'lower')

    if msg_contents == '>test':
        await get_emoji(message, 'test')
        return True

    #imster eg
    if msg_contents == 'grid can teleport twice':
        await message.channel.send('woah no way! grid can teleport twice?')
        return True
    elif msg_contents == '>true':
        await message.channel.send("True aaaaaaaaaaaand... Yeah, that's pretty true. That's true and- yeah that's true. That's true. That's true- That's pretty true. That's pretty true, I mean- inhales ... That's true. Yeah. That's true. Uhm- That's true. That's fuckin' true. Uhm... That's how it is dude.")
        await message.delete()
        return True
    elif msg_contents == '>twue':
        await message.channel.send("Twue aaaaaaaaaaaand... Yeah, that's pwetty twue. That's twue and- yeah that's twue. That's twue. That's twue- That's pwetty twue. That's pwetty twue, I mean- inhawes ... That's twue. Yeah. That's twue. Uhm- That's twue. That's fuckin' twue. Uhm... That's how it is dude.")
        await message.delete()
        return True
    return False

def generate_user_list(message):
    user_dict = {}
    for i in message.guild.members:
        if i.bot == False:
            record = {
                str(i.id):{
                    'name':i.name,
                    'discriminator':i.discriminator,
                    'nick':i.name if i.nick is None else i.nick,
                    'last_post_time':str(datetime.now() - timedelta(hours=2)),
                    'guesses':0,
                    'guesses_correct':0,
                }
            }
            user_dict.update(record)
    return user_dict


def update_user_list(message, bank):
    uprint('updating bank user list')
    user_list = generate_user_list(message)
    for i in user_list.keys():
        
        # add new users
        if i not in bank.keys():
            new_user = i
            new_user_record = user_list[i]
            new_user_record.update({
                'balance': DEFAULT_INITIAL_MONEY
            })
            bank.update({i:new_user_record})
        
        # update metadata of current users
        else:
            user_record = user_list[i]
            bank_record = bank[i]
            for meta in ['name', 'discriminator', 'nick']:
                if bank_record[meta] != user_record[meta]:
                    bank_record[meta] = user_record[meta]
            bank[i] = bank_record
    if 'default' in bank.keys():
        bank.pop('default', None)
    return bank


def write_bank_to_disk(bank, file_path):
    with open(file_path, 'w') as f:
        json.dump(bank, f)


async def verify_admin_user(message):
    this_user_id = message.author.id
    this_user_roles = message.author.roles

    if this_user_id in admin_list:
        return True
    else:
        for role in this_user_roles:
            if role.name == 'Mod':
                return True
    
    return False


async def is_banker(message):
    this_user_id = message.author.id
    this_user_roles = message.author.roles

    if this_user_id in admin_list:
        return True
    else:
        for role in this_user_roles:
            if role.name == 'Boof Distributor':
                return True
    
    return False


async def initialize_server(message):
    this_server = '_'.join(str(message.guild).split(' '))
    uprint(f'Generating bank for server: {this_server}')

    json_path = os.getcwd()+'\\data\\balances_'+this_server+'.json'
    uprint(f'Looking for json at path: {json_path}')

    if os.path.isfile(json_path):
        uprint('json found, updating user list')
        bank = read_json(json_path)
        bank = update_user_list(message, bank)
        write_bank_to_disk(bank, json_path)
    else:
        uprint('no json found, generating bank')
        bank = update_user_list(message, {'default': DEFAULT_INITIAL_MONEY})
        write_bank_to_disk(bank, json_path)
    
    uprint(f'server {this_server} initialized')
    return bank


async def hr_update(message, bank, hr_timer):
    uprint('executing hour update')
    current_time = datetime.now()
    last_update_time = hr_timer
    time_delta = (current_time - last_update_time).seconds
    time_delta_hours = math.floor(time_delta / 3600)
    payout = int(DEFAULT_TICK_MONEY * time_delta_hours)

    # divvy pity money
    for player in bank.keys():
        player_record = bank[player]
        player_balance = player_record['balance']

        new_player_balance = player_balance + payout
        player_record['balance'] = new_player_balance
        bank[player] = player_record
    
    #Update userlist
    bank = update_user_list(message, bank)
    
    # save bank to disk
    this_server = '_'.join(str(message.guild).split(' '))
    json_path = os.getcwd()+'\\data\\balances_'+this_server+'.json'
    write_bank_to_disk(bank, json_path)

    return bank


async def mi_update(message, bank):
    uprint('executing minute update')
    return True


async def place_bet(message, bank, purse):
    betting_player = str(message.author.id)

    msg_contents = get_string_content(message, case=None)
    msg_contents = msg_contents.split(' ')
    target_contestent = msg_contents[1]
    bet_amount = msg_contents[2]

    for i in ['<','>','!','@']:
        target_contestent = target_contestent.replace(i, '')
    
    
    target_contestent_name = bank[target_contestent]['nick']

    # validate bet integer
    try:
        bet_amount = int(bet_amount)
        if bet_amount < 1:
            raise ValueError('No Cheating.')
    except:
        await message.channel.send(f'{message.author.mention} Pick a normal number, dumbass.')
        return bank, purse
    
    # validate target player
    if target_contestent not in purse.keys():
        await message.channel.send(f'{message.author.mention} That user is not in the current bet, idiot.')
        return bank, purse
    
    # check if already bet
    contestents = sorted(purse.keys())
    already_placed_bet = False
    for contestent in contestents:
        bets = purse[contestent]
        if betting_player in bets:
            await message.channel.send(f'{message.author.mention} You have already placed your bet, eat shit.')
            return bank, purse

    # check player balance
    source_player_entry = bank[betting_player]
    source_player_balance = source_player_entry['balance']
    
    # empty account
    if source_player_balance == 0:
        await message.channel.send(f'{message.author.mention} You are too poor, sucks to suck.')
        return bank, purse
    
    # contestent betting for other player
    if betting_player in purse.keys() and betting_player != target_contestent:
        await message.channel.send(f'{message.author.mention} No match fixing, asshole.')
        return bank, purse

    # overdrawn
    if source_player_balance < bet_amount:
        await message.channel.send(f'{message.author.mention} You\'re a little light on <:latchcoin:849416995639918612>, but everything you do have will be bet.')
        bet_amount = source_player_balance
    
    # debit source account
    source_player_entry['balance'] = source_player_balance - bet_amount
    bank[betting_player] = source_player_entry

    # create entry in purse
    target_purse = purse[target_contestent]
    target_purse[betting_player] = bet_amount
    purse[target_contestent] = target_purse

    await message.channel.send(f'<:latchcoin:849416995639918612> {message.author.mention} has placed a bet for {bet_amount} for {target_contestent_name}. <:latchcoin:849416995639918612>')

    return bank, purse


async def check_balance(message, bank):
    player_id = str(message.author.id)

    player_balance = bank[player_id]['balance']

    message_out = f'{message.author.mention} your current balance is: {player_balance} <:latchcoin:849416995639918612>'
    await message.channel.send(content=message_out)

    return bank


async def command_factory_init(message, bank):
    msg_contents = get_string_content(message, 'lower')

    if msg_contents == '>leaderboard':
        bank = await show_leaderboard(message, bank)
        return bank
    elif msg_contents.startswith('>transfer'):
        bank = await transfer_amount(message, bank)
        return bank
    elif msg_contents.startswith('>balance'):
        bank = await check_balance(message, bank)
        return bank
    
    return bank


async def show_leaderboard(message, bank):
    format_length = 42
    leaderboard = [(bank[i]['nick'], bank[i]['balance']) for i in bank.keys()]
    leaderboard = sorted(leaderboard, key=lambda x: (-x[1], x[0]))
    leaderboard = leaderboard[:10]

    table = str(tabulate(leaderboard, ['Player','LatchCoins'], tablefmt="pretty"))

    await message.channel.send(content='<:latchcoin:849416995639918612> **CURRENT LEADERBOARD: <:latchcoin:849416995639918612>**\n```\n'+table+'```')
    await message.delete()
    return bank


async def print_leaderboard(message, bank):
    format_length = 42
    leaderboard = [(bank[i]['nick'], bank[i]['balance']) for i in bank.keys()]
    leaderboard = sorted(leaderboard, key=lambda x: (-x[1], x[0]))
    #leaderboard = leaderboard[:10]

    table = str(tabulate(leaderboard, ['Player','LatchCoins'], tablefmt="pretty"))

    now = datetime.now().strftime(r'%m%d%Y%H%M%S')
    file_name = now+'.txt'
    out_path = os.getcwd()+'\\data\\leaderboard_snapshots\\'+file_name
    with open(out_path, 'w', encoding='utf-8') as f:
        output_table = table
        f.write(output_table)

    return True


async def begin_salty_bet(message, bank):
    msg_contents = get_string_content(message, case=None)
    msg_contents.replace('>saltybet_start ', '')
    msg_contents = msg_contents.split('"')
    header = msg_contents[1]
    player_1 = msg_contents[2].split(' ')[1]
    player_2 = msg_contents[2].split(' ')[2]

    embed_obj = discord.Embed(
        title=header, 
        description="\n\n<:latchcoin:849416995639918612> **BETS ARE NOW OPEN.** <:latchcoin:849416995639918612>\nRespond with `.bet @PlayerName amount` to place your bet!\n\n",
        color=0x00ff00
    )
    
    # send live post
    #embed_obj.set_thumbnail(url='https://i.imgur.com/OiOkMoT.png')
    embed_obj.set_thumbnail(url='https://i.imgur.com/g3szWpv.png')
    embed_obj.add_field(name="PLAYER ONE", value=player_1, inline=False)
    embed_obj.add_field(name="PLAYER TWO", value=player_2, inline=False)
    await message.channel.send(embed=embed_obj)

    # setup purse
    for i in ['<','>','!','@']:
        player_1 = player_1.replace(i, '')
        player_2 = player_2.replace(i, '')
    
    purse = {
        player_1: {},
        player_2: {}
    }
    return purse


async def show_current_bets(message, bank, purse):
    contestents = sorted(purse.keys())
    contestent_1_id = contestents[0]
    contestent_1_name = bank[contestent_1_id]['nick']

    contestent_2_id = contestents[1]
    contestent_2_name = bank[contestent_2_id]['nick']

    # extract purse entries
    contestent_1_bets = purse[contestent_1_id]
    contestent_2_bets = purse[contestent_2_id]

    # contestent 1 bets
    if contestent_1_bets == {}:
        c_1_bets = [('No one :(', 0)]
        c_1_total = 0
    else:
        c_1_bets = [(bank[k]['nick'],v) for k,v in contestent_1_bets.items()]
        c_1_total = sum([x[1] for x in c_1_bets])
    
    # contestent 2 bets
    if contestent_2_bets == {}:
        c_2_bets = [('No one :(', 0)]
        c_2_total = 0
    else:
        c_2_bets = [(bank[k]['nick'],v) for k,v in contestent_2_bets.items()]
        c_2_total = sum([x[1] for x in c_2_bets])
    
    # sort bets
    c_1_bets = sorted(c_1_bets, key=lambda x: (-x[1], x[0]))[0:10]
    c_2_bets = sorted(c_2_bets, key=lambda x: (-x[1], x[0]))[0:10]
    
    # format table
    table_out = []
    for i in range(0,max([len(c_1_bets), len(c_2_bets)])):
        if i > len(c_1_bets)-1:
            c_1_tup = (None, None)
        else:
            c_1_tup = c_1_bets[i]
        if i > len(c_2_bets)-1:
            c_2_tup = (None, None)
        else:
            c_2_tup = c_2_bets[i]
        table_out.append((c_1_tup[0], c_1_tup[1], c_2_tup[0], c_2_tup[1]))
    
    
    title = [
        'P1: ' + contestent_1_name,
        'Total: ' + str(c_1_total),
        'P2: ' + contestent_2_name,
        'Total: ' + str(c_2_total)
    ]

    table = str(tabulate(table_out, title, tablefmt="pretty"))
    await message.channel.send(content='<:latchcoin:849416995639918612> **TOP BETTERS** <:latchcoin:849416995639918612>\n```\n'+table+'```')

    return table


async def end_salty_bet(message, bank, purse):
    msg_contents = get_string_content(message, case='lower')

    winning_player = msg_contents.split(' ')[1]
    for i in ['<','>','!','@']:
        winning_player = winning_player.replace(i, '')
    winning_player_nick = bank[winning_player]['nick']

    await message.channel.send(f'<:latchcoin:849416995639918612> **{winning_player_nick} HAS WON!** <:latchcoin:849416995639918612>')
    output_table = await show_current_bets(message, bank, purse)

    contestents = sorted(purse.keys())
    contestent_1_id = contestents[0]
    contestent_1_name = bank[contestent_1_id]['nick']

    contestent_2_id = contestents[1]
    contestent_2_name = bank[contestent_2_id]['nick']

    # extract purse entries
    contestent_1_bets = purse[contestent_1_id]
    contestent_2_bets = purse[contestent_2_id]

    # contestent 1 bets
    if contestent_1_bets == {}:
        c_1_bets = [('No one :(', 0)]
        c_1_total = 0
    else:
        c_1_bets = [(bank[k]['nick'],v) for k,v in contestent_1_bets.items()]
        c_1_total = sum([x[1] for x in c_1_bets])
    
    # contestent 2 bets
    if contestent_2_bets == {}:
        c_2_bets = [('No one :(', 0)]
        c_2_total = 0
    else:
        c_2_bets = [(bank[k]['nick'],v) for k,v in contestent_2_bets.items()]
        c_2_total = sum([x[1] for x in c_2_bets])
    
    grand_total = c_1_total + c_2_total
    if winning_player == contestent_1_id:
        winning_total = c_1_total
    elif winning_player == contestent_2_id:
        winning_total = c_2_total

    # credit gambler accounts
    winner_bets = purse[winning_player]
    if winner_bets.keys != {}:
        for win in winner_bets.keys():
            win_id = win
            bet_amount = winner_bets[win_id]
            payout = math.floor(grand_total * (bet_amount / winning_total))

            win_record = bank[win_id]
            win_balance = win_record['balance']
            new_win_balance = win_balance + payout
            win_record['balance'] = new_win_balance
            bank[win_id] = win_record

    # write out the final contest result
    now = datetime.now().strftime(r'%m%d%Y%H%M%S')
    file_name = now+'_'+contestent_1_id+'_'+contestent_2_id+'.txt'
    out_path = os.getcwd()+'\\data\\previous_bets\\'+file_name
    with open(out_path, 'w', encoding='utf-8') as f:
        output_table = f'WINNER: {winning_player_nick}\n'+output_table
        f.write(output_table)
    
    # save bank to disk
    this_server = '_'.join(str(message.guild).split(' '))
    json_path = os.getcwd()+'\\data\\balances_'+this_server+'.json'
    write_bank_to_disk(bank, json_path)

    return bank


async def transfer_amount(message, bank):
    source_player = str(message.author.id)
    msg_contents = get_string_content(message, case=None)
    msg_contents = msg_contents.split(' ')
    target_player = msg_contents[1]
    transfer_amount = msg_contents[2]

    for i in ['<','>','!','@']:
        target_player = target_player.replace(i, '')
    
    try:
        transfer_amount = int(transfer_amount)
        if transfer_amount < 1:
            raise ValueError('No Cheating.')
    except:
        await message.channel.send('Pick a normal number, dumbass.')
        return bank
    
    if target_player not in bank.keys():
        await message.channel.send('Target player could not be found, let CT know.')
        return bank
    elif target_player == source_player:
        await message.channel.send(f'{message.author.mention} Nice one! You\'re so funny!')
    else:
        # source_player entry
        source_player_entry = bank[source_player]
        source_player_balance = source_player_entry['balance']
        
        #empty accounts
        if source_player_balance == 0:
            await message.channel.send('You are too poor, sorry.')
            return bank
        
        #overdrawn
        if source_player_balance < transfer_amount:
            await message.channel.send('You\'re a little light on <:latchcoin:849416995639918612>, but everything you do have will be transfered.')
            transfer_amount = source_player_balance
        
        # debit source account
        source_player_entry['balance'] = source_player_balance - transfer_amount
        bank[source_player] = source_player_entry

        # credit target account
        target_player_entry = bank[target_player]
        target_player_entry['balance'] = target_player_entry['balance']+transfer_amount
        bank[target_player] = target_player_entry

        source_player_name = bank[source_player]['nick']
        target_player_name = bank[target_player]['nick']
        await message.channel.send(f'<:latchcoin:849416995639918612> Transfer of {transfer_amount} executed from {source_player_name} to {target_player_name} <:latchcoin:849416995639918612>')

    return bank


async def gift_user(message, bank):
    msg_contents = get_string_content(message, case=None)
    msg_contents = msg_contents.split(' ')
    target_player = msg_contents[1]
    gift_amount = msg_contents[2]

    for i in ['<','>','!','@']:
        target_player = target_player.replace(i, '')
    
    try:
        gift_amount = int(gift_amount)    
    except:
        await message.channel.send(f'{message.author.mention} Pick a normal number, dumbass.')
        return bank
    
    if target_player not in bank.keys():
        await message.channel.send(f'Target player could not be found, let imt know.')
        return bank
    else:
        player_entry = bank[target_player]
        player_entry['balance'] = max([player_entry['balance']+gift_amount, 0])
        bank[target_player] = player_entry
    
    nick = bank[target_player]['nick']
    await message.channel.send(f'<:latchcoin:849416995639918612> {nick} has been gifted {gift_amount} LatchCoins <:latchcoin:849416995639918612>')

    return bank


async def gift_multiple_users(message, bank):
    msg_contents = get_string_content(message, case=None)
    msg_contents = msg_contents.split(' ')
    
    gift_amount = int(msg_contents[1])
    user_list = msg_contents[2:]

    for gifted_user in user_list:

        for i in ['<','>','!','@']:
            gifted_user = gifted_user.replace(i, '')
    
        if len(gifted_user) > 10:
            if gifted_user not in bank.keys():
                await message.channel.send(f'Target player could not be found, let imt know.')
                return bank
            else:
                player_entry = bank[gifted_user]
                player_entry['balance'] = max([player_entry['balance']+gift_amount, 0])
                bank[gifted_user] = player_entry
        
            nick = bank[gifted_user]['nick']
            await message.channel.send(f'<:latchcoin:849416995639918612> {nick} has been gifted {gift_amount} <:latchcoin:849416995639918612>')

    return bank


async def magic_ball(message):
    responses = [
        "As I see it, yes.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don’t count on it.",
        "It is certain.",
        "It is decidedly so.",
        "Most likely.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Outlook good.",
        "Reply hazy, try again.",
        "Signs point to yes.",
        "Very doubtful.",
        "Without a doubt.",
        "Yes.",
        "Yes – definitely.",
        "You may rely on it."
    ]
    response = random.choice(responses)
    await message.channel.send(response)


async def get_meme(message, bank):
    source_player = str(message.author.id)

     # source_player entry
    source_player_entry = bank[source_player]
    source_player_balance = source_player_entry['balance']
    
    #empty accounts
    if source_player_balance == 0:
        await message.channel.send('You are too poor, sorry.')
        return bank
    
    #overdrawn
    if source_player_balance < MEME_COST:
        await message.channel.send(f'You\'re a little light on <:latchcoin:849416995639918612>, come back when you have {MEME_COST} LatchCoins.')
        return bank
    
    # debit source account
    source_player_entry['balance'] = source_player_balance - MEME_COST
    bank[source_player] = source_player_entry

    source_player_name = bank[source_player]['nick']
    random_post = await reddit_helper.retrieve_random_post()


    await message.channel.send(f'Thank you for your {MEME_COST} <:latchcoin:849416995639918612>, {source_player_name}. Here is your meme:\n{random_post}')

    return bank
