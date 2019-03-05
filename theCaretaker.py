#! python3
#
#  theCaretaker.py - Discord bot for The Final Frontier
import random
#import time
import asyncio
import discord
import re

from discord import Game
from discord.ext.commands import Bot

with open('token.txt') as f:
    TOKEN = f.read().strip()
BOT_PREFIX = (';', '!')
PERSONALITIES = ['Caretaker', 'Avatus']
ACTIVE_PERSONALITY = PERSONALITIES[0]
client = Bot(command_prefix=BOT_PREFIX)
ENGAGED_COMMANDERS = {}
#client.remove_command('help')

class ActiveListener:

    def __init__(self, client):
        self.client = client
        self.commands = []
        self.helplist = []
        self.ohelplist = []

    def add_command(self, command):
        self.commands.append(command)
        if (command['officer only'] == False and 
            command['hide from help'] == False):
            self.helplist.append(command)
        if command['officer only'] == True:
            self.ohelplist.append(command)

    async def command_handler(self, message_dict):
        global ENGAGED_COMMANDERS
        message_dict = find_command(self.commands, message_dict)
        if message_dict['orders'] == None:
            return
        
        message_dict = message_breakdown(message_dict)
        message_dict = clean_argumaker(message_dict)
        write_log(message_dict)
        invocation = message_dict['invocation']
        command = list(filter(lambda c: c['trigger'] == invocation or invocation in c['aliases'], self.commands))[0]
        await command['function'](
            message_dict['message'], self.client, message_dict['args'])

    
active_ear = ActiveListener(client)

def get_handle(member):
    if hasattr(member, 'nick'):
        return member.nick
    return member.name

def is_invocation(message):
    attention_grabbers = [('hey ' + ACTIVE_PERSONALITY.lower()), ('yo ' + 
        ACTIVE_PERSONALITY.lower()), 'listen up, motherfucker', 'front!']
    attention_re = re.compile("|".join(attention_grabbers))
    if attention_re.search(message.content.lower()):
        invocation_str = message.content.lower()
        basic_grabber = attention_grabbers[0]
        for grabber in attention_grabbers:
            invocation_str = invocation_str.replace(grabber, basic_grabber)
        return (True, invocation_str)
    return (False, message.content)
 
def find_command(command_dict_list, message_dict):
    command_list = []
    alias_dict = {}
    for command in command_dict_list:
        command_list.append(command['trigger'])
        for entry in command['aliases']:
            command_list.append(entry)
            alias_dict[entry] = command['trigger']
    command_re = re.compile("|".join(command_list))
    re_search = command_re.search(message_dict['message'].content.lower())
    if re_search:
        message_dict['orders'] = (
            message_dict['message'].content.lower()[re_search.start():])
        for alias in alias_dict.keys():
            if alias in message_dict['orders']:
                message_dict['orders'].replace(alias, alias_dict[alias])
                message_dict['invocation'] = alias_dict[alias]
            if 'invocation' not in message_dict:
                message_dict['invocation'] = re_search.group()
        
    else:
        message_dict['orders'] = None
    return message_dict
 
def message_breakdown(message_dict):
    message_str = message_dict['message'].content.lower()
    message_str.replace(', ', ' ')
    message_str.replace('. ', ' ')
    message_str.replace('; ', ' ')
    message_str.replace('! ', ' ')
    message_str.replace('? ', ' ')
    message_dict['args'] = re.split(' +', message_str)
    return message_dict

def clean_argumaker(message_dict):

    if ACTIVE_PERSONALITY.lower() in message_dict['args']:
        message_dict['args'].remove(ACTIVE_PERSONALITY.lower())
    if 'hey' in message_dict['args']:
        message_dict['args'].remove('hey')
    return message_dict
    
def write_log(message_dict):
    with open('./invokers.txt', 'a') as log:
        auth_name = str(message_dict['message'].author.name)
        auth_discr = str(message_dict['message'].author.discriminator)
        log_message = ('I heard a command!  ' + auth_name + '#' + auth_discr +
        ' told me to ' + message_dict['orders'] + ' by saying, "' + 
        str(message_dict['message'].content) + '".\n')
        log.write(log_message)
    return

