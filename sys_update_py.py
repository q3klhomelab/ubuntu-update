#!/usr/bin/env python3

import subprocess
import time
import requests
from dotenv import load_dotenv
import os

import logging
from logging.handlers import RotatingFileHandler

#Load variables
env_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), ".sys_update_py.env")
if os.path.exists(env_file):
    load_dotenv(dotenv_path=env_file)
    
bot_tkn = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")
server_name = os.getenv("SERVER_NAME")
server_os = os.getenv("SERVER_OS")

#Set logger
log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "log_dir")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "sys_update.log")

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

file_handler = RotatingFileHandler(
    filename=log_file,
    maxBytes=5*1024**2,
    backupCount=3,
    encoding="utf-8"
)
console_handler = logging.StreamHandler()

formater = logging.Formatter(
    "%(asctime)s [%(levelname)s] %(message)s"
)

file_handler.setFormatter(formater)
console_handler.setFormatter(formater)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

#Build the function to send telegram messages
def telegram_msg(token, chat_id, message):
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={message}"
    requests.get(url)

#Build the function to execute the commands
def cmd_execute(cmd):
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    output, error = process.communicate()
    all_ok = True
    if process.returncode not in [0, 100]:      #dnf return code 100 for success
        all_ok = False
    return all_ok, output, error

def main():

    if server_os=="Debian":
        # Debian update commands
        commands = [
            {"name": "update_index",    "role": "critical", "stop_on_fail": True,  "command": ["apt", "update"]},
            {"name": "list_upgradable", "role": "report",   "stop_on_fail": False, "command": ["apt", "list", "--upgradable"]},
            {"name": "upgrade",         "role": "critical", "stop_on_fail": True,  "command": ["apt", "upgrade", "-y"]},  #--dry-run
            {"name": "cleanup",         "role": "cleanup",  "stop_on_fail": False, "command": ["apt", "autoremove", "--purge", "-y"]}
            ]
    elif server_os=="RedHat":
        # RedHat update commands
        commands = [
            {"name": "update_index",    "role": "critical", "stop_on_fail": True,  "command": ["dnf", "makecache"]},
            {"name": "list_upgradable", "role": "report",   "stop_on_fail": False, "command": ["dnf", "check-update"]},
            {"name": "upgrade",         "role": "critical", "stop_on_fail": True,  "command": ["dnf", "upgrade", "-y"]},  # --assumeno
            {"name": "cleanup",         "role": "cleanup",  "stop_on_fail": False, "command": ["dnf", "autoremove", "-y"]}
            ]
    else:
        logger.error("Unknown Operatig System")
        return
    

    for cmd in commands:
        ok, output, error = cmd_execute(cmd["command"])
        if not ok:
            if cmd["stop_on_fail"]:
                message = f"Failed to execute {' '.join(cmd['command'])}. Upgrade process failed with error: {error}"
                logger.error(message)
                telegram_msg(bot_tkn, chat_id, server_name+" "+message)
                break
            else:
                message=f"Command {' '.join(cmd['command'])} failed to execute with error: {error}"
                logger.warning(message)
                telegram_msg(bot_tkn, chat_id, server_name+" "+message)
        else:
            if cmd["role"] == "report":

                if server_os=="Debian":
                    packages = [app.split('/')[0] for app in output.splitlines() if "upgradable" in app]
                elif server_os=="RedHat":
                    packages = [parts[0].split(".")[0] for line in output.splitlines() if (parts:=line.split()) and "." in parts[0]]

                if not packages:
                    message = "No packages to upgrade"
                    logger.info(message)
                    telegram_msg(bot_tkn, chat_id, server_name+" "+message)
                    break
                else:
                    message = f"Packages to upgrade:\n{'\n'.join(packages)}"
                    logger.info(message)
            if cmd["role"] == "cleanup":
                message = f"Cleanup: \n{output}"
                logger.info(message)
    else:
        message = f"Upgrade process completed successfully"
        logger.info(message)
        telegram_msg(bot_tkn, chat_id, server_name+" "+message)

    if os.path.exists("/var/run/reboot-required"):
        time.sleep(30)
        message = "Reboot requested due to upgrades"
        logger.info(message)
        telegram_msg(bot_tkn, chat_id, server_name+" "+message)
        _, _, error = cmd_execute(["systemctl", "reboot"])
        if error:
            message=f"Reboot system: {error}"
            logger.error(message)
            telegram_msg(bot_tkn, chat_id, f"{server_name} reboot error, check the log file")

        
if __name__ == "__main__":
    main()