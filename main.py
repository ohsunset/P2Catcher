import discum
import re
import time
import multiprocessing
import json
import datetime
import fake_useragent
import ctypes
from colorama import Fore, Style, init
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.layout import Layout

init(autoreset=True)
console = Console()
version = "v1.0.4"

with open(r"data\config.txt", "r") as file:
    info = json.loads(file.read())
    user_token = info["user_token"]
    channel_id = info["channel_id"]

with open(r"data\pokemon.txt", "r", encoding="utf8") as file:
    pokemon_list_string = file.read()

with open(r"data\legendaries.txt", "r") as file:
    legendary_list = file.read()

with open(r"data\mythics.txt", "r") as file:
    mythic_list = file.read()

num_pokemon = 0
num_shinies = 0
num_legendaries = 0
num_mythics = 0
num_fled = 0
start_time = time.time()

user_agent = fake_useragent.UserAgent()
bot = discum.Client(token=user_token, log=False, user_agent=user_agent.chrome)

def solve(message):
    hint = []
    for i in range(15, len(message) - 1):
        if message[i] != "\\":
            hint.append(message[i])

    hint_string = "".join(hint).strip()
    hint_replaced = hint_string.replace("_", ".").strip("!")
    solution = re.findall(f'^{hint_replaced}$', pokemon_list_string, re.IGNORECASE | re.MULTILINE)
    print_log(f"Matching against hint: '{hint_string}', found: {solution}", color=Fore.LIGHTCYAN_EX)
    return solution

def extract_pokemon_name(content):
    pattern = re.compile(r'[^:1234567890%]+')
    match = pattern.search(content)
    if match:
        extracted_text = match.group().strip()
        if extracted_text:
            return extracted_text
    return None

def spam():
    while True:
        bot.sendMessage(channel_id, version)
        time.sleep(4)

def start_spam_process():
    new_process = multiprocessing.Process(target=spam)
    new_process.start()
    return new_process

def stop_process(process_to_stop):
    process_to_stop.terminate()

def update_title():
    ctypes.windll.kernel32.SetConsoleTitleW(
        f"P2Catch - Pokemon Caught: {num_pokemon} | Shinies: {num_shinies} | Legendaries: {num_legendaries} | Mythics: {num_mythics} | Fled: {num_fled}"
    )

def print_log(message, color=Fore.WHITE):
    now = datetime.datetime.now()
    current_time = now.strftime("%H:%M:%S")
    console.print(f"[{current_time}] {color}{message}{Style.RESET_ALL}")

def update_gui():
    elapsed_time = time.time() - start_time
    elapsed_str = str(datetime.timedelta(seconds=int(elapsed_time)))
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="content")
    )
    
    header = Panel(f"[bold blue]P2Catch {version}[/bold blue]", style="bold blue", border_style="blue")
    content = Text(f"Pokemon Caught: {num_pokemon} | Shinies: {num_shinies} | Legendaries: {num_legendaries} | Mythics: {num_mythics} | Fled: {num_fled} | Time Elapsed: {elapsed_str}", style="bold cyan")
    
    layout["header"].update(header)
    layout["content"].update(content)
    
    return layout

@bot.gateway.command
def on_ready(resp):
    if resp.event.ready_supplemental:
        user = bot.gateway.session.user
        print_log(f"LOGGED INTO ACCOUNT: {user['username']}#{user['discriminator']}", color=Fore.GREEN)

@bot.gateway.command
def on_message(resp):
    global num_pokemon, num_shinies, num_legendaries, num_mythics, num_fled, spam_process

    if resp.event.message:
        m = resp.parsed.auto()
        content = m.get("content", "")
        channel_id_message = m["channel_id"]
        author_id = m["author"]["id"]

        if channel_id_message == channel_id:
            if author_id == "716390085896962058":
                if "The pokémon is " in content:
                    solution = solve(content)
                    if len(solution) == 0:
                        print_log("Pokemon could not be found in the database.", color=Fore.RED)
                    else:
                        for s in solution:
                            print_log(f"Sending catch command for: {s}", color=Fore.YELLOW)
                            time.sleep(4)
                            bot.sendMessage(channel_id, f"<@716390085896962058> catch {s}")
                        if spam_process is None or not spam_process.is_alive():
                            spam_process = start_spam_process()
                elif "Congratulations" in content:
                    num_pokemon += 1

                    if "These colors seem unusual..." in content:
                        num_shinies += 1

                    split = content.split(" ")
                    msg = " ".join(split[2:])
                    print_log(msg, color=Fore.CYAN)

                    pokemon = split[7].replace("!", "").strip()

                    if re.findall(f'^{pokemon}$', legendary_list, re.IGNORECASE | re.MULTILINE):
                        num_legendaries += 1

                    if re.findall(f'^{pokemon}$', mythic_list, re.IGNORECASE | re.MULTILINE):
                        num_mythics += 1

                    update_title()

                elif "Whoa there. Please tell us you're human!" in content:
                    stop_process(spam_process)
                    print_log("Captcha detected, program paused. Press enter to restart.", color=Fore.YELLOW)
                    input()
                    bot.sendMessage(channel_id, f"<@716390085896962058> catch")

            elif author_id == "854233015475109888":
                pokemon_name = extract_pokemon_name(content)
                if pokemon_name:
                    print_log(f"Sending catch command for assistant's Pokémon: {pokemon_name}", color=Fore.YELLOW)
                    bot.sendMessage(channel_id, f"<@716390085896962058> catch {pokemon_name}")
                else:
                    print_log("No Pokémon name extracted from the message.", color=Fore.RED)

        live.update(update_gui())

if __name__ == "__main__":
    print("=============================================================================")
    print_log("Starting P2Catch", color=Fore.GREEN)

    spam_process = start_spam_process()

    with Live(update_gui(), console=console, refresh_per_second=2) as live:
        bot.gateway.run(auto_reconnect=True)