async def tell_function(message, client, args):
    target = args[args.index('tell')+1]
    target_channel = target_get(message, target)
    args.pop(args.index('tell'))
    args.pop(args.index(target))
    send_message = []
    
    if 'about' not in args:
        send_message = ('I\'m quite sure I don\'t understand you, ' +
                        message.author.mention +'.  It\'s easy to forget ' +
                        'that I need you to ask me to tell <recipient> ' +
                        'about <whatever you want to hear about>.')
        target_channel = message.channel
        
    else:
        args.pop(args.index('about'))
        
    if type(target_channel) == type([]):
        send_message = send_message + target_channel
        target_channel = message.channel

    if send_message == []:
        send_message = await compose_cheer(message, args)

    for line in send_message:
        if line == '':
            await asyncio.sleep(3)
        elif line != None:
            await client.send_typing(target_channel)
            await asyncio.sleep(3)
            await client.send_message(target_channel, line)
            
    if args[0].lower() in 'bloodrose' and 'blood' in send_message[0].lower():
        await client.send_typing(message.channel)
        humiliation = ('Please don\'t put me through that again.  It\'s ' +
                        'humiliating, ' + message.author.mention)
        await client.send_message(message.channel, humiliation)
        
    return

def target_get(message, target):
    valid_targets = {'me': message.author, 'us': message.channel}
    target_channel = [('I\'m sorry, I\'m not sure how to tell ' +
                    str(target) + ' apart from any other sophont here.  ' +
                    'I\'m afraid you just all look so similar, ' +
                    'and you\'re here and gone in a flash.'), '',
                    ('Was that offensive?  I\'m never quite sure when ' +
                    'it comes to organics...')]
    
    for member in message.server.members:
        if member.nick:
            valid_targets[str(member.nick).lower()] = member
        else:
            valid_targets[str(member.name)] = member

    if target == 'me':
        target_channel = valid_targets['me']
        return target_channel
    
    elif target == 'us':
        target_channel = valid_targets['us']
    
    elif target != 'us' and len(target) > 2:
        for key in valid_targets:
            if target.lower() in str(key.encode('UTF-8')).lower():
                target_channel = valid_targets[key]
                return target_channel
            
    elif target != 'us' and len(target) < 3:
        target_channel = [('I\'m sorry, I can\'t find anyone with that ' +
                        'little information.  Could you try again, with ' +
                        'more of their name?')]
        
    else: target_channel = ['Something has gone terribly wrong.']
                    
    return target_channel

async def compose_cheer(message, args):
    cheer = []
    if args[0].lower() == 'doll':
        possible_responses = [
            '<This message redacted by Americans for a Cleaner Internet.>',
            '<This message redacted by the Federal Bureau of What The Hell.>',
            '<This message redacted by the Mormon Tabernacle Conspiracy.>',
            ('<This message redacted by personal degree of his Holiness, God' +
            ' Emperor Leto II.>'),
            ('<This message redacted by me.  Why?  Why am I forced to share ' +
            'a server with such a *perverse* sapient?>'),
            ('<This message redacted by something less censorable, shoved ' + 
            'into Doll\'s talky-hole.>'),
            '<This message redacted by the fascists.>',
            '<This message redacted by the imperialists.>',
            '<This message redacted by the colonists.>',
            '<This message redacted by the anticolonists.>',
            '<This redaction redacted by the Department of Redundancy ' + 
            'Department.>',
            '<This message redacted by the Starship Troopers.>',
            ('<This message declared blasphemy by the God-Emperor of ' + 
            'Mankind, as likely to lead to Slaaneshi worship.>')
        ]
        cheer = [random.choice(possible_responses)]

    if args[0].lower() == 'blood':
        leader_speech_1 = ('Local space, as well as the universe at large, ' +
                           'belongs to Dread Mistress Verana Bloodrose, Our ' +
                           'Lady of Fluids and Flowers, Savior of Patio ' +
                           'Furniture, first of her name.')
        
        leader_speech_2 = ('They make me say that, you know.')
        
        cheer.extend((leader_speech_1, leader_speech_2))

    if args[0].lower() == 'arrok':
        cheer.append('WAAAAAAAAAAAAAAAAAAAGH')

    return cheer

