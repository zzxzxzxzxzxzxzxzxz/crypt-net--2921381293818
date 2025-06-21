import os
import time
import random
import threading
import discum
import tls_client
import re
import json
import pyfiglet
import wikipedia
import qrcode
import tempfile
import datetime
import requests
from colorama import Fore, Style, init  
init(autoreset=True)
from deep_translator import GoogleTranslator
from gtts import gTTS
from rich.console import Console
from rich.text import Text
from io import BytesIO

user_tts_map = {}

partner_auto_send = {}

badge_rotator_thread = None
badge_rotator_running = False


os.system("title Abyss")


console = Console()

ASCII_ART = """
 ▄▄▄       ▄▄▄▄ ▓██   ██▓  ██████   ██████ 
▒████▄    ▓█████▄▒██  ██▒▒██    ▒ ▒██    ▒ 
▒██  ▀█▄  ▒██▒ ▄██▒██ ██░░ ▓██▄   ░ ▓██▄   
░██▄▄▄▄██ ▒██░█▀  ░ ▐██▓░  ▒   ██▒  ▒   ██▒
 ▓█   ▓██▒░▓█  ▀█▓░ ██▒▓░▒██████▒▒▒██████▒▒
 ▒▒   ▓▒█░░▒▓███▀▒ ██▒▒▒ ▒ ▒▓▒ ▒ ░▒ ▒▓▒ ▒ ░
  ▒   ▒▒ ░▒░▒   ░▓██ ░▒░ ░ ░▒  ░ ░░ ░▒  ░ ░
  ░   ▒    ░    ░▒ ▒ ░░  ░  ░  ░  ░  ░  ░  
      ░  ░ ░     ░ ░           ░        ░  
                ░░ ░                       
"""

def print_gradient_ascii_centered():
    try:
        width = os.get_terminal_size().columns
    except:
        width = 80

    for line in ASCII_ART.splitlines():
        text = Text()
        non_space_chars = [c for c in line if c != " "]
        total_chars = len(non_space_chars)
        current_index = 0

        for char in line:
            if char != " ":
                ratio = current_index / (total_chars - 1) if total_chars > 1 else 0
                r = int(0   * (1 - ratio) + 0   * ratio)
                g = int(0   * (1 - ratio) + 0   * ratio)
                b = int(255 * (1 - ratio) + 0   * ratio)
                color_code = f"#{r:02x}{g:02x}{b:02x}"
                text.append(char, style=color_code)
                current_index += 1
            else:
                text.append(" ")
        left_padding = max((width - len(line)) // 2, 0)
        console.print(" " * left_padding, end="")
        console.print(text)
        time.sleep(0.1)

print_gradient_ascii_centered()

def gradient_print(text, width=50):
        padded_text = text.ljust(width)
        total_chars = len(padded_text)
        color_points = [
                (100, 0, 0),      
                (120, 40, 0),     
                (100, 100, 0),    
                (0, 50, 0),       
                (0, 0, 80),       
                (0, 0, 50)        
        ]

        def lerp_color(c1, c2, t):
                return (
                        int(c1[0] + (c2[0] - c1[0]) * t),
                        int(c1[1] + (c2[1] - c1[1]) * t),
                        int(c1[2] + (c2[2] - c1[2]) * t)
                )

        gradient_text = Text()
        segments = len(color_points) - 1

        for i, char in enumerate(padded_text):
                pos = i / (total_chars - 1) if total_chars > 1 else 0
                segment_index = min(int(pos * segments), segments - 1)
                segment_pos = (pos - segment_index / segments) * segments
                r, g, b = lerp_color(color_points[segment_index], color_points[segment_index + 1], segment_pos)
                color_code = f"#{r:02x}{g:02x}{b:02x}"
                gradient_text.append(char, style=color_code)

        console.print(gradient_text)

with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)

owner_id_raw = config.get("owner_id", "")
if isinstance(owner_id_raw, list):
    OWNER_ID = [str(i).strip() for i in owner_id_raw]
else:
    OWNER_ID = [str(owner_id_raw).strip()]
PREFIX = config.get("prefix", ">").strip()
PING_MESSAGE = config.get("ping_message")
ACCOUNT = config.get("account", "").strip()
ACCOUNT_HOLDER = config.get("account_holder", "").strip()

if not OWNER_ID:
        print("config.json에서 owner_id를 찾을 수 없습니다.")
        exit(1)

gradient_print(f"[info] Owner ID: {OWNER_ID}")
gradient_print(f"[info] Prefix: {PREFIX}")
gradient_print(f"[info] Account: {ACCOUNT}")
gradient_print(f"[info] Account Holder: {ACCOUNT_HOLDER}")

with open("tokens.txt", "r") as f:
    TOKENS = [line.strip() for line in f if line.strip()]

gradient_print(f"✅ 총 {len(TOKENS)}개의 토큰 불러오기 성공!")

clients = []
print_lock = threading.Lock()
spamming = False
spam_threads = []

def print_log(TOKEN, text, cid=None):
    uid = TOKEN[:10]
    short_uid = uid[:12] + "..." if len(uid) > 15 else uid
    text_column = f"{text:<25}"
    with print_lock:
        if cid:
            gradient_print(f"[{short_uid}]  {text_column}  채널 {cid}")
        else:
            gradient_print(f"[{short_uid}]  {text_column}")

