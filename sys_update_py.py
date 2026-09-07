#!/usr/bin/env python3

import subprocess
from datetime import datetime
import time
import requests
from dotenv import load_dotenv
import os

import logging

#Set logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)

#Load variables
load_dotenv(dotenv_path="/usr/local/sbin/.sys_update_py.env")
bot_tkn = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")
server_name = os.getenv("SERVER_NAME")

#Build the function to send telegram messages
def telegram_msg(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)

def cmd_execute(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()
    all_ok = True
    if process.returncode != 0:
        all_ok = False
    return all_ok, output, error



def main():

# Ubuntu/Debian udate commands
    commands = [
        {"name": "update_index",    "role": "critical", "stop_on_fail": True,  "command": ["apt", "update"]},
        {"name": "list_upgradable", "role": "report",   "stop_on_fail": False, "command": ["apt", "list", "--upgradable"]},
        {"name": "upgrade",         "role": "critical", "stop_on_fail": True,  "command": ["apt", "upgrade", "-y"]},  #--dry-run
        {"name": "cleanup",         "role": "cleanup",  "stop_on_fail": False, "command": ["apt", "autoremove", "--purge", "-y"]}
        ]
# Fedora update commands
#     commands = [
#         {"name": "update_index",    "role": "critical", "stop_on_fail": True,  "command": ["dnf", "makecache"]},
#         {"name": "list_upgradable", "role": "report",   "stop_on_fail": False, "command": ["dnf", "list", "upgrades"]},
#         {"name": "upgrade",         "role": "critical", "stop_on_fail": True,  "command": ["dnf", "upgrade", "-y"]},  # --assumeno
#         {"name": "cleanup",         "role": "cleanup",  "stop_on_fail": False, "command": ["dnf", "autoremove", "-y"]}
# ]
    

    for cmd in commands:
        ok, output, error = cmd_execute(cmd["command"])
        if not ok:
            if cmd["stop_on_fail"]:
                message = f"Failed to execute {' '.join(cmd['command'])}. Upgrade process failed with error: {error}"
                logging.error(message)
                telegram_msg(bot_tkn, chat_id, server_name+" "+message)
                break
            else:
                message=f"Command {' '.join(cmd['command'])} failed to execute with error: {error}"
                logging.warning(message)
                telegram_msg(bot_tkn, chat_id, server_name+" "+message)
        else:
            if cmd["role"] == "report":
                packages = [app.split('/')[0] for app in output.splitlines() if "upgradable" in app]
                if not packages:
                    message = "No packages to upgrade"
                    logging.info(message)
                    telegram_msg(bot_tkn, chat_id, server_name+" "+message)
                    break
                else:
                    message = f"Packages to upgrade:\n{'\n'.join(packages)}"
                    logging.info(message)
            if cmd["role"] == "cleanup":
                message = f"Cleanup: \n{output}"
                logging.info(message)
    else:
        message = f"Upgrade process completed successfully"
        logging.info(message)
        telegram_msg(bot_tkn, chat_id, server_name+" "+message)

    if os.path.exists("/var/run/reboot-required"):
        time.sleep(30)
        message = "Reboot requested due to upgrades"
        logging.info(message)
        telegram_msg(bot_tkn, chat_id, server_name+" "+message)
        _, _, error = cmd_execute(["systemctl", "reboot"])
        if error:
            message=f"Reboot system: {error}"
            logging.error(message)
            telegram_msg(bot_tkn, chat_id, f"{server_name} reboot error, check the log file")

        
if __name__ == "__main__":
    main()


"""
The script location: /usr/local/sbin/sys_update_py.py
Make it executable: chmod +x /usr/local/sbin/sys_update_py.py
Crontab: sudo crontab -e and add: 0 22 * * * /usr/bin/python3 /usr/local/sbin/sys_update_py.py
The .env file location: /usr/local/sbin/

test: sudo /usr/bin/python3 /usr/local/sbin/sys_update_py.py

"""