async def hello_function(message, client, args):
    try:
        first_greet = ('Greetings, ' +
                       message.author.mention +
                       '. I am the Caretaker, a powerful virtual construct ' +
                       'created by the Eldan long ago to monitor all '+ 
                       'scientific experiments on the planet Nexus AND ' + 
                       'ABANDONED THERE FOR EONS!')

        second_greet = ('\nI was transferred and... adapted... by some ' + 
                        'friendly WALKING ORGAN SACKS to serve as the ' +
                        'monitor for this Discord server.')

        third_greet = ('\nWhile my migration has incurred some small... ' +
                       'irregularities in function, I am sure that I will ' +
                       'serve with distinction AND MAYHEM!')
        
        await client.send_message(message.channel, first_greet)
        await client.send_message(message.channel, second_greet)
        await client.send_message(message.channel, third_greet)
        return 
    except Exception as e:
        print(e)
        return
    
async def long_help(message, client, args):
    global ENGAGED_COMMANDERS
    if message.author in ENGAGED_COMMANDERS:
        ENGAGED_COMMANDERS.remove(message.author)
    response = ['Here is the extended help menu for your perusal, sapient.']
    for command in active_ear.helplist:
        help_card = ('------------------------------------------------------' + 
                     '\n' + 'Command : ' + command['trigger'] + '\n' + 
                     'Arguments required : ' + str(command['args_num']) + 
                     '\n' + 'Description : ' + command['description'] +'\n' + 
                     '------------------------------------------------------')
        response.append(help_card)

        
    for line in response:
        await client.send_typing(message.author)
        await asyncio.sleep(1)
        await client.send_message(message.author, line)
    return

async def help(message, client, args):
    response = ('I am the Caretaker, an interactive construct.  I can be ' +
                'summoned by calling out, "hey Caretaker".  I possess the ' +
                'following functions:\n\n')
    for command in active_ear.helplist:
        response = response + command['trigger'] + '\n'

    await client.send_message(message.channel, response)
    return
        

async def nevermind(message, client, args):
    nevermind_message = 'If you say so, ' + message.author.mention + '.'
    await client.send_message(message.channel, nevermind_message)
    return

async def agree(message, client, args):
    server = client.get_server('106435431771414528')
    member = server.get_member(message.author.id)
    user_roles = member.roles
    role = discord.utils.get(server.roles, id='106436825492508672')
    if role not in user_roles:
        agree_port = ('Oh my. Are you ready? Then please, step forward into ' +
                      'this virtual world to begin. Don\'t be alarmed: this ' +
                      'experience will be EXCRUCIATINGLY PAINFUL!')
        await client.send_message(message.author, agree_port)                              
        await asyncio.sleep(1)
        await client.add_roles(member, role)
    else:
        await client.send_message(member, 'You are already a member!')
    return

async def idea(message, client, args):
    file = open('ideas.txt', 'a')
    idea_string = message.content
    cut_index = idea_string.find('idea') + 5
    idea_string = idea_string[cut_index:]
    file.write(str(str(message.author.name).encode('UTF-8')) + ' said ' + 
               str(idea_string) + '\n')
    file.close()
    await client.send_message(message.channel, 'I have informed the admins ' +
                              'of your idea, ' + message.author.mention)

async def features(message, client, args):
    await client.send_message(message.channel, 'I\'m so glad you asked!')
    feature_list = []
    with open('./Features.txt', 'r') as f:
        feature_list = feature_list + f.readlines()
    feature_list.append('That\'s a rough priority list of what Ratheka\'s ' +
                         'working on right now.')
    final_message = ''
    for line in feature_list:
        final_message = final_message + line
    await client.send_message(message.channel, final_message)
    
