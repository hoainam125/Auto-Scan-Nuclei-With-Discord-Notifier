import os
import subprocess
import asyncio
import concurrent.futures
from datetime import datetime
import discord
from discord import Intents
from fake_useragent import UserAgent
import aiohttp
# Constants
MAX_MESSAGE_LENGTH = 2000
MESSAGE_DELAY = 2  # seconds

# Discord setup with intents
intents = Intents.default()
intents.messages = True
intents.guilds = True
token = "YOUR DISCORD TOKEN HERE"
os.system("clear")
client = discord.Client(intents=intents)

async def create_aiohttp_session():
    return aiohttp.ClientSession(trust_env=True)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    max_req_per_s = 150
    template_root_path = "result"
    target_list = "httpx_dir_scope"
    client.aiohttp_session = await create_aiohttp_session()
    await main(max_req_per_s, template_root_path, target_list)
async def get_channel(channel_id):
    try:
        channel = await client.fetch_channel(channel_id)
        return channel
    except Exception as e:
        print(f"Error fetching channel: {e}")
        return None
async def send_to_channel(channel, message):
    if not message.strip():
        print("Empty message, not sending.")
        return

    try:
        # Splitting message into chunks of 2000 characters
        char_limit = 2000
        msg_chunks = [message[i:i + char_limit] for i in range(0, len(message), char_limit)]

        for chunk in msg_chunks:
            await channel.send(chunk)
            await asyncio.sleep(MESSAGE_DELAY)  # Optional delay between message chunks
    except Exception as e:
        print(f"Error sending message to {channel.name}: {e}")

async def send_scan_results(template_name, log_file_path, specific_channel_id):
    current_time = datetime.now().strftime("%I:%M%p %d/%m/%Y")
    message_intro = f"@everyone, Now is {current_time}. I have done the scan on Target using {template_name}"

    if os.path.exists(log_file_path) and os.path.getsize(log_file_path) > 0:
        with open(log_file_path, "r") as log_file:
            log_contents = log_file.readlines()
            message_body = " and I found:\n" + ''.join([f"+{line}\n" for line in log_contents])
    else:
        message_body = " but did not find anything, hope we will have better luck next time\n"

    # Get the specific channel
    specific_channel = await get_channel(specific_channel_id)
    if specific_channel:
        await send_to_channel(specific_channel, message_intro + message_body)
    else:
        print(f"Channel with ID {specific_channel_id} not found.")

def list_directories(destination):
    return os.listdir(destination)

async def execute_nuclei_command(target_variable, dir_to_template, output_file, max_req_per_s):
    ua = UserAgent()
    user_agent = ua.random

    command = f"nuclei -H 'User-Agent:{user_agent}' -stats -l {target_variable} -t {dir_to_template} -o {output_file} -rl {max_req_per_s}"
    print("Execute command: " + command)

    loop = asyncio.get_running_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        await loop.run_in_executor(pool, lambda: subprocess.run(command, shell=True))

def init_new_file(result_path, template_root_path):
    template = sorted(list_directories(template_root_path))
    with open(result_path, 'w') as file:
        print(f"File {result_path} was created.")
        for i in template:
            file.write(i + "\n")

def append_done_template(done_template):
    with open("done_list.txt", 'a') as file:
        print(f"{done_template} has Done! write to log!")
        file.write(done_template + "\n")

def rewrite_template_left(result_path, lines):
    with open(result_path, 'w') as file:
        print(f"there are {len(lines)} left")
        for i in lines:
            file.write(i + "\n")

# Asynchronous main execution function
async def main(max_req_per_s, template_root_path, target_list):
    result_path = "progress_nuclei.txt"
    logs_dir = "logs"
    
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
        print(f"Folder {logs_dir} was created.")
    else:
        print(f"The Folder {logs_dir} already exists.")

    if not os.path.exists(result_path):
        init_new_file(result_path, template_root_path)
    else:
        print(f"The file {result_path} already exists.")

    with open(result_path, "r") as file:
        lines = [line.strip("\n") for line in file.readlines()]

    for i in lines:
        await execute_nuclei_command(target_variable=target_list, dir_to_template=os.path.join(template_root_path, i), output_file=os.path.join(logs_dir, i), max_req_per_s=max_req_per_s)
        # Replace CHANNEL_ID with the actual channel ID
        SPECIFIC_CHANNEL_ID = YOUR_CHANNEL_ID_HERE

# Inside your main function, update the call to send_scan_results
        await send_scan_results(i, os.path.join(logs_dir, i), SPECIFIC_CHANNEL_ID)

        
        lines.remove(i)
        append_done_template(i)
        rewrite_template_left(result_path, lines)


client.event(on_ready)
client.run(token)  # Replace with your Discord bot token
