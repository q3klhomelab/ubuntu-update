#!/usr/bin/env python3

import subprocess
from datetime import datetime
import time
import requests
from dotenv import load_dotenv
import os

#Load variables
load_dotenv(dotenv_path="/usr/local/sbin/.sys_update_py.env")
bot_tkn = os.getenv("BOT_TOKEN")
chat_id = os.getenv("CHAT_ID")

#Set the log file
log_file = f"/var/log/sys_update_py_{datetime.now().strftime('%Y-%m-%d')}.log"

#Set the server name for the log file and telegram message
server_name = "GreenSRV"

def log_msg(log_file, message):
    with open(log_file, "a+") as file:
        file.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}\n")

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
   
    commands = [
        {"name": "update_index", "role": "critical", "stop_on_fail": True, "command": ["apt", "update"]},
        {"name": "list_upgradable", "role": "report", "stop_on_fail": False, "command": ["apt", "list", "--upgradable"]},
        {"name": "upgrade", "role": "critical", "stop_on_fail": True, "command": ["apt", "upgrade", "-y"]},
        {"name": "cleanup", "role": "cleanup", "stop_on_fail": False, "command": ["apt", "autoremove", "--purge", "-y"]}
        ]
    

    for cmd in commands:
        ok, output, error = cmd_execute(cmd["command"])
        if not ok:
            if cmd["stop_on_fail"]:
                message = f"ERROR Failed to execute {' '.join(cmd['command'])}. Upgrade process failed with error: {error}"
                log_msg(log_file, message)
                telegram_msg(bot_tkn, chat_id, server_name+" "+message)
                break
            else:
                log_msg(log_file, f"WARNING Command {' '.join(cmd['command'])} failed to execute with error: {error}")
                telegram_msg(bot_tkn, chat_id, f"{server_name} succesfully upgraded. Command {" ".join(cmd['command'])} failed to execute, check the log file")
        else:
            if cmd["role"] == "report":
                packages = [app.split('/')[0] for app in output.splitlines() if "upgradable" in app]
                if not packages:
                    telegram_msg(bot_tkn, chat_id, f"{server_name} no packages to upgrade")
                    break
                else:
                    message = f"REPORT Upgraded packages:\n{'\n'.join([app.split('/')[0] for app in output.splitlines() if "upgradable" in app])}"
                    log_msg(log_file, message)
            if cmd["role"] == "cleanup":
                message = f"REPORT Cleanup: \n{output}"
                log_msg(log_file, message)
    else:
        message = f"SUCCESS Upgrade process completed successfully"
        log_msg(log_file, message)
        telegram_msg(bot_tkn, chat_id, server_name+" "+message)

    if os.path.exists("/var/run/reboot-required"):
        time.sleep(30)
        log_msg(log_file, "REPORT reboot requested due to upgrades")
        telegram_msg(bot_tkn, chat_id, f"{server_name} will reboot now")
        _, _, error = cmd_execute(["systemctl", "reboot"])
        if error:
            log_msg(log_file, f"ERROR reboot system: {error}")
            telegram_msg(bot_tkn, chat_id, f"{server_name} reboot error, check the log file")

        
if __name__ == "__main__":
    main()


"""
Unde pun scriptul: /usr/local/sbin/sys_update_py.py
il fac executabil cu: chmod +x /usr/local/sbin/sys_update_py.py
editez crontab: sudo crontab -e si adaug: 0 22 * * * /usr/bin/python3 /usr/local/sbin/sys_update_py.py
pun si .env unde am pus scriptul, in: /usr/local/sbin/

test: sudo /usr/bin/python3 /usr/local/sbin/sys_update_py.py

"""
