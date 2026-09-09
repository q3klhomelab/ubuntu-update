# SysUpdate Automation

A lightweight, automated Python script designed to handle system updates, maintain rotating logs, and send real-time Telegram notifications for Linux servers (supporting both Debian/Ubuntu and RedHat/Fedora distributions).

## 🚀 About the Project

This project started out of a personal need for a reliable script to keep an Ubuntu server updated daily, track updates in a log file, and send alerts via Telegram if anything went wrong. As the homelab expanded to include Fedora-based machines, the script was adapted to dynamically support both `apt` and `dnf` package managers, ensuring a unified update workflow across different systems.

## ✨ Features

- **Cross-Distribution Support:** Dynamically adapts its update workflow based on the operating system (`Debian` or `RedHat`) specified by the user in the environment configuration file.
- **Smart Package Parsing:** Cleanly extracts upgradable packages, filtering out system headers and empty lines.
- **Telegram Notifications:** Sends instant status updates, error warnings, and success messages directly to your Telegram chat.
- **Robust Logging:** Maintains a local rotating log file (`log_dir/sys_update.log`) to keep history clean without disk bloat.
- **Automated Reboots:** Gracefully detects if a system reboot is required (`/var/run/reboot-required`) and triggers it safely.

---

## 🛠️ Installation Guide

Follow these steps to set up the script on your server:

### 1. Clone or Download Files
Create the target directory and place the project files inside:
```bash
sudo mkdir -p /opt/sys_update
cd /opt/sys_update
# (Place the script .py file, requirements.txt, and .env.example here)
```

### 2. Set Up a Python Virtual Environment
Create and activate a virtual environment for the project:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the required Python packages using pip:
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Rename the example environment file and edit it with your specific credentials:
```bash
mv .sys_update_py.env.example .sys_update_py.env
nano .sys_update_py.env
```
Fill in your configuration details:

    BOT_TOKEN: Your Telegram bot token

    CHAT_ID: Your Telegram chat ID

    SERVER_NAME: A friendly identifier for your server

    SERVER_OS: Set to either Debian or RedHat

## ⏰ Scheduling with Cron
To run the update script automatically every day (e.g., at 22:00), configure a root cron job:
### 1. Open the root crontab:
```bash
sudo crontab -e
```
### 2. Add the following line at the bottom of the file:
```
0 22 * * * /opt/sys_update/.venv/bin/python3 /opt/sys_update/sys_update_py.py
```

## 📄 License

This project is open-source and available under the MIT License.