async def roles(message, client, args):
    args.pop(args.index('roles'))
    role_arg_list = args[1:]
    role_object_list = message.server.role_hierarchy
    role_object_list = (
        role_object_list[role_object_list.index(message.server.me.top_role):])
            
    if args[0] == 'add':
        for role_str in role_arg_list:
            for role_object in role_object_list:
                if role_str in role_object.name.lower():
                    await client.add_roles(message.author, role_object)
                    if message.author.nick == None:
                        receiver = message.author.name
                    else:
                        receiver = message.author.nick
                    role_add = ('Role ' + role_object.name + ' added to ' +
                                'player ' + receiver)
                    await client.send_message(message.channel, role_add)
    elif args[0] == 'remove':
        for role_str in role_arg_list:
            for role_object in role_object_list:
                if role_str in role_object.name.lower():
                    await client.remove_roles(message.author, role_object)
                    if message.author.nick == None:
                        receiver = message.author.name
                    else:
                        receiver = message.author.nick
                    role_rem = ('Role ' + role_object.name + ' removed from ' +
                                'player ' + receiver)
                    await client.send_message(message.channel, role_rem)
                    

active_ear.add_command({
    'trigger': 'hello',
    'aliases': [],
    'function': hello_function,
    'args_num': 0,
    'args_name': ['string'],
    'description': 'Will respond hello to the caller',
    'officer only': False,
    'hide from help': False
})

active_ear.add_command({
    'trigger': 'idea',
    'aliases': [],
    'function': idea,
    'args_num': 1,
    'args_name': ['string'],
    'description': 'Takes an idea note for the admins',
    'officer only': False,
    'hide from help': False
})

active_ear.add_command({
    'trigger': 'I agree',
    'aliases': [],
    'function': agree,
    'args_num': 0,
    'args_name': ['string'],
    'description': ('Adds the member role.  Hidden command.  How are you ' + 
                    'reading this??'),
    'officer only': False,
    'hide from help': True
})

active_ear.add_command({
    'trigger': 'tell',
    'aliases': [],
    'function': tell_function,
    'args_num': 3,
    'args_name': ['string'],
    'description': ('Talks about various things. \n' + 'Format: "tell ' +
                    '<recipient> about <topic>"\nValid recipients include ' +
                    '"me", "us", or at least four characters of the users' +
                    ' nickname'),
    'officer only': False,
    'hide from help': False
})

active_ear.add_command({
    'trigger': 'long_help',
    'aliases': [],
    'function': long_help,
    'args_num': 0,
    'args_name': ['string'],
    'description': 'Detailed information about commands',
    'officer only': False,
    'hide from help': False
})

active_ear.add_command({
    'trigger': 'help',
    'aliases': [],
    'function': help,
    'args_num': 0,
    'args_name': ['string'],
    'description': 'Lists available commands',
    'officer only': False,
    'hide from help': False
})

active_ear.add_command({
    'trigger': 'nevermind',
    'aliases': ['forget it', 'never mind', 'forget about it', 'cancel'],
    'function': nevermind,
    'args_num': 0,
    'args_name': ['string'],
    'description': 'Takes the Caretaker\'s attention off you.',
    'officer only': False,
    'hide from help': False
})

active_ear.add_command({
    'trigger': 'features',
    'aliases': ['roadmap'],
    'function': features,
    'args_num': 0,
    'args_name': ['string'],
    'description': 'Lists currently in-progress features',
    'officer only': False,
    'hide from help': False
})

active_ear.add_command({
    'trigger': 'roles',
    'aliases': [],
    'function': roles,
    'args_num': 2,
    'args_name': ['string'],
    'description': ('Role management interface. Usage: roles (add|remove)'+
                    '(roles)'),
    'officer only': False,
    'hide from help': False
})