def spam_task(TOKEN, CHANNEL_ID, MESSAGE):
    session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
    headers = {
        "Authorization": TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    while spamming:
        try:
            session.post(
                f"https://discord.com/api/v9/channels/{CHANNEL_ID}/messages",
                json={"content": MESSAGE},
                headers=headers
            )
        except:
            pass
        time.sleep(random.uniform(0.5, 1.2))

def parse_emoji(emj):
    if emj.startswith("<:") or emj.startswith("<a:"):
        match = re.match(r"<a?:([a-zA-Z0-9_]+):(\d+)>", emj)
        if match:
            name, eid = match.groups()
            return f"{name}:{eid}"
    return emj

def schedule_partner_message(client, cid, count, message):
    global partner_auto_send 
    def send_loop():
        while partner_auto_send.get(cid, False):
            now = datetime.datetime.now()
            seconds_per_send = 24 * 60 * 60 / count
            for i in range(count):
                if not partner_auto_send.get(cid, False):
                    break
                client.sendMessage(cid, f"{message}")
                time.sleep(seconds_per_send)
            tomorrow = (now + datetime.timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            wait_sec = (tomorrow - datetime.datetime.now()).total_seconds()
            if wait_sec > 0:
                time.sleep(wait_sec)
    threading.Thread(target=send_loop, daemon=True).start()
def change_guild_tag(tls_session, token, guild_id, new_tag):

    url = f"https://discord.com/api/v9/users/@me/guild-profiles/{guild_id}"
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {"tag": new_tag}
    res = tls_session.patch(url, headers=headers, json=payload)
    return res

def create_client(TOKEN):
    client = discum.Client(token=TOKEN, log=False)
    tls_session = tls_client.Session(client_identifier="chrome_120", random_tls_extension_order=True)
    rename_active = {}
    emoji_map = {}
    pinned_users = set()




    def headers(token):
        return {
            "Authorization": token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0"
        }

    def rename_group(channel_id, base_name):
        while rename_active.get(channel_id, False):
            new_name = f"{base_name} {random.randint(1000, 9999)}"
            try:
                response = tls_session.patch(
                    f"https://discord.com/api/v9/channels/{channel_id}",
                    headers=headers(TOKEN),
                    json={"name": new_name}
                )
                if response.status_code == 200:
                    print_log(TOKEN, f"변경됨 -> {new_name}", channel_id)
                elif response.status_code == 429:
                    retry_after = response.json().get("retry_after", 5)
                    print_log(TOKEN, f"Rate Limited! {retry_after}초 후 재시도...", channel_id)
                    time.sleep(retry_after)
                else:
                    print_log(TOKEN, f"실패: {response.status_code}", channel_id)
                    rename_active[channel_id] = False
                    break
                time.sleep(1.5)
            except Exception as e:
                print_log(TOKEN, f"예외 발생: {e}", channel_id)
                break

    def join_voice(guild_id, channel_id):
        client.gateway.send({
            "op": 4,
            "d": {
                "guild_id": guild_id,
                "channel_id": channel_id,
                "self_mute": False,
                "self_deaf": False
            }
        })
        print_log(TOKEN, f"음성채널 참가 {channel_id}")

    def leave_voice(guild_id):
        client.gateway.send({
            "op": 4,
            "d": {
                "guild_id": guild_id,
                "channel_id": None,
                "self_mute": False,
                "self_deaf": False
            }
        })
        print_log(TOKEN, "음성채널 나감")

    def generate_minesweeper(size=5):
        size = max(5, min(size, 10))
        board = [[0 for _ in range(size)] for _ in range(size)]
        mines = random.sample(range(size*size), size)
        
        for m in mines:
            x, y = m // size, m % size
            board[x][y] = '💣'
            for i in range(max(0, x-1), min(size, x+2)):
                for j in range(max(0, y-1), min(size, y+2)):
                    if board[i][j] != '💣':
                        board[i][j] += 1

        return "\n".join("||" + "||||".join(str(cell) if cell != 0 else "⬜" for cell in row) + "||" for row in board)

    def create_webhook(channel_id, token):
        headers = {"Authorization": token, "Content-Type": "application/json"}
        data = {"name": "Abyss Webhook"}
        res = requests.post(f"https://discord.com/api/v9/channels/{channel_id}/webhooks", headers=headers, json=data)
        return res.json()

    def get_crypto_price(coin):
        try:
            symbol_map = {
                "btc": ("bitcoin", "Bitcoin"),
                "eth": ("ethereum", "Ethereum"),
                "doge": ("dogecoin", "Dogecoin"),
                "sol": ("solana", "Solana"),
                "xrp": ("ripple", "Ripple"),
                "ada": ("cardano", "Cardano"),
                "matic": ("matic-network", "Polygon"),
                "trx": ("tron", "Tron"),
                "ltc": ("litecoin", "Litecoin"),
                "bch": ("bitcoin-cash", "Bitcoin Cash"),
                "dot": ("polkadot", "Polkadot"),
                "avax": ("avalanche-2", "Avalanche"),
                "link": ("chainlink", "Chainlink"),
                "atom": ("cosmos", "Cosmos"),
                "etc": ("ethereum-classic", "Ethereum Classic"),
                "xlm": ("stellar", "Stellar"),
                "eos": ("eos", "EOS"),
                "sand": ("the-sandbox", "The Sandbox"),
                "ape": ("apecoin", "ApeCoin"),
                "arb": ("arbitrum", "Arbitrum"),
                "op": ("optimism", "Optimism")
            }
            if coin.lower() in symbol_map:
                coin_id, coin_fullname = symbol_map[coin.lower()]
            else:
                coin_id = coin.lower()
                coin_fullname = coin.capitalize()
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd"
            res = requests.get(url).json()
            if coin_id not in res or 'usd' not in res[coin_id]:
                return f"❌ 지원하지 않는 코인 이름/심볼입니다.\n예시: {PREFIX}crypto sol"
            price = res[coin_id]['usd']
            return f"💰 {coin_fullname} 가격: ${price:,.2f}"
        except Exception as e:
            return f"암호화폐 정보를 가져올 수 없습니다. 오류: {e}"

    def typier(channel_id):
        try:
            while True:
                res = tls_session.post(
                    f"https://discord.com/api/v9/channels/{channel_id}/typing",
                    headers=headers(TOKEN)
                )
                if res.status_code == 204:
                    print_log(TOKEN, "Typing 중...", channel_id)
                    time.sleep(9)
                elif res.status_code == 429:
                    retry_after = res.json().get("retry_after", 5)
                    print_log(TOKEN, f"Rate Limited - {retry_after}s 대기", channel_id)
                    time.sleep(float(retry_after))
                else:
                    print_log(TOKEN, f"Typing 실패: {res.status_code}", channel_id)
                    break
        except Exception as e:
            print_log(TOKEN, f"Typing 예외: {e}", channel_id)

    @client.gateway.command
    def on_message(resp):
        nonlocal rename_active, emoji_map, pinned_users
        global spamming, spam_threads, PREFIX

        if not resp.event.message:
            return

        msg = resp.parsed.auto()
        uid = msg["author"]["id"]
        cid = msg["channel_id"]
        content = msg["content"]
        mid = msg["id"]
        gid = msg.get("guild_id", None)

        if uid in emoji_map:
            for emj in emoji_map[uid]:
                try:
                    parsed = parse_emoji(emj)
                    client.addReaction(cid, mid, parsed)
                except Exception as e:
                    print_log(TOKEN, f"이모지 실패: {e}", cid)

        
        with open("config.json", "r", encoding="utf-8") as f:
            config_data = json.load(f)
        owner_ids = config_data.get("owner_id", [])
        if isinstance(owner_ids, str):
            owner_ids = [owner_ids]
        if uid not in owner_ids:
            return

        if content.startswith(PREFIX + "prefix "):
            new_prefix = content[len(PREFIX + "prefix "):].strip()
            if new_prefix:
                PREFIX = new_prefix
                try:
                    with open("config.json", "r", encoding="utf-8") as f:
                        config_data = json.load(f)
                    config_data["prefix"] = new_prefix
                    with open("config.json", "w", encoding="utf-8") as f:
                        json.dump(config_data, f, ensure_ascii=False, indent=4)
                except Exception as e:
                    print_log(TOKEN, f"config.json 저장 오류: {e}", cid)
                print_log(TOKEN, f"접두사 변경됨 → {PREFIX}", cid)
            else:
                print_log(TOKEN, "새 접두사를 입력하세요.", cid)
            return

        if content.startswith(PREFIX + "fd "):
            if spamming:
                print_log(TOKEN, "이미 도배 중입니다", cid)
                return
            message = content[len(PREFIX + "fd "):].strip()
            if not message:
                print_log(TOKEN, "도배 메시지가 비어 있음", cid)
                return
            spamming = True
            spam_threads.clear()
            for tok in TOKENS:
                t = threading.Thread(target=spam_task, args=(tok, cid, message), daemon=True)
                t.start()
                spam_threads.append(t)
            print_log(TOKEN, f"도배 시작: '{message}'", cid)

        elif content == PREFIX + "fdstop":
            if not spamming:
                print_log(TOKEN, "도배 중이 아닙니다", cid)
                return
            spamming = False
            print_log(TOKEN, "도배 중지됨", cid)

        elif content.startswith(PREFIX + "gn "):
            name = content[len(PREFIX + "p "):].strip()
            if not name:
                return
            if rename_active.get(cid, False):
                print_log(TOKEN, "이미 변경 중", cid)
                return
            rename_active[cid] = True
            threading.Thread(target=rename_group, args=(cid, name), daemon=True).start()

        elif content == PREFIX + "gn-stop":
            rename_active[cid] = False
            print_log(TOKEN, "이름 변경 중지", cid)

        elif any(content.startswith(cmd) for cmd in [PREFIX + "sp ", PREFIX + "sl ", PREFIX + "sw ", PREFIX + "sc "]):
            activity_map = {PREFIX + "sp": 0, PREFIX + "sl": 2, PREFIX + "sw": 3, PREFIX + "sc": 5}
            for cmd, act_type in activity_map.items():
                if content.startswith(cmd):
                    msg_ = content[len(cmd):].strip()
                    presence = {
                        "op": 3,
                        "d": {
                            "since": 0,
                            "activities": [{"name": msg_, "type": act_type}],
                            "status": "online",
                            "afk": False
                        }
                    }
                    client.gateway.send(presence)
                    print_log(TOKEN, f"상태 변경됨: {msg_}", cid)

        elif content.startswith(PREFIX + "vf "):
            parts = content.split()
            if len(parts) == 2 and gid:
                join_voice(gid, parts[1])

        elif content == PREFIX + "leave":
            if gid:
                leave_voice(gid)

        elif content == PREFIX + "typing":
            threading.Thread(target=typier, args=(cid,), daemon=True).start()
            print_log(TOKEN, f"Typing 시작됨", cid)

        elif content.startswith(PREFIX + "nick "):
            if not gid:
                print_log(TOKEN, "서버(guild) 내에서만 사용 가능", cid)
                return
            new_nick = content[len(PREFIX + "nick "):].strip()
            if not new_nick:
                print_log(TOKEN, "닉네임이 비어 있음", cid)
                return
            try:
                r = tls_session.patch(
                    f"https://discord.com/api/v9/guilds/{gid}/members/@me",
                    headers=headers(TOKEN),
                    json={"nick": new_nick}
                )
                if r.status_code == 200:
                    print_log(TOKEN, f"닉네임 변경됨 → {new_nick}", cid)
                elif r.status_code == 429:
                    retry_after = r.json().get("retry_after", 5)
                    print_log(TOKEN, f"Rate Limited - {retry_after}s 대기", cid)
                    time.sleep(float(retry_after))
                else:
                    print_log(TOKEN, f"닉네임 변경 실패: {r.status_code}", cid)
            except Exception as e:
                print_log(TOKEN, f"닉네임 변경 예외: {e}", cid)

        elif content.startswith(PREFIX + "react "):
            parts = content.split()
            if len(parts) < 3:
                print("사용법: !f @유저ID 🖤 😂 👍")
                return
            target = parts[1].replace("<@", "").replace(">", "")
            emjs = parts[2:]
            if target.isdigit():
                emoji_map[target] = emjs
                print(f"🎯 {target} -> {', '.join(emjs)}")

        elif content.startswith(PREFIX + "react-stop"):
            emoji_map.clear()
            print("🎯 모든 자동 리액션 기능 중지됨")
            client.sendMessage(cid, "✅ 모든 자동 리액션 기능이 중지되었습니다.")

        elif content.startswith(PREFIX + "st "):
            msg_ = content[len(PREFIX + "st "):].strip()
            if not msg_:
                print_log(TOKEN, "방송 문구가 비어 있음", cid)
                return
            presence = {
                "op": 3,
                "d": {
                    "since": 0,
                    "activities": [{
                        "name": msg_,
                        "type": 1,
                        "url": "https://www.twitch.tv/sbxjsasdadjsdada"
                    }],
                    "status": "online",
                    "afk": False
                }
            }
            client.gateway.send(presence)
            print_log(TOKEN, f"🎥 방송 중 상태 변경됨: {msg_}", cid)

        if content.lower() == PREFIX + "ping":
                if not PING_MESSAGE:
                        print_log(TOKEN, "ping 메시지가 config.json에 설정되지 않았습니다.", cid)
                        return
                try:
                        res = client.sendMessage(cid, PING_MESSAGE)
                        msg_id = res.json()["id"]
                        time.sleep(3)
                        client.deleteMessage(cid, msg_id)
                        print_log(TOKEN, f"'ping' 감지 → 메시지를 3초 뒤 삭제", cid)
                except Exception as e:
                        print_log(TOKEN, f"ping 처리 실패: {e}", cid)

        if content.lower().startswith(PREFIX + "vfr"):
                try:
                        parts = content.split()
                        if len(parts) < 2:
                                client.sendMessage(cid, "채널 ID를 입력해 주세요.")
                                return

                        voice_channel_id = parts[1]

                        join_voice_channel(voice_channel_id)

                        start_live_stream()

                        print_log(TOKEN, f"'vfr' 명령어 감지 → 채널 {voice_channel_id} 통화방 입장 및 라이브 시작", cid)
                except Exception as e:
                        print_log(TOKEN, f"vfr 처리 실패: {e}", cid)

        elif content.lower().startswith(PREFIX + "ascii"):
                message = content[len(PREFIX + "ascii"):].strip()
                if not message:
                        client.sendMessage(cid, "변환할 메시지를 입력해주세요.")
                else:
                        import pyfiglet
                        ascii_art = pyfiglet.figlet_format(message)
                        response = f"```\n{ascii_art}\n```"
                        client.sendMessage(cid, response)
                        print_log(TOKEN, f"ascii art 변환됨", cid)

        elif content.lower().startswith(PREFIX + "b64"):
                import base64
                raw_message = content[len(PREFIX + "b64"):].strip()
                if not raw_message:
                        client.sendMessage(cid, "인코딩할 메시지를 입력해주세요.")
                else:
                        try:
                                encoded_bytes = base64.b64encode(raw_message.encode('utf-8'))
                                encoded_message = encoded_bytes.decode('utf-8')
                                client.sendMessage(cid, f"Base64 인코딩 결과:\n```\n{encoded_message}\n```")
                                print_log(TOKEN, "Base64 인코딩 성공", cid)
                        except Exception as e:
                                client.sendMessage(cid, f"인코딩 실패: {e}")
                                print_log(TOKEN, f"Base64 인코딩 실패: {e}", cid)


        elif content.lower().startswith(PREFIX + "dec-b64 "):
                import base64
                encoded_message = content[len(PREFIX + "dec-b64 "):].strip()
                if not encoded_message:
                        client.sendMessage(cid, "디코딩할 Base64 메시지를 입력해주세요.")
                else:
                        try:
                                missing_padding = len(encoded_message) % 4
                                if missing_padding:
                                        encoded_message += '=' * (4 - missing_padding)
                                decoded_bytes = base64.b64decode(encoded_message)
                                decoded_message = decoded_bytes.decode('utf-8')
                                client.sendMessage(cid, f"Base64 디코딩 결과:\n```\n{decoded_message}\n```")
                        except Exception as e:
                                client.sendMessage(cid, f"디코딩 실패: {e}")

        elif content.lower().startswith(PREFIX + "caesar"):
                shift = 3  # 본인이 설정가능 
                message = content[len(PREFIX + "caesar"):].strip()
                if not message:
                        client.sendMessage(cid, "암호화할 메시지를 입력해주세요.")
                else:
                        result = ""
                        for ch in message:
                                if 'A' <= ch <= 'Z':
                                        result += chr((ord(ch) - ord('A') + shift) % 26 + ord('A'))
                                elif 'a' <= ch <= 'z':
                                        result += chr((ord(ch) - ord('a') + shift) % 26 + ord('a'))
                                elif '0' <= ch <= '9':
                                        result += chr((ord(ch) - ord('0') + shift) % 10 + ord('0'))
                                elif '가' <= ch <= '힣':
                                        result += chr((ord(ch) - ord('가') + shift) % (ord('힣') - ord('가') + 1) + ord('가'))
                                else:
                                        result += ch
                        client.sendMessage(cid, f"카이사르 암호화 결과:\n```\n{result}\n```")
                        print_log(TOKEN, "카이사르 암호화 성공", cid)

        elif content.lower().startswith(PREFIX + "dec-caesar"):
                shift = 3  # shift = 3  # 본인이 설정가능 << 이거랑 동일해야함 !! 
                message = content[len(PREFIX + "dec-caesar"):].strip()
                if not message:
                        client.sendMessage(cid, "해독할 메시지를 입력해주세요.")
                else:
                        result = ""
                        for ch in message:
                                if 'A' <= ch <= 'Z':
                                        result += chr((ord(ch) - ord('A') - shift) % 26 + ord('A'))
                                elif 'a' <= ch <= 'z':
                                        result += chr((ord(ch) - ord('a') - shift) % 26 + ord('a'))
                                elif '0' <= ch <= '9':
                                        result += chr((ord(ch) - ord('0') - shift) % 10 + ord('0'))
                                elif '가' <= ch <= '힣':
                                        result += chr((ord(ch) - ord('가') - shift) % (ord('힣') - ord('가') + 1) + ord('가'))
                                else:
                                        result += ch
                        client.sendMessage(cid, f"카이사르 해독 결과:\n```\n{result}\n```")
                        print_log(TOKEN, "카이사르 해독 성공", cid)

        elif content == PREFIX + "bank":
            with open("config.json", "r", encoding="utf-8") as f:
                config_data = json.load(f)
            account = config_data.get("account", "")
            account_holder = config_data.get("account_holder", "")
            bank_msg = (
                "┏━━━━━━━━━━━━━━━┓\n"
                "┃ \n"
                f"**📑 계좌번호**: `{account}`\n\n"
                f"*** ┃ 📝 입금자명:  {account_holder}***\n"
                "┗━━━━━━━━━━━━━━━┛"
            )
            client.sendMessage(cid, bank_msg)
            return

        if content.startswith(PREFIX + "edit-bank "):
            args = content[len(PREFIX + "edit-bank "):].strip().split(" ", 1)
            if len(args) == 2:
                new_account = args[0].strip()
                new_holder = args[1].strip()
                global ACCOUNT, ACCOUNT_HOLDER
                with open("config.json", "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                config_data["account"] = new_account
                config_data["account_holder"] = new_holder
                with open("config.json", "w", encoding="utf-8") as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=4)
                ACCOUNT = new_account
                ACCOUNT_HOLDER = new_holder
                print_log(TOKEN, f"`계좌번호/예금주 변경됨 → {ACCOUNT} / {ACCOUNT_HOLDER}`", cid)
            else:
                print_log(TOKEN, "`사용법: edit-bank <새 계좌번호> <예금주>`", cid)
            return

        if content.startswith(PREFIX + "edit-coin "):
            args = content[len(PREFIX + "edit-coin "):].strip().split(" ", 1)
            if len(args) == 2:
                new_wallet = args[0].strip()
                new_type = args[1].strip()
                with open("config.json", "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                config_data["coin_wallet"] = new_wallet
                config_data["coin_type"] = new_type
                with open("config.json", "w", encoding="utf-8") as f:
                    json.dump(config_data, f, ensure_ascii=False, indent=4)
                print_log(TOKEN, f"`코인지갑/코인종류 변경됨 → {new_wallet} / {new_type}`", cid)
            else:
                print_log(TOKEN, "`사용법: edit-coin <코인지갑> <코인종류>`", cid)
            return

        if content == PREFIX + "coin":
            with open("config.json", "r", encoding="utf-8") as f:
                config_data = json.load(f)
            coin_wallet = config_data.get("coin_wallet", "")
            coin_type = config_data.get("coin_type", "")
            coin_msg = (
                "┏━━━━━━━━━━━━━━━┓\n"
                "┃ \n"
                f"**💰 코인지갑 **: `{coin_wallet}`\n\n"
                f"```┃ 🪙 코인종류: {coin_type}\n```"
                "┗━━━━━━━━━━━━━━━┛"
            )
            client.sendMessage(cid, coin_msg)
            return


        elif content.lower().startswith(PREFIX + "clear"):
                clear_message = ("ㅤ\n" * 400)
                client.sendMessage(cid, clear_message)

        elif content.lower().startswith(PREFIX + "ip-info "):
                ip = content[len(PREFIX + "ip-info "):].strip()
                if not ip:
                        client.sendMessage(cid, "`조회할 IP를 입력해주세요.`")
                        return

                try:
                        info_res = requests.get(f"https://ipinfo.io/{ip}/json")
                        if info_res.status_code != 200:
                                client.sendMessage(cid, "`IP 정보를 가져올 수 없습니다.`")
                                return
                        info_data = info_res.json()

                        vpn_res = requests.get(f"https://ipapi.co/{ip}/json/")
                        vpn_data = vpn_res.json()

                        is_proxy = vpn_data.get("proxy", False)
                        is_vpn = vpn_data.get("vpn", False)
                        is_tor = vpn_data.get("tor", False)
                        is_hosting = vpn_data.get("hosting", False)

                        message = (
                                f"📡 IP 정보 조회: `{info_data.get('ip', '정보 없음')}`\n"
                                f"🖥️ 호스트네임: {info_data.get('hostname', '정보 없음')}\n"
                                f"🌍 도시: {info_data.get('city', '정보 없음')}\n"
                                f"🗺️ 지역: {info_data.get('region', '정보 없음')}\n"
                                f"🌎 국가: {info_data.get('country', '정보 없음')}\n"
                                f"🏣 우편번호: {info_data.get('postal', '정보 없음')}\n"
                                f"📍 위치 (위도,경도): {info_data.get('loc', '정보 없음')}\n"
                                f"📶 통신사: {info_data.get('org', '정보 없음')}\n"
                                f"🕒 시간대: {info_data.get('timezone', '정보 없음')}\n"
                                f"\n"
                                f"🛡️ 프록시 사용: `{is_proxy}`\n"
                                f"🔐 VPN 사용: `{is_vpn}`\n"
                                f"🕳️ TOR 노드: `{is_tor}`\n"
                                f"🏢 호스팅 서버: `{is_hosting}`\n"
                                f"\n"
                                f"Powered by ipinfo.io & ipapi.co"
                        )

                        client.sendMessage(cid, message)

                except Exception as e:
                        client.sendMessage(cid, f"오류 발생: {e}")

        elif content.lower().startswith(PREFIX + "hypesquad "):
                try:
                        parts = content.split()
                        if len(parts) < 2:
                                client.sendMessage(cid, "`하이퍼스쿼드 종류를 입력해주세요. (bravery/brilliance/balance)`")
                                return

                        squad = parts[1].lower()
                        valid_squads = ["bravery", "brilliance", "balance"]

                        if squad not in valid_squads:
                                client.sendMessage(cid, "`올바른 종류를 입력해주세요. (bravery/brilliance/balance)`")
                                return

                        result = client.setHypesquad(squad)

                        if hasattr(result, 'status_code') and result.status_code == 204:
                                client.sendMessage(cid, f"하이퍼스쿼드 `{squad}`로 설정 완료!")
                        else:
                                status = getattr(result, 'status_code', '알 수 없음')
                                client.sendMessage(cid, f"`설정 실패. 상태코드: {status}`")

                except Exception:
                        pass  
        elif content.lower().startswith(PREFIX + "hypesquad-list"):
                client.sendMessage(cid,
                        "하이퍼스쿼드 종류 목록:\n"
                        "- `bravery`\n"
                        "- `brilliance`\n"
                        "- `balance`"
                )

        elif content.startswith(PREFIX + "pronoun "):
            parts = content.split(maxsplit=1)
            if len(parts) != 2 or not parts[1].strip():
                client.sendMessage(cid, f"사용법: {PREFIX}pronoun <새로운대명사>")
                return
            new_pronoun = parts[1].strip()
            patch_res = tls_session.patch(
                "https://discord.com/api/v9/users/@me/profile",
                headers=headers(TOKEN),
                json={"pronouns": new_pronoun}
            )
            if patch_res.status_code == 200:
                client.sendMessage(cid, f"대명사가 '{new_pronoun}'(으)로 변경되었습니다.")
            else:
                client.sendMessage(cid, f"대명사 변경 실패: {patch_res.status_code} {patch_res.text}")

        elif content == PREFIX + "pronoun-delete":
            patch_res = tls_session.patch(
                "https://discord.com/api/v9/users/@me/profile",
                headers=headers(TOKEN),
                json={"pronouns": ""}
            )
            if patch_res.status_code == 200:
                client.sendMessage(cid, "`대명사가 삭제되었습니다.`")
            else:
                client.sendMessage(cid, f"`대명사 삭제에 실패했습니다. (코드: {patch_res.status_code}) {patch_res.text}`")

        elif content.startswith(PREFIX + "bio "):
            parts = content.split(maxsplit=1)
            if len(parts) != 2 or not parts[1].strip():
                return
            new_bio = parts[1].strip()
            patch_res = tls_session.patch(
                "https://discord.com/api/v9/users/@me/profile",
                headers=headers(TOKEN),
                json={"bio": new_bio}
            )
            if patch_res.status_code == 200:
                client.sendMessage(cid, "`소개글이 변경되었습니다.`")
            else:
                client.sendMessage(cid, f"`소개글 변경에 실패했습니다. (코드: {patch_res.status_code}) {patch_res.text}`")

        elif content == PREFIX + "bio-delete":
            patch_res = tls_session.patch(
                "https://discord.com/api/v9/users/@me/profile",
                headers=headers(TOKEN),
                json={"bio": ""}
            )
            if patch_res.status_code == 200:
                client.sendMessage(cid, "`소개글이 삭제되었습니다.`")
            else:
                client.sendMessage(cid, f"`소개글 삭제에 실패했습니다. (코드: {patch_res.status_code}) {patch_res.text}`")

        elif content.lower().startswith(PREFIX + "search "):
                import wikipedia

                query = content[len(PREFIX + "search "):].strip()
                if not query:
                        client.sendMessage(cid, "### 검색어를 입력해주세요.")
                        return
                try:
                        summary = wikipedia.summary(query, sentences=2, auto_suggest=False)
                        page = wikipedia.page(query, auto_suggest=False)

                        max_len = 1000
                        if len(summary) > max_len:
                                summary = summary[:max_len].rstrip() + "..."

                        message = (
                                f"📚 {query} 검색 결과:\n{summary}\n\n"
                                f"🔗 더 보기: {page.url}"
                        )
                        client.sendMessage(cid, message)

                except wikipedia.exceptions.DisambiguationError as e:
                        options = e.options[:5]  
                        client.sendMessage(cid, "모호한 검색어입니다. 다음 중 하나를 선택해주세요:\n" + "\n".join(f"`{opt}`" for opt in options))

                except wikipedia.exceptions.PageError:
                        client.sendMessage(cid, "해당 검색어에 대한 결과가 없습니다.")
                except Exception as e:
                        client.sendMessage(cid, f"오류 발생: {e}")

        elif content.lower().startswith(PREFIX + "trans "):
                parts = content.split(" ")
                if len(parts) < 4:
                        client.sendMessage(cid, f"사용법: `{PREFIX}trans <원본언어> <대상언어> <내용>`")
                        return

                src_lang = parts[1]
                dest_lang = parts[2]
                text_to_translate = " ".join(parts[3:])

                try:
                        translated_text = GoogleTranslator(source=src_lang, target=dest_lang).translate(text_to_translate)
                        client.sendMessage(cid, f"📤 번역 결과:\n\n{translated_text}")
                except Exception as e:
                        client.sendMessage(cid, f"번역 중 오류 발생: {e}")

        elif content.lower().startswith(PREFIX + "trans-list"):
                try:
                        translator        = GoogleTranslator(source="auto", target="en")
                        languages         = translator.get_supported_languages(as_dict=True)

                        lang_kr           = {
                                "en": "영어",
                                "ko": "한국어",
                                "ja": "일본어",
                                "zh-CN": "중국어(간체)",
                                "zh-TW": "중국어(번체)",
                                "fr": "프랑스어",
                                "de": "독일어",
                                "es": "스페인어",
                                "ru": "러시아어",
                                "vi": "베트남어",
                                "id": "인도네시아어",
                                "th": "태국어",
                                "hi": "힌디어",
                        }

                        lang_list         = "\n".join(
                                f"`{name}` : {code} ({lang_kr[code]})"
                                for name, code in languages.items()
                                if code in lang_kr
                        )

                        client.sendMessage(cid, f"📖 지원하는 언어 코드 목록:\n\n{lang_list}")
                except Exception as e:
                        client.sendMessage(cid, f"언어 목록을 가져오는 중 오류 발생: {e}")

        elif content.lower().startswith(PREFIX + "pfp "):
                parts = content.split(" ", 1)
                if len(parts) < 2 or not parts[1].strip():
                        client.sendMessage(cid, "`유저를 멘션하거나 ID를 입력해주세요!`")
                        return

                raw_target = parts[1].strip()
                match = re.match(r"<@!?(\d+)>", raw_target)
                if match:
                        target_id = match.group(1)
                else:
                        target_id = raw_target

                try:
                        res = tls_session.get(
                                f"https://discord.com/api/v9/users/{target_id}",
                                headers=headers(TOKEN)
                        )
                        if res.status_code == 200:
                                user_data = res.json()
                                avatar = user_data.get("avatar")
                                if avatar:
                                        avatar_url = f"https://cdn.discordapp.com/avatars/{target_id}/{avatar}.png"
                                        client.sendMessage(cid, f"📸 프로필 사진: {avatar_url}")
                                else:
                                        client.sendMessage(cid, "❌ 해당 유저는 프로필 사진이 없음")
                        elif res.status_code == 429:
                                retry_after = res.json().get("retry_after", 5)
                                print_log(TOKEN, f"Rate Limited - {retry_after}s 대기", cid)
                                time.sleep(float(retry_after))
                        else:
                                client.sendMessage(cid, f"❌ 유저 정보 가져오기 실패 ({res.status_code})")
                except Exception as e:
                        print_log(TOKEN, f"프로필 가져오기 예외: {e}", cid)
        elif content.lower().startswith(PREFIX + "banner "):
                parts = content.split(" ", 1)
                if len(parts) < 2 or not parts[1].strip():
                        client.sendMessage(cid, "❌ 유저를 멘션하거나 ID를 입력해주세요!")
                        return

                raw_target = parts[1].strip()
                match = re.match(r"<@!?(\d+)>", raw_target)
                if match:
                        target_id = match.group(1)
                else:
                        target_id = raw_target

                try:
                        res = tls_session.get(
                                f"https://discord.com/api/v9/users/{target_id}",
                                headers=headers(TOKEN)
                        )
                        if res.status_code == 200:
                                user_data = res.json()
                                banner = user_data.get("banner")
                                banner_format = "gif" if banner and banner.startswith("a_") else "png"
                                if banner:
                                        banner_url = f"https://cdn.discordapp.com/banners/{target_id}/{banner}.{banner_format}"
                                        client.sendMessage(cid, f"🖼️ 배너 이미지: {banner_url}")
                                else:
                                        client.sendMessage(cid, "❌ 해당 유저는 배너가 없음")
                        elif res.status_code == 429:
                                retry_after = res.json().get("retry_after", 5)
                                print_log(TOKEN, f"Rate Limited - {retry_after}s 대기", cid)
                                time.sleep(float(retry_after))
                        else:
                                client.sendMessage(cid, f"❌ 유저 정보 가져오기 실패 ({res.status_code})")
                except Exception as e:
                        print_log(TOKEN, f"배너 가져오기 예외: {e}", cid)

        elif content.lower().startswith(PREFIX + "minesweeper"):
                size = 5
                parts = content.split()
                if len(parts) > 1 and parts[1].isdigit():
                        size = int(parts[1])
                game = generate_minesweeper(size)
                client.sendMessage(cid, f"지뢰찾기 (크기: {size}x{size}):\n{game}")

        elif content.lower().startswith(PREFIX + "8ball "):
                answers = [
                        "확실합니다", "네", "아니오", "아마도", "나중에 다시",
                        "집중해서 물어보세요", "예측 불가", "긍정적", "부정적"
                ]
                client.sendMessage(cid, f"🎱 {random.choice(answers)}")

        elif content.lower().startswith(PREFIX + "webhook-create"):
            is_owner = (uid == OWNER_ID)
            if not is_owner:
                return
            webhook = create_webhook(cid, TOKEN)
            if 'url' in webhook:
                client.sendMessage(cid, f"웹훅 생성됨: {webhook['url']}\n이름: {webhook['name']}")
            else:
                error_msg = webhook.get('message', '알 수 없는 오류')
                error_code = webhook.get('code', '코드 없음')
                client.sendMessage(cid, f"웹훅 생성 실패\n사유: {error_msg}\n코드: {error_code}")

        elif content.lower().startswith(PREFIX + "crypto "):
                coin = content[len(PREFIX + "crypto "):].strip().lower()
                price = get_crypto_price(coin)
                client.sendMessage(cid, price)

        elif content.lower().startswith(PREFIX + "webhook-spam "):
            try:
                parts = content.split(" ", 2)
                if len(parts) < 3:
                    client.sendMessage(cid, f"❌ 사용법: {PREFIX}webhook-spam <웹훅URL> <메시지>")
                    return
                webhook_url = parts[1].strip()
                spam_message = parts[2].strip()
                if not webhook_url.startswith("https://discord.com/api/webhooks/"):
                    client.sendMessage(cid, "❌ 올바른 웹훅 URL을 입력하세요.")
                    return

                def spam_webhook():
                    for i in range(30):
                        try:
                            resp = requests.post(webhook_url, json={"content": spam_message})
                            if resp.status_code != 204 and resp.status_code != 200:
                                print(f"[webhook-spam] {i+1}회 실패: {resp.status_code} {resp.text}")
                            time.sleep(0.3)
                        except Exception as e:
                            print(f"[webhook-spam] 예외 발생: {e}")

                threading.Thread(target=spam_webhook, daemon=True).start()
            except Exception as e:
                client.sendMessage(cid, f"❌ 웹훅 스팸 중 오류 발생: {e}")


        elif content.lower().startswith(PREFIX + "qr "):
                text_to_encode = content[len(PREFIX + "qr "):].strip()
                
                if not text_to_encode:
                    client.sendMessage(cid, "❌ QR 코드로 변환할 텍스트를 입력해주세요.")
                    return
                
                try:
                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(text_to_encode)
                    qr.make(fit=True)
                    
                    img = qr.make_image(fill_color="black", back_color="white")
                    
                    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
                        img.save(tmp_file.name)
                        tmp_file.flush()
                        client.sendFile(cid, tmp_file.name)
                    
                    client.sendMessage(cid, f"QR 코드 생성: {text_to_encode[:50]}...")
                    
                    print_log(TOKEN, f"QR 코드 생성: {text_to_encode}", cid)
                    
                except Exception as e:
                    client.sendMessage(cid, f"❌ QR 코드 생성 중 오류 발생: {str(e)}")
                    print_log(TOKEN, f"QR 코드 생성 실패: {e}", cid)

        elif content.lower().startswith(PREFIX + "tts "):
            try:
                from gtts import gTTS
                tts_text = content[len(PREFIX + "tts "):].strip()
                if not tts_text:
                    client.sendMessage(cid, "❌ 음성으로 변환할 텍스트를 입력해주세요.")
                    return
                tts = gTTS(tts_text, lang='ko') 
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                    tts.save(tmp_file.name)
                    tmp_file.flush()
                    client.sendFile(cid, tmp_file.name)
                print_log(TOKEN, f"TTS 생성: {tts_text}", cid)
            except Exception as e:
                client.sendMessage(cid, f"❌ TTS 생성 중 오류 발생: {e}")
                print_log(TOKEN, f"TTS 생성 실패: {e}", cid)

        elif content.startswith(PREFIX + "user-tts-stop"):
            if "user_tts_map" in globals() and cid in user_tts_map:
                user_tts_map.pop(cid, None)
                client.sendMessage(cid, "✅ user-tts 기능이 중지되었습니다.")
            else:
                client.sendMessage(cid, "user-tts 기능이 활성화되어 있지 않습니다.")

        elif content.startswith(PREFIX + "user-tts "):
            parts = content.split()
            if len(parts) < 2:
                client.sendMessage(cid, "❌ 유저를 멘션하거나 ID를 입력하세요.")
                return
            raw_target = parts[1].strip()
            match = re.match(r"<@!?(\d+)>", raw_target)
            if match:
                tts_target_id = match.group(1)
            elif raw_target.isdigit():
                tts_target_id = raw_target
            else:
                client.sendMessage(cid, "❌ 올바른 유저를 입력하세요.")
                return
            user_tts_map[cid] = tts_target_id

        if "user_tts_map" in globals() and cid in user_tts_map:
            tts_target_id = user_tts_map[cid]
            if uid == tts_target_id and content.strip():
                try:
                    from gtts import gTTS
                    tts = gTTS(content, lang='ko')
                    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp_file:
                        tts.save(tmp_file.name)
                        tmp_file.flush()
                        client.sendFile(cid, tmp_file.name)
                    client.deleteMessage(cid, mid)
                except Exception as e:
                    print_log(TOKEN, f"user-tts 실패: {e}", cid)


        elif content.startswith(PREFIX + "user-gn "):
            parts = content.split()
            if len(parts) < 2:
                client.sendMessage(cid, "❌ 유저를 멘션하거나 ID를 입력하세요.")
                return
            raw_target = parts[1].strip()
            match = re.match(r"<@!?(\d+)>", raw_target)
            if match:
                target_id = match.group(1)
            elif raw_target.isdigit():
                target_id = raw_target
            else:
                client.sendMessage(cid, "❌ 올바른 유저를 입력하세요.")
                return
            if "user_gn_map" not in globals():
                global user_gn_map
                user_gn_map = {}
            user_gn_map[cid] = target_id

        if "user_gn_map" in globals() and cid in user_gn_map:
            target_id = user_gn_map[cid]
            if uid == target_id and gid is None:
                try:
                    new_name = content[:90] if content else "이름없음"
                    tls_session.patch(
                        f"https://discord.com/api/v9/channels/{cid}",
                        headers=headers(TOKEN),
                        json={"name": new_name}
                    )
                    client.deleteMessage(cid, mid)
                    print_log(TOKEN, f"user-gn: {new_name} (메시지 삭제)", cid)
                except Exception as e:
                    print_log(TOKEN, f"user-gn 실패: {e}", cid)

        elif content.startswith(PREFIX + "user-gn-stop"):
            if "user_gn_map" in globals() and cid in user_gn_map:
                user_gn_map.pop(cid, None)
                client.sendMessage(cid, "✅ user-gn 기능이 중지되었습니다.")
            else:
                client.sendMessage(cid, "user-gn 기능이 활성화되어 있지 않습니다.")
    
        elif content == PREFIX + "crypto-list":
            msg = (
                "[지원 코인 종류 예시] <코인 가격 볼때는 줄여서 사용>\n"
                "btc : Bitcoin\n"
                "eth : Ethereum\n"
                "doge : Dogecoin\n"
                "sol : Solana\n"
                "xrp : Ripple\n"
                "ada : Cardano\n"
                "matic : Polygon\n"
                "trx : Tron\n"
                "ltc : Litecoin\n"
                "bch : Bitcoin Cash\n"
                "dot : Polkadot\n"
                "avax : Avalanche\n"
                "link : Chainlink\n"
                "atom : Cosmos\n"
                "etc : Ethereum Classic\n"
                "xlm : Stellar\n"
                "eos : EOS\n"
                "sand : The Sandbox\n"
                "ape : ApeCoin\n"
                "arb : Arbitrum\n"
                "op : Optimism\n"
                "\n예시: {0}crypto btc".format(PREFIX)
            )
            client.sendMessage(cid, msg)

        elif content.lower() == PREFIX + "serverinfo":
            if not gid:
                client.sendMessage(cid, "❌ 서버(길드) 채널에서만 사용 가능합니다.")
                return
            try:
                res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}",
                    headers=headers(TOKEN)
                )
                guild = res.json()
                member_count = guild.get("member_count") or guild.get("approximate_member_count")
                if member_count is None:
                    preview = tls_session.get(
                        f"https://discord.com/api/v9/guilds/{gid}/preview",
                        headers=headers(TOKEN)
                    )
                    if preview.status_code == 200:
                        member_count = preview.json().get("approximate_member_count", "알 수 없음")
                    else:
                        member_count = "알 수 없음"
                name = guild.get("name", "알 수 없음")
                owner_id = guild.get("owner_id", "알 수 없음")
                region = guild.get("region", "알 수 없음")
                created_at = guild.get("id", "")[:8]
                icon = guild.get("icon")
                if icon:
                    icon_ext = "gif" if str(icon).startswith("a_") else "png"
                    icon_url = f"https://cdn.discordapp.com/icons/{gid}/{icon}.{icon_ext}"
                else:
                    icon_url = "없음"

                banner = guild.get("banner")
                if banner:
                    banner_ext = "gif" if str(banner).startswith("a_") else "png"
                    banner_url = f"https://cdn.discordapp.com/banners/{gid}/{banner}.{banner_ext}?size=4096"
                else:
                    banner_url = "없음"
                description = guild.get("description", "없음")

                channels_res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/channels",
                    headers=headers(TOKEN)
                )
                channels = channels_res.json() if channels_res.status_code == 200 else []
                channel_count = len(channels)

                roles_res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/roles",
                    headers=headers(TOKEN)
                )
                roles = roles_res.json() if roles_res.status_code == 200 else []
                role_count = len(roles)

                emojis_res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/emojis",
                    headers=headers(TOKEN)
                )
                emojis = emojis_res.json() if emojis_res.status_code == 200 else []
                emoji_count = len(emojis)

                features_raw = guild.get("features", [])
                feature_map = {
                    "COMMUNITY": "커뮤니티",
                    "ANIMATED_ICON": "움직이는 아이콘",
                    "BANNER": "배너",
                    "INVITE_SPLASH": "초대 스플래시",
                    "NEWS": "공지 채널",
                    "PARTNERED": "파트너 서버",
                    "VERIFIED": "공식 인증 서버",
                    "VANITY_URL": "커스텀 초대링크",
                    "WELCOME_SCREEN_ENABLED": "환영 화면",
                    "MEMBER_VERIFICATION_GATE_ENABLED": "멤버 인증",
                    "PREVIEW_ENABLED": "프리뷰",
                    "ROLE_ICONS": "역할 아이콘",
                    "TICKETED_EVENTS_ENABLED": "유료 이벤트",
                    "MONETIZATION_ENABLED": "수익화",
                    "MORE_STICKERS": "스티커 확장",
                    "PRIVATE_THREADS": "비공개 스레드",
                    "THREADS_ENABLED": "스레드",
                    "DIRECTORY_ENABLED": "디렉토리",
                    "HUB": "허브",
                    "ANIMATED_BANNER": "움직이는 배너",
                    "SEVEN_DAY_THREAD_ARCHIVE": "7일 스레드 보관",
                    "THREE_DAY_THREAD_ARCHIVE": "3일 스레드 보관",
                    "MEMBER_LIST_DISABLED": "멤버 리스트 비활성화",
                }
                features_kr = [feature_map.get(f, f) for f in features_raw]
                features = ", ".join(features_kr) if features_kr else "없음"

                msg = (
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"**📊 서버 정보**\n"
                    f"━━━━━━━━━━━━━━━━━━\n"
                    f"**이름:** {name}\n"
                    f"**ID:** `{gid}`\n"
                    f"**소유자 `{owner_id}`\n"
                    f"**설명:** {description}\n"
                    f"**멤버 수:** {member_count}\n"
                    f"**채널 수:** {channel_count}\n"
                    f"**역할 수:** {role_count}\n"
                    f"**이모지 수:** {emoji_count}\n"
                    f"**아이콘:** {icon_url}\n"
                    f"**배너:** {banner_url}\n"
                    f"━━━━━━━━━━━━━━━━━━"
                )
                client.sendMessage(cid, msg)
            except Exception as e:
                client.sendMessage(cid, f"❌ 서버 정보 조회 중 오류 발생: {e}")

        elif content.lower().startswith(PREFIX + "partner-set "):
            parts = content.split()
            if len(parts) < 2 or not parts[1].isdigit():
                client.sendMessage(cid, f"❌ 사용법: {PREFIX}partner-set <횟수>")
                return
            count = int(parts[1])
            if count < 1 or count > 24:
                client.sendMessage(cid, "❌ 1~24 사이의 횟수만 지정 가능합니다.")
                return
            partner_auto_send[cid] = True
            auto_message = config.get("partner_message", "파트너 홍보 메시지입니다!")
            client.sendMessage(cid, f"✅ 하루 {count}회 자동 파트너 메시지 전송 시작!")
            try:
                client.deleteMessage(cid, mid)
            except Exception:
                pass
            schedule_partner_message(client, cid, count, auto_message)

        elif content.lower().startswith(PREFIX + "partner-stop"):
            partner_auto_send[cid] = False
            client.sendMessage(cid, "✅ 파트너 자동 메시지 전송 중지됨.")

        elif content.lower().startswith(PREFIX + "vfr "):
            parts = content.split()
            if len(parts) < 2 or not gid:
                client.sendMessage(cid, "❌ 사용법: {0}vfr <음성채널ID>".format(PREFIX))
                return
            voice_channel_id = parts[1]

            try:
                client.gateway.send({
                    "op": 4,
                    "d": {
                        "guild_id": gid,
                        "channel_id": voice_channel_id,
                        "self_mute": False,
                        "self_deaf": False
                    }
                })
                time.sleep(1)
                client.gateway.send({
                    "op": 18,
                    "d": {
                        "type": "guild",
                        "guild_id": gid,
                        "channel_id": voice_channel_id,
                        "preferred_region": None
                    }
                })
                client.sendMessage(cid, f"✅ 음성채널({voice_channel_id}) 입장 및 라이브 시작 시도!")
            except Exception as e:
                client.sendMessage(cid, f"❌ vfr 오류: {e}")

        elif content.lower().startswith(PREFIX + "vf-sound "):
            parts = content.split()
            if len(parts) < 2 or not gid:
                client.sendMessage(cid, f"❌ 사용법: {PREFIX}vf-sound <음성채널ID>")
                return
            voice_channel_id = parts[1]
            try:
                client.gateway.send({
                    "op": 4,
                    "d": {
                        "guild_id": gid,
                        "channel_id": voice_channel_id,
                        "self_mute": False,
                        "self_deaf": False
                    }
                })
                time.sleep(2)
                res = requests.get(
                    "https://canary.discord.com/api/v9/soundboard-default-sounds",
                    headers={"Authorization": TOKEN}
                )
                if res.status_code != 200:
                    client.sendMessage(cid, "❌ 사운드보드 목록을 가져올 수 없습니다.")
                    return
                sounds = res.json()
                if not sounds:
                    client.sendMessage(cid, "❌ 사용할 수 있는 사운드보드 사운드가 없습니다.")
                    return

                def play_soundboard():
                    while True:
                        sound = random.choice(sounds)
                        payload = {
                            "emoji_id": None,
                            "emoji_name": sound.get("emoji_name"),
                            "sound_id": sound.get("sound_id"),
                        }
                        resp = requests.post(
                            f"https://canary.discord.com/api/v9/channels/{voice_channel_id}/send-soundboard-sound",
                            headers={"Authorization": TOKEN, "Content-Type": "application/json"},
                            json=payload
                        )
                        if resp.status_code == 204:
                            print_log(TOKEN, f"사운드보드 재생: {sound.get('name')}", cid)
                        elif resp.status_code == 429:
                            retry_after = resp.json().get("retry_after", 1)
                            print_log(TOKEN, f"사운드보드 레이트리밋: {retry_after}s 대기", cid)
                            time.sleep(float(retry_after))
                        else:
                            print_log(TOKEN, f"사운드보드 실패: {resp.status_code}", cid)
                        time.sleep(random.uniform(1.2, 2.5)) 

                threading.Thread(target=play_soundboard, daemon=True).start()
            except Exception as e:
                client.sendMessage(cid, f"❌ 사운드보드 오류: {e}")
        elif content.startswith(PREFIX + "owner-id-add "):
            new_owner_id = content[len(PREFIX + "owner_id-add "):].strip()
            if new_owner_id:
                with open("config.json", "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                owner_ids = config_data.get("owner_id", [])
                if isinstance(owner_ids, str):
                    owner_ids = [owner_ids]
                if new_owner_id not in owner_ids:
                    owner_ids.append(new_owner_id)
                    config_data["owner_id"] = owner_ids
                    with open("config.json", "w", encoding="utf-8") as f:
                        json.dump(config_data, f, ensure_ascii=False, indent=4)
                    print_log(TOKEN, f"새 오너 아이디 추가됨 → {new_owner_id}", cid)
                else:
                    print_log(TOKEN, "이미 등록된 오너 아이디입니다.", cid)
            else:
                print_log(TOKEN, "추가할 오너 아이디를 입력하세요.", cid)
            return
        
        elif content.startswith(PREFIX + "owner-id-del "):
            del_owner_id = content[len(PREFIX + "owner-id-del "):].strip()
            if del_owner_id:
                with open("config.json", "r", encoding="utf-8") as f:
                    config_data = json.load(f)
                owner_ids = config_data.get("owner_id", [])
                if isinstance(owner_ids, str):
                    owner_ids = [owner_ids]
                if del_owner_id in owner_ids:
                    if len(owner_ids) == 1:
                        print_log(TOKEN, "오너 아이디가 1개만 남아있어 삭제할 수 없습니다.", cid)
                    else:
                        owner_ids.remove(del_owner_id)
                        config_data["owner_id"] = owner_ids
                        with open("config.json", "w", encoding="utf-8") as f:
                            json.dump(config_data, f, ensure_ascii=False, indent=4)
                        print_log(TOKEN, f"오너 아이디 삭제됨 → {del_owner_id}", cid)
                else:
                    print_log(TOKEN, "해당 오너 아이디가 존재하지 않습니다.", cid)
            else:
                print_log(TOKEN, "삭제할 오너 아이디를 입력하세요.", cid)
            return

# ...on_message 내부...

        elif content == PREFIX + "delete-channel-all":
            if not gid:
                client.sendMessage(cid, "❌ 서버(길드) 채널에서만 사용 가능합니다.")
                return
            # 명령 메시지도 삭제
            try:
                client.deleteMessage(cid, mid)
            except Exception:
                pass
            confirm_msg = client.sendMessage(cid, "⚠️ 정말로 모든 채널을 삭제할까요? (y/n)")
            confirm_msg_id = None
            if isinstance(confirm_msg, dict):
                confirm_msg_id = confirm_msg.get("id")

            def wait_for_confirm():
                for _ in range(30):  # 30초 대기
                    time.sleep(1)
                    messages = client.getMessages(cid, num=1)
                    try:
                        messages = messages.json()
                    except Exception:
                        messages = []
                    if messages:
                        last_msg = messages[0]
                        if last_msg['author']['id'] == uid:
                            reply = last_msg['content'].strip().lower()
                            # 확인 메시지와 답변 메시지 모두 삭제
                            if confirm_msg_id:
                                client.deleteMessage(cid, confirm_msg_id)
                            client.deleteMessage(cid, last_msg['id'])
                            if reply == "y":
                                # 채널 삭제 실행
                                try:
                                    res = tls_session.get(
                                        f"https://discord.com/api/v9/guilds/{gid}/channels",
                                        headers=headers(TOKEN)
                                    )
                                    if res.status_code != 200:
                                        client.sendMessage(cid, "❌ 채널 목록을 가져올 수 없습니다.")
                                        return
                                    channels = res.json()
                                    deleted = 0
                                    for ch in channels:
                                        ch_id = ch.get("id")
                                        ch_name = ch.get("name", "")
                                        del_res = tls_session.delete(
                                            f"https://discord.com/api/v9/channels/{ch_id}",
                                            headers=headers(TOKEN)
                                        )
                                        if del_res.status_code in (200, 204):
                                            deleted += 1
                                            print_log(TOKEN, f"채널 삭제됨: {ch_name} ({ch_id})", cid)
                                        else:
                                            print_log(TOKEN, f"채널 삭제 실패: {ch_name} ({ch_id})", cid)
                                        time.sleep(random.uniform(0.3, 0.8))
                                    client.sendMessage(cid, f"✅ {deleted}개 채널 삭제 완료")
                                except Exception as e:
                                    client.sendMessage(cid, f"❌ 채널 삭제 중 오류: {e}")
                                return
                            elif reply == "n":
                                client.sendMessage(cid, "❌ 삭제가 취소되었습니다.")
                                return
                client.sendMessage(cid, "⏰ 30초 내에 응답이 없어 취소되었습니다.")

            threading.Thread(target=wait_for_confirm, daemon=True).start()

        elif content.startswith(PREFIX + "delete-channel "):
            parts = content.split()
            if len(parts) != 2:
                client.sendMessage(cid, "❌ 사용법: " + PREFIX + "delete-channel <채널아이디>")
                return
            channel_id = parts[1]
            res = tls_session.delete(
                f"https://discord.com/api/v9/channels/{channel_id}",
                headers=headers(TOKEN)
            )
            if res.status_code in (200, 204):
                client.sendMessage(cid, f"✅ 채널 {channel_id} 삭제 완료")
            elif res.status_code == 403:
                client.sendMessage(cid, f"❌ 권한이 없습니다.")
            elif res.status_code == 404:
                client.sendMessage(cid, f"❌ 채널을 찾을 수 없습니다.")
            else:
                client.sendMessage(cid, f"❌ 삭제 실패: {res.status_code} {res.text}")

# ...on_message 내부...

        elif content.startswith(PREFIX + "add-channel "):
            parts = content.split()
            if len(parts) < 3:
                client.sendMessage(cid, f"❌ 사용법: {PREFIX}add-channel <횟수> <채널이름>")
                return
            try:
                count = int(parts[1])
            except ValueError:
                client.sendMessage(cid, "❌ 횟수는 숫자로 입력하세요.")
                return
            channel_name = " ".join(parts[2:])
            if not gid:
                client.sendMessage(cid, "❌ 서버(길드) 채널에서만 사용 가능합니다.")
                return
            created = 0
            for _ in range(count):
                payload = {
                    "name": channel_name,
                    "type": 0  # 0: 텍스트 채널
                }
                res = tls_session.post(
                    f"https://discord.com/api/v9/guilds/{gid}/channels",
                    headers=headers(TOKEN),
                    json=payload
                )
                if res.status_code == 201:
                    created += 1
                time.sleep(random.uniform(0.3, 0.8))
            client.sendMessage(cid, f"✅ {created}개 채널 생성 완료")

        elif content == PREFIX + "delete-role-all":
            if not gid:
                client.sendMessage(cid, " 서버(길드) 채널에서만 사용 가능합니다.")
                return
            try:
                client.deleteMessage(cid, mid)
            except Exception:
                pass
            confirm_msg = client.sendMessage(cid, "정말로 모든 역할을 삭제할까요? (y/n)")
            confirm_msg_id = None
            if isinstance(confirm_msg, dict):
                confirm_msg_id = confirm_msg.get("id")

            def wait_for_role_confirm():
                for _ in range(30):  
                    time.sleep(1)
                    messages = client.getMessages(cid, num=1)
                    try:
                        messages = messages.json()
                    except Exception:
                        messages = []
                    if messages:
                        last_msg = messages[0]
                        if last_msg['author']['id'] == uid:
                            reply = last_msg['content'].strip().lower()
                            # 확인 메시지와 답변 메시지 모두 삭제
                            if confirm_msg_id:
                                client.deleteMessage(cid, confirm_msg_id)
                            client.deleteMessage(cid, last_msg['id'])
                            if reply == "y":
                                # 역할 삭제 실행
                                try:
                                    res = tls_session.get(
                                        f"https://discord.com/api/v9/guilds/{gid}/roles",
                                        headers=headers(TOKEN)
                                    )
                                    if res.status_code != 200:
                                        client.sendMessage(cid, "역할 목록을 가져올 수 없습니다.")
                                        return
                                    roles = res.json()
                                    deleted = 0
                                    for role in roles:
                                        role_id = role.get("id")
                                        role_name = role.get("name", "")
                                        del_res = tls_session.delete(
                                            f"https://discord.com/api/v9/guilds/{gid}/roles/{role_id}",
                                            headers=headers(TOKEN)
                                        )
                                        if del_res.status_code in (200, 204):
                                            deleted += 1
                                            print_log(TOKEN, f"역할 삭제됨: {role_name} ({role_id})", cid)
                                        else:
                                            print_log(TOKEN, f"역할 삭제 실패: {role_name} ({role_id})", cid)
                                        time.sleep(random.uniform(0.3, 0.8))
                                    client.sendMessage(cid, f"{deleted}개 역할 삭제 완료")
                                except Exception as e:
                                    client.sendMessage(cid, f"역할 삭제 중 오류: {e}")
                                return
                            elif reply == "n":
                                client.sendMessage(cid, "삭제가 취소되었습니다.")
                                return
                client.sendMessage(cid, "⏰ 30초 내에 응답이 없어 취소되었습니다.")

            threading.Thread(target=wait_for_role_confirm, daemon=True).start()

        elif content.startswith(PREFIX + "add-role "):
            parts = content.split()
            if len(parts) < 3:
                client.sendMessage(cid, f"사용법: {PREFIX}add-role <횟수> <역할이름>")
                return
            try:
                count = int(parts[1])
            except ValueError:
                client.sendMessage(cid, "횟수는 숫자로 입력하세요.")
                return
            role_name = " ".join(parts[2:])
            if not gid:
                client.sendMessage(cid, "서버(길드) 채널에서만 사용 가능합니다.")
                return
            created = 0
            for _ in range(count):
                payload = {
                    "name": role_name
                }
                res = tls_session.post(
                    f"https://discord.com/api/v9/guilds/{gid}/roles",
                    headers=headers(TOKEN),
                    json=payload
                )
                if res.status_code == 200 or res.status_code == 201:
                    created += 1
                time.sleep(random.uniform(0.3, 0.8))
            client.sendMessage(cid, f"{created}개 역할 생성 완료")

        elif content.startswith(PREFIX + "kick "):
            if not gid:
                client.sendMessage(cid, "서버(길드) 채널에서만 사용 가능합니다.")
                return
            parts = content.split()
            if len(parts) != 2:
                client.sendMessage(cid, f"사용법: {PREFIX}kick <사용자아이디>")
                return
            target_id = parts[1]
            if target_id == uid:
                client.sendMessage(cid, "자기 자신은 추방할 수 없습니다.")
                return
            # 명령 메시지 삭제
            try:
                client.deleteMessage(cid, mid)
            except Exception:
                pass
            kick_res = tls_session.delete(
                f"https://discord.com/api/v9/guilds/{gid}/members/{target_id}",
                headers=headers(TOKEN)
            )
            if kick_res.status_code in (200, 204):
                msg = client.sendMessage(cid, f"{target_id} 추방 완료")
                # 메시지가 전송될 때까지 잠깐 대기 후 삭제 시도
                msg_id = None
                if isinstance(msg, dict):
                    msg_id = msg.get("id")
                if not msg_id:
                    # 메시지 ID를 못 받았으면 최근 메시지에서 찾기
                    time.sleep(0.5)
                    messages = client.getMessages(cid, num=1)
                    try:
                        messages = messages.json()
                        if messages and messages[0]['author']['id'] == uid and target_id in messages[0]['content']:
                            msg_id = messages[0]['id']
                    except Exception:
                        pass
                if msg_id:
                    time.sleep(0.5)
                    try:
                        client.deleteMessage(cid, msg_id)
                    except Exception:
                        pass
            elif kick_res.status_code == 403:
                client.sendMessage(cid, f"권한이 없습니다.")
            elif kick_res.status_code == 404:
                client.sendMessage(cid, f"사용자를 찾을 수 없습니다.")
            else:
                client.sendMessage(cid, f"추방 실패: {kick_res.status_code} {kick_res.text}")

        elif content.startswith(PREFIX + "ban "):
            if not gid:
                client.sendMessage(cid, "서버(길드) 채널에서만 사용 가능합니다.")
                return
            parts = content.split()
            if len(parts) != 2:
                client.sendMessage(cid, f"사용법: {PREFIX}ban <사용자아이디>")
                return
            target_id = parts[1]
            if target_id == uid:
                client.sendMessage(cid, "자기 자신은 벤할 수 없습니다.")
                return
            # 명령 메시지 삭제
            try:
                client.deleteMessage(cid, mid)
            except Exception:
                pass
            ban_res = tls_session.put(
                f"https://discord.com/api/v9/guilds/{gid}/bans/{target_id}",
                headers=headers(TOKEN),
                json={}
            )
            if ban_res.status_code in (200, 201, 204):
                msg = client.sendMessage(cid, f"{target_id} 벤 완료")
                # 메시지가 전송될 때까지 잠깐 대기 후 삭제 시도
                msg_id = None
                if isinstance(msg, dict):
                    msg_id = msg.get("id")
                if not msg_id:
                    time.sleep(0.5)
                    messages = client.getMessages(cid, num=1)
                    try:
                        messages = messages.json()
                        if messages and messages[0]['author']['id'] == uid and target_id in messages[0]['content']:
                            msg_id = messages[0]['id']
                    except Exception:
                        pass
                if msg_id:
                    time.sleep(0.5)
                    try:
                        client.deleteMessage(cid, msg_id)
                    except Exception:
                        pass
            elif ban_res.status_code == 403:
                client.sendMessage(cid, f"권한이 없습니다.")
            elif ban_res.status_code == 404:
                client.sendMessage(cid, f"사용자를 찾을 수 없습니다.")
            else:
                client.sendMessage(cid, f"벤 실패: {ban_res.status_code} {ban_res.text}")


        elif content.startswith(PREFIX + "unban "):
            if not gid:
                client.sendMessage(cid, "서버(길드) 채널에서만 사용 가능합니다.")
                return
            parts = content.split()
            if len(parts) != 2:
                client.sendMessage(cid, f"사용법: {PREFIX}unban <사용자아이디>")
                return
            target_id = parts[1]
            # 명령 메시지 삭제
            try:
                client.deleteMessage(cid, mid)
            except Exception:
                pass
            unban_res = tls_session.delete(
                f"https://discord.com/api/v9/guilds/{gid}/bans/{target_id}",
                headers=headers(TOKEN)
            )
            if unban_res.status_code in (200, 204):
                msg = client.sendMessage(cid, f"{target_id} 벤 해제 완료")
                # 메시지가 전송될 때까지 잠깐 대기 후 삭제 시도
                msg_id = None
                if isinstance(msg, dict):
                    msg_id = msg.get("id")
                if not msg_id:
                    time.sleep(0.5)
                    messages = client.getMessages(cid, num=1)
                    try:
                        messages = messages.json()
                        if messages and messages[0]['author']['id'] == uid and target_id in messages[0]['content']:
                            msg_id = messages[0]['id']
                    except Exception:
                        pass
                if msg_id:
                    time.sleep(0.5)
                    try:
                        client.deleteMessage(cid, msg_id)
                    except Exception:
                        pass
            elif unban_res.status_code == 403:
                client.sendMessage(cid, f"권한이 없습니다.")
            elif unban_res.status_code == 404:
                client.sendMessage(cid, f"사용자를 찾을 수 없습니다.")
            else:
                client.sendMessage(cid, f"벤 해제 실패: {unban_res.status_code} {unban_res.text}")

        elif content == PREFIX + "unban-all":
            if not gid:
                client.sendMessage(cid, "서버(길드) 채널에서만 사용 가능합니다.")
                return
            # 명령 메시지 삭제
            try:
                client.deleteMessage(cid, mid)
            except Exception:
                pass
            try:
                res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/bans",
                    headers={
                        "Authorization": TOKEN,
                        "User-Agent": "Mozilla/5.0"
                        # "Content-Type"은 넣지 않음!
                    }
                )
                if res.status_code != 200:
                    client.sendMessage(cid, f"벤 목록을 가져올 수 없습니다. ({res.status_code})")
                    return
                bans = res.json()
                unbanned = 0
                for ban in bans:
                    user = ban.get("user", {})
                    user_id = user.get("id")
                    user_name = user.get("username", "")
                    # Content-Type 없이, data/json 없이!
                    unban_res = tls_session.delete(
                        f"https://discord.com/api/v9/guilds/{gid}/bans/{user_id}",
                        headers={
                            "Authorization": TOKEN,
                            "User-Agent": "Mozilla/5.0"
                        }
                    )
                    if unban_res.status_code in (200, 204):
                        unbanned += 1
                        print_log(TOKEN, f"벤 해제됨: {user_name} ({user_id})", cid)
                    else:
                        print_log(
                            TOKEN,
                            f"벤 해제 실패: {user_name} ({user_id}) - {unban_res.status_code} {unban_res.text}",
                            cid
                        )
                    time.sleep(random.uniform(0.3, 0.8))
                client.sendMessage(cid, f"{unbanned}명 벤 해제 완료")
            except Exception as e:
                client.sendMessage(cid, f"벤 해제 중 오류: {e}")
        elif content.startswith(PREFIX + "slow-time-all "):
            if not gid:
                client.sendMessage(cid, "서버(길드) 채널에서만 사용 가능합니다.")
                return
            parts = content.split()
            if len(parts) != 2 or not parts[1].isdigit():
                client.sendMessage(cid, f"사용법: {PREFIX}slow-time-all <초(0~21600)>")
                return
            slow_time = int(parts[1])
            if slow_time < 0 or slow_time > 21600:
                client.sendMessage(cid, "슬로우타임은 0~21600초(6시간) 사이로만 설정 가능합니다.")
                return
            try:
                res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/channels",
                    headers=headers(TOKEN)
                )
                if res.status_code != 200:
                    client.sendMessage(cid, "채널 목록을 가져올 수 없습니다.")
                    return
                channels = res.json()
                changed = 0
                for ch in channels:
                    ch_id = ch.get("id")
                    if ch.get("type") != 0:  # 텍스트 채널만
                        continue
                    patch_res = tls_session.patch(
                        f"https://discord.com/api/v9/channels/{ch_id}",
                        headers=headers(TOKEN),
                        json={"rate_limit_per_user": slow_time}
                    )
                    if patch_res.status_code == 200:
                        changed += 1
                        print_log(TOKEN, f"슬로우타임 {slow_time}초 적용: {ch.get('name', '')} ({ch_id})", cid)
                    else:
                        print_log(TOKEN, f"슬로우타임 실패: {ch.get('name', '')} ({ch_id}) - {patch_res.status_code}", cid)
                    time.sleep(random.uniform(0.5, 1.0))
                client.sendMessage(cid, f"{changed}개 채널에 {slow_time}초 슬로우타임 적용 완료")
            except Exception as e:
                client.sendMessage(cid, f"슬로우타임 적용 중 오류: {e}")

        elif content == PREFIX + "slow-time-delete-all":
            if not gid:
                client.sendMessage(cid, "서버(길드) 채널에서만 사용 가능합니다.")
                return
            try:
                res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/channels",
                    headers=headers(TOKEN)
                )
                if res.status_code != 200:
                    client.sendMessage(cid, "채널 목록을 가져올 수 없습니다.")
                    return
                channels = res.json()
                changed = 0
                for ch in channels:
                    ch_id = ch.get("id")
                    if ch.get("type") != 0:  # 텍스트 채널만
                        continue
                    patch_res = tls_session.patch(
                        f"https://discord.com/api/v9/channels/{ch_id}",
                        headers=headers(TOKEN),
                        json={"rate_limit_per_user": 0}
                    )
                    if patch_res.status_code == 200:
                        changed += 1
                        print_log(TOKEN, f"슬로우타임 해제: {ch.get('name', '')} ({ch_id})", cid)
                    else:
                        print_log(TOKEN, f"슬로우타임 해제 실패: {ch.get('name', '')} ({ch_id}) - {patch_res.status_code}", cid)
                    time.sleep(random.uniform(0.3, 0.8))
                client.sendMessage(cid, f"✅ {changed}개 채널 슬로우타임 해제 완료")
            except Exception as e:
                client.sendMessage(cid, f"슬로우타임 해제 중 오류: {e}")
        elif content.startswith(PREFIX + "slow-time "):
            parts = content.split()
            if len(parts) != 3 or not parts[2].isdigit():
                client.sendMessage(cid, f"사용법: {PREFIX}slow-time <채널아이디> <초(0~21600)>")
                return
            channel_id = parts[1]
            slow_time = int(parts[2])
            if slow_time < 0 or slow_time > 21600:
                client.sendMessage(cid, "슬로우타임은 0~21600초(6시간) 사이로만 설정 가능합니다.")
                return
            patch_res = tls_session.patch(
                f"https://discord.com/api/v9/channels/{channel_id}",
                headers=headers(TOKEN),
                json={"rate_limit_per_user": slow_time}
            )
            if patch_res.status_code == 200:
                client.sendMessage(cid, f"채널 {channel_id}에 {slow_time}초 슬로우타임 적용 완료")
            else:
                client.sendMessage(cid, f"슬로우타임 적용 실패: {patch_res.status_code} {patch_res.text}")
        elif content.startswith(PREFIX + "slow-time-delete "):
            parts = content.split()
            if len(parts) != 2:
                client.sendMessage(cid, f"사용법: {PREFIX}slow-time-delete <채널아이디>")
                return
            channel_id = parts[1]
            patch_res = tls_session.patch(
                f"https://discord.com/api/v9/channels/{channel_id}",
                headers=headers(TOKEN),
                json={"rate_limit_per_user": 0}
            )
            if patch_res.status_code == 200:
                client.sendMessage(cid, f" 채널 {channel_id} 슬로우타임 해제 완료")
            else:
                client.sendMessage(cid, f" 슬로우타임 해제 실패: {patch_res.status_code} {patch_res.text}")

        elif content.startswith(PREFIX + "to "):
            parts = content.split()
            if len(parts) != 3 or not parts[2].isdigit():
                client.sendMessage(cid, f" 사용법: {PREFIX}to <사용자아이디> <초(최대 2419200)>")
                return
            target_id = parts[1]
            timeout_seconds = int(parts[2])
            if timeout_seconds < 1 or timeout_seconds > 2419200:
                client.sendMessage(cid, " 타임아웃은 1초~2419200초(28일) 사이로만 설정 가능합니다.")
                return
            until_timestamp = int(time.time()) + timeout_seconds
            patch_res = tls_session.patch(
                f"https://discord.com/api/v9/guilds/{gid}/members/{target_id}",
                headers=headers(TOKEN),
                json={"communication_disabled_until": time.strftime("%Y-%m-%dT%H:%M:%S.000+00:00", time.gmtime(until_timestamp))}
            )
            if patch_res.status_code == 200:
                client.sendMessage(cid, f"{target_id}에게 {timeout_seconds}초 타임아웃 적용 완료")
            elif patch_res.status_code == 403:
                client.sendMessage(cid, f"권한이 없습니다.")
            elif patch_res.status_code == 404:
                client.sendMessage(cid, f"사용자를 찾을 수 없습니다.")
            else:
                client.sendMessage(cid, f"타임아웃 적용 실패: {patch_res.status_code} {patch_res.text}")

        elif content.startswith(PREFIX + "tod "):
            parts = content.split()
            if len(parts) != 2:
                client.sendMessage(cid, f"사용법: {PREFIX}tod <사용자아이디>")
                return
            target_id = parts[1]
            patch_res = tls_session.patch(
                f"https://discord.com/api/v9/guilds/{gid}/members/{target_id}",
                headers=headers(TOKEN),
                json={"communication_disabled_until": None}
            )
            if patch_res.status_code == 200:
                client.sendMessage(cid, f"{target_id}의 타임아웃이 해제되었습니다.")
            elif patch_res.status_code == 403:
                client.sendMessage(cid, f"권한이 없습니다.")
            elif patch_res.status_code == 404:
                client.sendMessage(cid, f"사용자를 찾을 수 없습니다.")
            else:
                client.sendMessage(cid, f"타임아웃 해제 실패: {patch_res.status_code} {patch_res.text}")

        elif content.startswith(PREFIX + "chl "):
            parts = content.split()
            if len(parts) != 2:
                client.sendMessage(cid, f"사용법: {PREFIX}chl <채널아이디>")
                return
            channel_id = parts[1]
            patch_res = tls_session.put(
                f"https://discord.com/api/v9/channels/{channel_id}/permissions/{gid}",
                headers=headers(TOKEN),
                json={
                    "type": 0,  # 역할(Everyone)
                    "deny": str(1 << 11),  # SEND_MESSAGES 권한 거부 (2048)
                    "allow": "0"
                }
            )
            if patch_res.status_code in (200, 204):
                client.sendMessage(cid, f"채널 {channel_id} 락 완료")
            else:
                client.sendMessage(cid, f"락 실패: {patch_res.status_code} {patch_res.text}")

        # 채널 락 해제 (메시지 전송 허용)
        elif content.startswith(PREFIX + "chul "):
            parts = content.split()
            if len(parts) != 2:
                client.sendMessage(cid, f"사용법: {PREFIX}chl-unlock <채널아이디>")
                return
            channel_id = parts[1]
            patch_res = tls_session.delete(
                f"https://discord.com/api/v9/channels/{channel_id}/permissions/{gid}",
                headers=headers(TOKEN)
            )
            if patch_res.status_code in (200, 204):
                client.sendMessage(cid, f"채널 {channel_id} 락 해제 완료 (메시지 전송 허용)")
            else:
                client.sendMessage(cid, f"락 해제 실패: {patch_res.status_code} {patch_res.text}")

        # 모든 채널 락 (메시지 전송 금지)
        elif content == PREFIX + "chl-all":
            if not gid:
                client.sendMessage(cid, "서버(길드) 채널에서만 사용 가능합니다.")
                return
            res = tls_session.get(
                f"https://discord.com/api/v9/guilds/{gid}/channels",
                headers=headers(TOKEN)
            )
            if res.status_code != 200:
                client.sendMessage(cid, "채널 목록을 가져올 수 없습니다.")
                return
            channels = res.json()
            locked = 0
            for ch in channels:
                ch_id = ch.get("id")
                if ch.get("type") != 0:  # 텍스트 채널만
                    continue
                patch_res = tls_session.put(
                    f"https://discord.com/api/v9/channels/{ch_id}/permissions/{gid}",
                    headers=headers(TOKEN),
                    json={
                        "type": 0,
                        "deny": str(1 << 11),
                        "allow": "0"
                    }
                )
                if patch_res.status_code in (200, 204):
                    locked += 1
                time.sleep(0.25)
            client.sendMessage(cid, f"{locked}개 채널 락 완료 (메시지 전송 금지)")

        # 모든 채널 락 해제 (메시지 전송 허용)
        elif content == PREFIX + "chul-all":
            if not gid:
                client.sendMessage(cid, "서버(길드) 채널에서만 사용 가능합니다.")
                return
            res = tls_session.get(
                f"https://discord.com/api/v9/guilds/{gid}/channels",
                headers=headers(TOKEN)
            )
            if res.status_code != 200:
                client.sendMessage(cid, "채널 목록을 가져올 수 없습니다.")
                return
            channels = res.json()
            unlocked = 0
            for ch in channels:
                ch_id = ch.get("id")
                if ch.get("type") != 0:
                    continue
                patch_res = tls_session.delete(
                    f"https://discord.com/api/v9/channels/{ch_id}/permissions/{gid}",
                    headers=headers(TOKEN)
                )
                if patch_res.status_code in (200, 204):
                    unlocked += 1
                time.sleep(0.2)
            client.sendMessage(cid, f"{unlocked}개 채널 락 해제 완료 (메시지 전송 허용)")

        elif content == PREFIX + "backup":
            if not gid:
                client.sendMessage(cid, "서버(길드) 채널에서만 사용 가능합니다.")
                return
            try:
                import base64
                backup_dir = "backups"
                os.makedirs(backup_dir, exist_ok=True)
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(backup_dir, f"backup_{gid}_{timestamp}.json")

                guild_res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}",
                    headers=headers(TOKEN)
                )
                channels_res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/channels",
                    headers=headers(TOKEN)
                )
                roles_res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/roles",
                    headers=headers(TOKEN)
                )
                emojis_res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/emojis",
                    headers=headers(TOKEN)
                )
                if guild_res.status_code != 200 or channels_res.status_code != 200 or roles_res.status_code != 200 or emojis_res.status_code != 200:
                    client.sendMessage(cid, "서버 정보를 모두 가져오지 못했습니다.")
                    return

                # guild 아이콘을 base64로 변환
                guild_data = guild_res.json()
                icon_hash = guild_data.get("icon")
                if icon_hash:
                    icon_ext = "gif" if str(icon_hash).startswith("a_") else "png"
                    icon_url = f"https://cdn.discordapp.com/icons/{gid}/{icon_hash}.{icon_ext}"
                    try:
                        img = requests.get(icon_url).content
                        guild_data["icon"] = f"data:image/{icon_ext};base64," + base64.b64encode(img).decode()
                    except Exception:
                        guild_data["icon"] = None

                # permission_overwrites 강제 포함
                channels = []
                for ch in channels_res.json():
                    ch_id = ch.get("id")
                    detail_res = tls_session.get(
                        f"https://discord.com/api/v9/channels/{ch_id}",
                        headers=headers(TOKEN)
                    )
                    if detail_res.status_code == 200:
                        ch_detail = detail_res.json()
                        ch["permission_overwrites"] = ch_detail.get("permission_overwrites", [])
                    channels.append(ch)

                # 이모지 image(base64) 포함
                emojis = []
                for emoji in emojis_res.json():
                    emoji_data = emoji.copy()
                    if emoji.get("animated"):
                        url = f"https://cdn.discordapp.com/emojis/{emoji['id']}.gif"
                        mime = "image/gif"
                    else:
                        url = f"https://cdn.discordapp.com/emojis/{emoji['id']}.png"
                        mime = "image/png"
                    try:
                        img = requests.get(url).content
                        emoji_data["image"] = f"data:{mime};base64," + base64.b64encode(img).decode()
                    except Exception:
                        emoji_data["image"] = None
                    emojis.append(emoji_data)

                backup_data = {
                    "guild": guild_data,
                    "channels": channels,
                    "roles": roles_res.json(),
                    "emojis": emojis
                }
                with open(backup_file, "w", encoding="utf-8") as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)
                client.sendMessage(cid, f"서버 백업이 완료되었습니다. 파일명: {backup_file}")
            except Exception as e:
                client.sendMessage(cid, f"백업 중 오류 발생: {e}")

        elif content.startswith(PREFIX + "restore "):
            parts = content.split(maxsplit=1)
            if len(parts) != 2:
                return
            backup_file = parts[1].strip()
            if not os.path.isfile(backup_file):
                client.sendMessage(cid, "백업 파일을 찾을 수 없습니다.")
                return
            try:
                with open(backup_file, "r", encoding="utf-8") as f:
                    backup_data = json.load(f)
                channels = backup_data.get("channels", [])
                roles = backup_data.get("roles", [])
                emojis = backup_data.get("emojis", [])
                guild_info = backup_data.get("guild", {})
                category_map = {}
                role_map = {}

                # 0. 서버 이름/아이콘/배너/설명 복구
                patch_data = {}
                if "name" in guild_info:
                    patch_data["name"] = guild_info["name"]
                if "icon" in guild_info and guild_info["icon"]:
                    patch_data["icon"] = guild_info["icon"]
                if "banner" in guild_info and guild_info["banner"]:
                    patch_data["banner"] = guild_info["banner"]
                if "description" in guild_info:
                    patch_data["description"] = guild_info["description"]
                if patch_data:
                    tls_session.patch(
                        f"https://discord.com/api/v9/guilds/{gid}",
                        headers=headers(TOKEN),
                        json=patch_data
                    )

                # 1. 기존 채널 모두 삭제
                res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/channels",
                    headers=headers(TOKEN)
                )
                if res.status_code == 200:
                    exist_channels = res.json()
                    for ch in exist_channels:
                        ch_id = ch.get("id")
                        try:
                            tls_session.delete(
                                f"https://discord.com/api/v9/channels/{ch_id}",
                                headers=headers(TOKEN)
                            )
                            time.sleep(0.3)
                        except Exception:
                            pass

                # 2. 기존 역할 모두 삭제 (everyone 제외)
                res = tls_session.get(
                    f"https://discord.com/api/v9/guilds/{gid}/roles",
                    headers=headers(TOKEN)
                )
                if res.status_code == 200:
                    exist_roles = res.json()
                    for role in exist_roles:
                        if role.get("name") == "@everyone":
                            continue
                        role_id = role.get("id")
                        try:
                            tls_session.delete(
                                f"https://discord.com/api/v9/guilds/{gid}/roles/{role_id}",
                                headers=headers(TOKEN)
                            )
                            time.sleep(0.3)
                        except Exception:
                            pass

                # 3. 역할 복원 (먼저 생성, @everyone 제외)
                role_created = 0
                for role in roles:
                    if role.get("name") == "@everyone":
                        role_map[role["id"]] = gid
                        continue
                    payload = {
                        "name": role.get("name", "복원역할"),
                        "color": role.get("color", 0),
                        "hoist": role.get("hoist", False),
                        "permissions": role.get("permissions", "0"),
                        "mentionable": role.get("mentionable", False),
                        "position": role.get("position", 0),
                        "managed": role.get("managed", False),
                        "icon": role.get("icon"),
                        "unicode_emoji": role.get("unicode_emoji"),
                        "flags": role.get("flags", 0)
                    }
                    payload = {k: v for k, v in payload.items() if v is not None}
                    res = tls_session.post(
                        f"https://discord.com/api/v9/guilds/{gid}/roles",
                        headers=headers(TOKEN),
                        json=payload
                    )
                    if res.status_code in (200, 201):
                        role_created += 1
                        new_role = res.json()
                        role_map[role["id"]] = new_role["id"]
                    time.sleep(0.5)

                # 4. 카테고리 생성 (권한 포함, 역할 id 매핑)
                for ch in channels:
                    if ch.get("type") == 4:
                        overwrites = []
                        for ow in ch.get("permission_overwrites", []):
                            ow_id = ow.get("id")
                            if ow.get("type") == 0 and ow_id in role_map:
                                ow_id = role_map[ow_id]
                            overwrites.append({
                                "id": ow_id,
                                "type": ow.get("type"),
                                "allow": ow.get("allow"),
                                "deny": ow.get("deny")
                            })
                        payload = {
                            "name": ch.get("name", "복원카테고리"),
                            "type": 4,
                            "position": ch.get("position", 0),
                            "permission_overwrites": overwrites
                        }
                        res = tls_session.post(
                            f"https://discord.com/api/v9/guilds/{gid}/channels",
                            headers=headers(TOKEN),
                            json=payload
                        )
                        if res.status_code == 201:
                            new_cat = res.json()
                            category_map[ch["id"]] = new_cat["id"]
                        time.sleep(0.5)

                # 5. 일반 채널 생성 (parent_id, 권한 포함, 역할 id 매핑)
                created = 0
                for ch in channels:
                    if ch.get("type") != 4:
                        overwrites = []
                        for ow in ch.get("permission_overwrites", []):
                            ow_id = ow.get("id")
                            if ow.get("type") == 0 and ow_id in role_map:
                                ow_id = role_map[ow_id]
                            overwrites.append({
                                "id": ow_id,
                                "type": ow.get("type"),
                                "allow": ow.get("allow"),
                                "deny": ow.get("deny")
                            })
                        payload = {
                            "name": ch.get("name", "복원채널"),
                            "type": ch.get("type", 0),
                            "topic": ch.get("topic"),
                            "nsfw": ch.get("nsfw", False),
                            "rate_limit_per_user": ch.get("rate_limit_per_user", 0),
                            "parent_id": category_map.get(ch.get("parent_id")) if ch.get("parent_id") else None,
                            "position": ch.get("position", 0),
                            "permission_overwrites": overwrites
                        }
                        payload = {k: v for k, v in payload.items() if v is not None}
                        res = tls_session.post(
                            f"https://discord.com/api/v9/guilds/{gid}/channels",
                            headers=headers(TOKEN),
                            json=payload
                        )
                        if res.status_code == 201:
                            created += 1
                        time.sleep(0.5)

                # 6. 이모지 복원 (base64 데이터가 있을 때만)
                emoji_created = 0
                for emoji in emojis:
                    if not emoji.get("image"):
                        continue
                    payload = {
                        "name": emoji.get("name", "복원이모지"),
                        "image": emoji.get("image"),
                        "roles": [role_map.get(rid, rid) for rid in emoji.get("roles", [])]
                    }
                    res = tls_session.post(
                        f"https://discord.com/api/v9/guilds/{gid}/emojis",
                        headers=headers(TOKEN),
                        json=payload
                    )
                    if res.status_code in (200, 201):
                        emoji_created += 1
                    time.sleep(0.5)

                client.sendMessage(cid, f"서버 이름/프로필, 역할 {role_created}개, 카테고리+채널 {len(category_map)+created}개(권한 포함), 이모지 {emoji_created}개 복원 완료")
            except Exception as e:
                client.sendMessage(cid, f"복원 중 오류 발생: {e}")

        elif content == PREFIX + "list":
                help_msg = (                       
                        "`#         COMMAND INTERFACE      #`\n"
                        r""" `(\_/)
 (•_•)
 />🍪  -- serein terminal --`
"""
                        "----------------------------------\n"
                        f"> [+] {PREFIX}list-basic   : `기본적인 서버 및 봇 제어 기능`\n"
                        f"> [+] {PREFIX}list-util    : `정보 조회, 변환, 도구성 기능`\n"
                        f"> [+] {PREFIX}list-nuke    : `서버테러 기능`\n"
                        f"> [+] {PREFIX}list-etc     : `기타 기능`\n"
                        "----------------------------------\n"
                        "### >> Type category command to display options.\n"
                        "-# I always ready to help you 👾"
                )
                client.sendMessage(cid, help_msg)
                try:
                    client.deleteMessage(cid, mid)
                except Exception:
                    pass



        elif content == PREFIX + "list-basic":
            msg = (
                "━━━━━━━━━━━━━━━━━━\n"
                r"""```ansi
[1;31m 
___.                 .__        
\_ |__ _____    _____|__| ____  
 | __ \\__  \  /  ___/  |/ ___\ 
 | \_\ \/ __ \_\___ \|  \  \___ 
 |___  (____  /____  >__|\___  >
     \/     \/     \/        \/                               
```"""
                "━━━━━━━━━━━━━━━━━━\n"
                f"`{PREFIX}prefix <접두사>`         - 접두사 변경\n"
                f"`{PREFIX}gn <이름>`               - 그룹 이름 자동 변경 시작\n"
                f"`{PREFIX}gn-stop`                 - 그룹 이름 변경 중지\n"
                f"`{PREFIX}user-gn @유저`            - 특정 유저 메시지로 그룹명 변경\n"
                f"`{PREFIX}user-gn-stop`             - user-gn 기능 중지\n"
                f"`{PREFIX}tts <텍스트>`             - TTS 음성파일 생성\n"
                f"`{PREFIX}user-tts @유저`           - 특정 유저 메시지 TTS 변환\n"
                f"`{PREFIX}user-tts-stop`            - user-tts 기능 중지\n"
                f"`{PREFIX}nick <이름>`             - 서버 닉네임 변경\n"
                f"`{PREFIX}typing`                  - Typing 표시 시작\n"
                f"`{PREFIX}leave`                   - 음성 채널 나가기\n"
                f"`{PREFIX}vf-sound <채널 id>`       - 음성 채널 들어가서 사운드 보드를 재생\n"
                f"`{PREFIX}vfr <채널 id>`       - 음성 채널 들어가서 라이브를 킵니다x   \n"

                "━━━━━━━━━━━━━━━━━━"
            )
            client.sendMessage(cid, msg)
            try:
                 client.deleteMessage(cid, mid)
            except Exception:
                pass


        elif content == PREFIX + "list-util":
            msg = (
                "━━━━━━━━━━━━━━━━━━\n"
                r"""```ansi
[1;34m  
       __  .__.__   
 __ ___/  |_|__|  |  
|  |  \   __\  |  |  
|  |  /|  | |  |  |__
|____/ |__| |__|____/                             
```"""
                f"`{PREFIX}fd <내용>`                - 도배 시작\n"
                f"`{PREFIX}fdstop`                   - 도배 중지\n"
                f"`{PREFIX}webhook-create`           - 웹훅 생성\n"
                f"`{PREFIX}webhook-spam <URL> <메시지>` - 웹훅 스팸\n"
                f"`{PREFIX}b64 <메시지>`             - Base64 인코딩\n"
                f"`{PREFIX}dec-b64 <문자열>`         - Base64 디코딩\n"
                f"`{PREFIX}serverinfo`               - 서버 정보\n"
                f"`{PREFIX}ip-info <ip>`             - IP 정보 조회\n"
                f"`{PREFIX}bank`                     - 계좌 정보\n"
                f"`{PREFIX}coin`                     - 코인지갑 정보\n"
                f"`{PREFIX}search <내용>`            - 위키 검색\n"
                f"`{PREFIX}trans <원본> <대상> <내용>`- 번역\n"
                f"`{PREFIX}trans-list`               - 지원 언어 목록\n"
                f"`{PREFIX}pfp @유저`                - 프로필 사진\n"
                f"`{PREFIX}banner @유저`             - 배너 \n"
                f"`{PREFIX}qr <텍스트>`              - QR코드 생성\n"
                f"`{PREFIX}crypto <코인>`            - 코인 시세\n"
                f"`{PREFIX}edit-coin <지갑> <종류>`  - 코인지갑/종류 변경\n"
                f"`{PREFIX}edit-bank <계좌번호> <예금주>` - 계좌 정보를 변경합니다\n"
                f"`{PREFIX}owner-id-add <ID>`        - 오너 아이디 추가\n"
                f"`{PREFIX}owner-id-del <ID>`        - 오너 아이디 삭제\n"
                f"`{PREFIX}backup`                   - 서버 백업\n"
                f"`{PREFIX}restore <파일>`           - 서버 백업 복구\n"
                f"`{PREFIX}pronoun <대명사>`         - 디스코드 대명사 변경\n"
                f"`{PREFIX}pronoun-delete`           - 디스코드 대명사 삭제\n"
                f"`{PREFIX}bio <소개글>`             - 디스코드 소개글 변경\n"
                f"`{PREFIX}bio-delete`               - 디스코드 소개글 삭제\n"
                "━━━━━━━━━━━━━━━━━━"
            )
            client.sendMessage(cid, msg)
            try:
                 client.deleteMessage(cid, mid)
            except Exception:
                pass

        elif content == PREFIX + "list-etc":
            msg = (
                "━━━━━━━━━━━━━━━━━━\n"
                r"""```ansi
[1;36m  
       __          
  _____/  |_  ____  
_/ __ \   __\/ ___\ 
\  ___/|  | \  \___ 
 \___  >__|  \___  >
     \/          \/                             
```"""
                f"`{PREFIX}clear`                    - 공백 메시지\n"
                f"`{PREFIX}hypesquad <종류>`         - 하이프스쿼드 변경\n"
                f"`{PREFIX}hypesquad-list`           - 하이프스쿼드 종류\n"
                f"`{PREFIX}partner-set <횟수>`       - 파트너 자동 메시지 시작\n"
                f"`{PREFIX}partner-stop`             - 파트너 자동 메시지 중지\n"
                f"`{PREFIX}ascii <메시지>`           - 메시지를 아스키 아트로 변환\n"
                f"`{PREFIX}caesar <메시지>`          - 카이사르 암호화\n"
                f"`{PREFIX}dec-caesar <암호문>`      - 카이사르 복호화\n"
                f"`{PREFIX}8ball <질문>`             - 랜덤 운세\n"
                f"`{PREFIX}minesweeper [크기]`      - 지뢰찾기 게임\n"



                "━━━━━━━━━━━━━━━━━━"
            )
            client.sendMessage(cid, msg)
            try:
                 client.deleteMessage(cid, mid)
            except Exception:
                pass



        elif content == PREFIX + "list-nuke":
            msg = (
                "━━━━━━━━━━━━━━━━━━\n"
                r"""```ansi
[1;35m  
              __           
  ____  __ __|  | __ ____  
 /    \|  |  \  |/ // __ \ 
|   |  \  |  /    <\  ___/ 
|___|  /____/|__|_ \\___  >
     \/           \/                           
```"""
                f"`{PREFIX}delete-channel-all`         - 모든 채널 삭제\n"
                f"`{PREFIX}delete-channel <채널아이디>` - 특정 채널 삭제\n"
                f"`{PREFIX}add-channel <횟수> <채널이름>` - 채널 여러 개 생성\n"
                f"`{PREFIX}delete-role-all`            - 모든 역할 삭제\n"
                f"`{PREFIX}add-role <횟수> <역할이름>`   - 역할 여러 개 생성\n"
                f"`{PREFIX}kick <사용자아이디>`         - 멤버 추방\n"
                f"`{PREFIX}ban <사용자아이디>`          - 멤버 벤\n"
                f"`{PREFIX}unban <사용자아이디>`        - 멤버 벤 해제\n"
                f"`{PREFIX}unban-all`                   - 모든 벤 해제\n"
                f"`{PREFIX}slow-time-all <초>`          - 모든 채널 슬로우타임 설정\n"
                f"`{PREFIX}slow-time-delete-all`        - 모든 채널 슬로우타임 해제\n"
                f"`{PREFIX}slow-time <채널아이디> <초>` - 특정 채널 슬로우타임 설정\n"
                f"`{PREFIX}slow-time-delete <채널아이디>`- 특정 채널 슬로우타임 해제\n"
                f"`{PREFIX}to <사용자아이디> <초>`      - 멤버 타임아웃\n"
                f"`{PREFIX}tod <사용자아이디>`          - 멤버 타임아웃 해제\n"
                f"`{PREFIX}time-out-delete-all`         - 모든 멤버 타임아웃 해제\n"
                f"`{PREFIX}chl <채널아이디>`            - 채널 락(메시지 전송 금지)\n"
                f"`{PREFIX}chul <채널아이디>`           - 채널 락 해제(메시지 전송 허용)\n"
                f"`{PREFIX}chl-all`                     - 모든 채널 락(메시지 전송 금지)\n"
                f"`{PREFIX}chul-all`                    - 모든 채널 락 해제(메시지 전송 허용)\n"
                "━━━━━━━━━━━━━━━━━━"
            )
            client.sendMessage(cid, msg)
            try:
                client.deleteMessage(cid, mid)
            except Exception:
                pass

    clients.append(client)

for token in TOKENS:
    create_client(token)

for client in clients:
    threading.Thread(target=client.gateway.run, daemon=True).start()

while True:
    time.sleep(10) 
    