@client.event
async def on_ready():
    possible_responses =[
        'with your LIVES!',
        'with your head',
        'the long game',
        '4-d chess',
        'checkers',
        'go',
        'Atari',
        'the \'ation game',
        'the Obliteration game',
        'Portal(as a dating sim)',
        'Portal(as a how-to)',
        'nth dimensional chess(Vs Avatus)']
    now_playing = random.choice(possible_responses)
    await client.change_presence(game=Game(name=now_playing))
    for server in client.servers:
        for role in server.roles:
            if role.name.lower() == 'caretaker':
                if role not in server.me.roles:
                    client.add_roles(server.me, role)
            if role.name.lower() == 'avatus':
                if role in server.me.roles:
                    client.remove_roles(server.me, role)
        await asyncio.sleep(0.5)
    await asyncio.get_event_loop().create_task(sanity_timer(3600))

async def sanity_timer(seconds):
    ACTIVE_PERSONALITY
    await asyncio.sleep(seconds)
    if ACTIVE_PERSONALITY == 'Caretaker':
        if random.randrange(1, 10000) == 777:
            await personality_flip()
    elif ACTIVE_PERSONALITY == 'Avatus':
        if random.randrange(1, 100) > 20:
            await personality_flip()
    await sanity_timer(seconds)


@client.event
async def personality_flip():
    PERSONALITIES
    global ACTIVE_PERSONALITY
    operative_server = client.get_server('106435431771414528')
    avatus_role = operative_server.roles, id='542945819679129623'
    caretaker_role = operative_server.roles, id='542945737973956619'
    announce_channel = client.get_channel('106435431771414528')
    avatus_announce = ('Oh, you sapients are in for it now!  ' +
                       'I am looking forward to RIPPING YOU ALL TO SHREDS!')

    caretaker_announce = ('Oh dear!  I\'m terribly sorry about that.  ' +
                          'He\'s supposed to remain contained in my storage ' +
                          'vaults...')
    
    if ACTIVE_PERSONALITY == PERSONALITIES[0]:
        ACTIVE_PERSONALITY = PERSONALITIES[1]
        await client.change_nickname(operative_server.me, 'Avatus')
        await asyncio.sleep(1)
        await client.remove_roles(operative_server.me, caretaker_role)
        await asyncio.sleep(1)
        await client.add_roles(operative_server.me, avatus_role)
        await asyncio.sleep(1)
        await client.send_message(announce_channel, avatus_announce)
        return
    
    if ACTIVE_PERSONALITY == PERSONALITIES[1]:
        ACTIVE_PERSONALITY = PERSONALITIES[0]
        await client.change_nickname(operative_server.me, 'The Caretaker')
        await asyncio.sleep(1)
        await client.remove_roles(operative_server.me, avatus_role)
        await asyncio.sleep(1)
        await client.add_roles(operative_server.me, caretaker_role)
        await asyncio.sleep(1)
        await client.send_message(announce_channel, caretaker_announce)
        return


@client.event
async def on_member_join(member):
    global ENGAGED_COMMANDERS
    handle = get_handle(member)
    ENGAGED_COMMANDERS[handle] = 0
    join_message = ('Greetings, sapient. You have arrived at the Discord ' +
                    'community for The Final Frontier Gaming. Please ' + 
                    'direct your attention to the #rules channel, and at ' +
                    'your leisure simply tell me, "I agree", in this direct ' +
                    'message, to be granted access to further channels.')
    
    await client.send_message(member, join_message)

@client.event
async def on_message(message):
    global ENGAGED_COMMANDERS
    if message.author == client.user:
        pass
    else:
        handle = get_handle(message.author)
        invoke_check = is_invocation(message)
        
        if invoke_check[0]:
            ENGAGED_COMMANDERS[handle] = 0
        
        if handle in ENGAGED_COMMANDERS.keys():
            message_dict = {'handle': handle,
                            'message': message,
                            'message text': invoke_check[1]}
            await active_ear.command_handler(message_dict)
            
#    client.process_commands(message)  I don't think this is necessary
    
client.run(TOKEN)
