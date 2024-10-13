import asyncio
import random
import sys
import traceback
from itertools import cycle
from urllib.parse import unquote, quote

import aiohttp
import requests
from aiocfscrape import CloudflareScraper
from aiohttp_proxy import ProxyConnector
from better_proxy import Proxy
from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered, FloodWait
from pyrogram.raw.types import InputBotAppShortName
from pyrogram.raw.functions.messages import RequestAppWebView
from bot.core.agents import generate_random_user_agent
from bot.config import settings
import time as time_module

from bot.utils import logger
from bot.exceptions import InvalidSession
from .headers import headers
from .tasks import tasks
from random import randint
import urllib3
from datetime import datetime
import re

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def check_yesterday_time(created_time):
    timestamp = datetime.strptime(created_time, "%Y-%m-%dT%H:%M:%S.%fZ")
    current_date = datetime.utcnow().date()
    if timestamp.date() == current_date:
        return True
    else:
        return False


class Tapper:
    def __init__(self, tg_client: Client, multi_thread: bool):
        self.tg_client = tg_client
        self.session_name = tg_client.name
        self.first_name = ''
        self.last_name = ''
        self.user_id = ''
        self.auth_token = ""
        self.last_claim = None
        self.last_checkin = None
        self.balace = 0
        self.maxtime = 0
        self.fromstart = 0
        self.new_usr = False
        self.balance = 0
        self.multi_thread = multi_thread
        self.my_ref = "coub__marker_29987832"
        self.coin_earn_per_tap = 0
        self.available_energy = 0
        self.max_energy = 0
        self.hash = ""
        self.chat_type = ""
        self.start_param = ""
        self.auth_date = ""
        self.chat_instance = ""
        self.user_data = ""
        self.token_generated_time = 0
        self.logged_in = False
        self.tg_web_data = ""
        self.completed_task_ids = []
        self.token_expire = 0
        self.balance = 0
        self.last_create_time = {}
        self.template_header = headers.copy()
        self.channel_id = 0
        self.session1 = requests.Session()

    async def get_tg_web_data(self, proxy: str | None) -> str:
        try:
            if settings.REF_LINK == "":
                ref_param = "coub__marker_29987832"
            else:
                ref_param = settings.REF_LINK.split("=")[1]
        except:
            logger.error(f"{self.session_name} | Ref link invaild please check again !")
            sys.exit()
        actual = random.choices([self.my_ref, ref_param], weights=[30, 70]) # edit this line to [0, 100] if you don't want to support me
        self.ref = actual[0]
        if proxy:
            proxy = Proxy.from_str(proxy)
            proxy_dict = dict(
                scheme=proxy.protocol,
                hostname=proxy.host,
                port=proxy.port,
                username=proxy.login,
                password=proxy.password
            )
        else:
            proxy_dict = None

        self.tg_client.proxy = proxy_dict
        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                    start_command_found = False
                    async for message in self.tg_client.get_chat_history('coub'):
                        if (message.text and message.text.startswith('/start')) or (
                                message.caption and message.caption.startswith('/start')):
                            start_command_found = True
                            break

                    if not start_command_found:
                        self.new_usr = True
                        await self.tg_client.send_message('coub', "/start")
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            while True:
                try:
                    peer = await self.tg_client.resolve_peer('coub')
                    break
                except FloodWait as fl:
                    fls = fl.value

                    logger.warning(f"<light-yellow>{self.session_name}</light-yellow> | FloodWait {fl}")
                    logger.info(f"<light-yellow>{self.session_name}</light-yellow> | Sleep {fls}s")

                    await asyncio.sleep(fls + 3)

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotAppShortName(bot_id=peer, short_name="app"),
                platform='android',
                write_allowed=True,
                start_param=actual[0]
            ))

            auth_url = web_view.url
            # print(auth_url)
            tg_web_data1 = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])
            # print(tg_web_data)
            tg_web_data = unquote(
                string=unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0]))

            # print(tg_web_data)

            self.hash = tg_web_data.split('&hash=')[1]
            self.user_data = tg_web_data.split("user=")[1].split("&chat_instance=")[0]
            self.auth_date = tg_web_data.split('&auth_date=')[1].split('&hash=')[0]
            self.chat_instance = tg_web_data.split("&chat_instance=")[1].split("&chat_type=")[0]
            self.chat_type = tg_web_data.split("&chat_type=")[1].split("&start_param=")[0]
            self.start_param = actual[0]

            # print(self.user_data)

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data1

        except InvalidSession as error:
            raise error

        except Exception as error:
            traceback.print_exc()
            logger.error(f"<light-yellow>{self.session_name}</light-yellow> | Unknown error during Authorization: "
                         f"{error}")
            await asyncio.sleep(delay=3)

    async def check_proxy(self, http_client: aiohttp.ClientSession, proxy: Proxy):
        try:
            response = await http_client.get(url='https://httpbin.org/ip', timeout=aiohttp.ClientTimeout(5), )
            ip = (await response.json()).get('origin')
            logger.info(f"{self.session_name} | Proxy IP: {ip}")
            return True
        except Exception as error:
            logger.error(f"{self.session_name} | Proxy: {proxy} | Error: {error}")
            return False

    def get_xcsrf_token(self, url):
        temp_headers = self.template_header.copy()
        temp_headers['Sec-Fetch-Dest'] = "iframe"
        temp_headers['Sec-Fetch-Mode'] = "navigate"
        temp_headers['Sec-Fetch-Site'] = "same-origin"
        temp_headers['Referer'] = "https://coub.com/tg-app/feed/random"
        res = self.session1.get(url, headers=temp_headers)
        for cookie in res.cookies:
            if cookie.name == "_cobb_session":
                self.session1.cookies.set(cookie.name, cookie.value)
        pattern = r'<meta\s+name="csrf-token"\s+content="([^"]+)"'
        match = re.search(pattern, res.text)
        if match:
            csrf_token = match.group(1)
            return csrf_token
        else:
            return None

    def signup(self, session: requests.Session):
        payload = {
            "user": self.user_data,
            "chat_instance": self.chat_instance,
            "chat_type": self.chat_type,
            "start_param": self.start_param,
            "auth_date": self.auth_date,
            "hash": self.hash
        }
        signup_headers = headers.copy()
        signup_headers['Content-Type'] = "application/x-www-form-urlencoded"
        res = session.post("https://coub.com/api/v2/sessions/signup_mini_app", headers=signup_headers, data=payload)
        if res.status_code == 200:
            api_auth = res.json()
            for cookie in res.cookies:
                if cookie.name == "_cobb_session":
                    session.cookies.set(cookie.name, cookie.value)
                    self.session1.cookies.set(cookie.name, cookie.value)

            headers['X-Auth-Token'] = api_auth['api_token']
            logger.success(f"{self.session_name} | <green>Successfully registered an account!</green>")
        else:
            print(res.text)
            logger.warning(f"{self.session_name} | <yellow>Failed to create account: {res.status_code}</yellow>")

    def get_token(self, session: requests.Session):
        res = session.post("https://coub.com/api/v2/torus/token", headers=headers)
        if res.status_code == 200:
            token = res.json()
            for cookie in res.cookies:
                if cookie.name == "_cobb_session":
                    session.cookies.set(cookie.name, cookie.value)
                    self.session1.cookies.set(cookie.name, cookie.value)

            headers['Authorization'] = f"{token['token_type']} {token['access_token']}"
            self.token_expire = token['expires_in']
            self.token_generated_time = int(time_module.time())
            self.logged_in = True
        else:
            print(res.text)
            logger.warning(f"{self.session_name} | <yellow>Failed to get token: {res.status_code}</yellow>")

    def get_status_new_user(self, session: requests.Session):
        headers1 = headers.copy()
        headers1['Referer'] = "https://coub.com/tg-app/onboarding"
        res = session.get("https://coub.com/api/v2/sessions/status", headers=headers)
        if res.status_code == 200:
            channel_info = res.json()
            self.channel_id = channel_info['user']['current_channel']['id']
            headers['Sec-Fetch-Site'] = "same-site"
            headers['X-Tg-Authorization'] = self.tg_web_data
            return True
        else:
            print(res.text)
            logger.warning(f"{self.session_name} | <yellow>Failed to get user status: {res.status_code}</yellow>")
            return False

    def get_ref_stats(self, session: requests.Session):
        ref_headers = headers.copy()
        ref_headers['Referer'] = "https://coub.com/"
        ref_headers['Host'] = None
        # print(ref_headers)
        res = session.get("https://rewards.coub.com/api/v2/referal_rewards", headers=ref_headers)
        if res.status_code == 200:
            data_ = res.json()
            logger.info(f"{self.session_name} | Coub balance: <blue>{self.balance}</blue> coub | Referal balance: <blue>{data_['referal_balance']}</blue> coubs | Referal count: <cyan>{data_['referal_count']}</cyan>")
        else:
            print(res.text)
            logger.warning(f"{self.session_name} | <yellow>Failed to get referral stats: {res.status_code}</yellow>")

    def get_status(self, session: requests.Session):
        res = session.get("https://coub.com/api/v2/sessions/status", headers=headers)
        if res.status_code == 200:
            channel_info = res.json()
            headers['Sec-Fetch-Site'] = "same-site"
            headers['X-Tg-Authorization'] = self.tg_web_data
            c_info = f"""
                ===<blue>{self.session_name}</blue>===
                Total followers: <blue>{channel_info['user']['current_channel']['followers_count']}</blue> followers
                Recoubs count: <blue>{channel_info['user']['current_channel']['recoubs_count']}</blue> recoubs
                Likes count: <blue>{channel_info['user']['current_channel']['likes_count']}</blue> likes
                Views count: <blue>{channel_info['user']['current_channel']['views_count']}</blue> views
            """
            self.channel_id = channel_info['user']['current_channel']['id']
            logger.info(f"{self.session_name} | {channel_info['user']['current_channel']['title']}'s channel Info:\n{c_info}")
            return True
        else:
            print(res.text)
            logger.warning(f"{self.session_name} | <yellow>Failed to get user status: {res.status_code}</yellow>")
            return False

    def get_user_rewards(self, session: requests.Session):
        temp_headers = headers.copy()
        temp_headers['Referer'] = "https://coub.com/"
        temp_headers['Host'] = None
        res = session.get("https://rewards.coub.com/api/v2/get_user_rewards", headers=temp_headers)
        if res.status_code == 200:
            reward = res.json()
            # print(reward)
            self.balance = 0
            for taskid in reward:
                self.balance += taskid['points']
                if taskid['id'] not in tasks.keys():
                    continue
                if tasks[taskid['id']]['repeatable'] is True:
                    self.last_create_time.update({
                        taskid['id']: taskid['created_at']
                    })
                    continue
                if taskid not in self.completed_task_ids:
                    self.completed_task_ids.append(taskid['id'])
            for taskid in reward:
                if taskid['id'] not in tasks.keys():
                    continue
                # self.balance += taskid['points']
                if tasks[taskid['id']]['repeatable'] is True:
                   if check_yesterday_time(self.last_create_time[taskid['id']]):
                       self.completed_task_ids.append(taskid['id'])

            if self.new_usr:
                logger.success(f"{self.session_name} | <green>Successfully claimed <blue>{reward[0]['points']} coubs</blue></green>")
                self.new_usr = False
        else:
            print(res.text)
            logger.warning(f"{self.session_name} | <yellow>Failed to get claim user reward: {res.status_code}</yellow>")
            # return False
    def get_lastest_user_rewards(self, session: requests.Session):
        temp_headers = headers.copy()
        temp_headers['Referer'] = "https://coub.com/"
        temp_headers['Host'] = None
        res = session.get("https://rewards.coub.com/api/v2/get_user_rewards", headers=temp_headers)
        if res.status_code == 200:
            reward = res.json()
            # print(reward)
            self.balance = 0
            for taskid in reward:
                
                self.balance += taskid['points']
                if taskid['id'] not in tasks.keys():
                    continue
                if tasks[taskid['id']]['repeatable'] is True:
                    self.last_create_time.update({
                        taskid['id']: taskid['created_at']
                    })
                    continue
                if taskid not in self.completed_task_ids:
                    self.completed_task_ids.append(taskid['id'])
            for taskid in reward:
                if taskid['id'] not in tasks.keys():
                    continue
                # self.balance += taskid['points']
                if tasks[taskid['id']]['repeatable'] is True:
                    if check_yesterday_time(self.last_create_time[taskid['id']]):
                        self.completed_task_ids.append(taskid['id'])

            logger.success(f"{self.session_name} | <green>Successfully claimed <blue>{reward[-1]['points']} coubs</blue></green>")
        else:
            print(res.text)
            logger.warning(f"{self.session_name} | <yellow>Failed to get claim user reward: {res.status_code}</yellow>")
            # return False

    def complete_ref_task(self, session: requests.Session):
        if 1 in self.completed_task_ids:
            return
        temp_headers = headers.copy()
        temp_headers['Referer'] = "https://coub.com/"
        temp_headers['Host'] = None
        res = session.get("https://rewards.coub.com/api/v2/complete_task?task_reward_id=1", headers=temp_headers)
        if res.status_code == 200:
            logger.success(f"{self.session_name} | <green>Successfully completed ref task</green>")
        else:
            print(res.text)
            logger.warning(f"{self.session_name} | <yellow>Failed to complete ref task: {res.status_code}</yellow>")
            # return False

    def login(self, session: requests.Session):
        payload = {
            "user": self.user_data,
            "chat_instance": self.chat_instance,
            "chat_type": self.chat_type,
            "start_param": self.start_param,
            "auth_date": self.auth_date,
            "hash": self.hash
        }
        login_headers = headers.copy()
        login_headers['Content-Type'] = "application/x-www-form-urlencoded"
        response = session.post(f"https://coub.com/api/v2/sessions/login_mini_app", headers=login_headers, data=payload)
        if response.status_code == 200:
            for cookie in response.cookies:
                if cookie.name == "_cobb_session":
                    session.cookies.set(cookie.name, cookie.value)
                    self.session1.cookies.set(cookie.name, cookie.value)

            logger.success(f"{self.session_name} | <green>Logged in.</green>")
            # return True
        else:
            print(response.text)
            logger.warning(f"{self.session_name} | <red>Failed to login</red>")
            # return False

    async def complete_not_repeat_tasks(self, session: requests.Session):
        temp_headers = headers.copy()
        temp_headers['Referer'] = "https://coub.com/"
        temp_headers['Host'] = None
        for id in tasks.keys():
            if id in self.completed_task_ids or tasks[id]['repeatable']:
                continue
            res = session.get(f"https://rewards.coub.com/api/v2/complete_task?task_reward_id={id}", headers=temp_headers)
            if res.status_code == 200:
                logger.success(f"{self.session_name} | <green>Successfully completed task <blue>{tasks[id]['title']}</blue></green>")
                self.get_lastest_user_rewards(session)
            else:
                print(res.text)
                logger.warning(f"{self.session_name} | <yellow>Failed to complete task {tasks[id]['title']} - id: {id}: {res.status_code}</yellow>")
            await asyncio.sleep(random.uniform(3, 6))
                # return False

    async def complete_repeat_tasks(self, session: requests.Session):
        temp_headers = headers.copy()
        temp_headers['Referer'] = "https://coub.com/"
        temp_headers['Host'] = None
        for id in tasks.keys():
            if id in self.completed_task_ids:
                continue
            if tasks[id]['repeatable'] is False:
                continue
            res = session.get(f"https://rewards.coub.com/api/v2/complete_task?task_reward_id={id}",
                                  headers=temp_headers)
            if res.status_code == 200:
                logger.success(
                        f"{self.session_name} | <green>Successfully completed task <blue>{tasks[id]['title']}</blue></green>")
                self.get_lastest_user_rewards(session)
            else:
                print(res.text)
                logger.warning(
                        f"{self.session_name} | <yellow>Failed to complete task {tasks[id]['title']} - id: {id}: {res.status_code}</yellow>")
            await asyncio.sleep(random.uniform(3, 6))


    async def run(self, proxy: str | None) -> None:
        access_token_created_time = 0
        proxy_conn = ProxyConnector().from_url(proxy) if proxy else None

        headers["User-Agent"] = generate_random_user_agent(device_type='android', browser_type='chrome')
        http_client = CloudflareScraper(headers=headers, connector=proxy_conn)

        session = requests.Session()
        # session1 = requests.Session()

        if proxy:
            proxy_check = await self.check_proxy(http_client=http_client, proxy=proxy)
            if proxy_check:
                proxy_type = proxy.split(':')[0]
                proxies = {
                    proxy_type: proxy
                }
                session.proxies.update(proxies)
                logger.info(f"{self.session_name} | bind with proxy ip: {proxy}")


        token_live_time = randint(3000, 3600)
        while True:
            try:
                if time_module.time() - access_token_created_time >= token_live_time:
                    tg_web_data = await self.get_tg_web_data(proxy=proxy)
                    self.tg_web_data = tg_web_data
                    # await asyncio.sleep(100)
                    access_token_created_time = time_module.time()
                    token_live_time = randint(3000, 3600)

                if self.new_usr:
                    logger.info(f"{self.session_name} | Creating new account...")
                    self.signup(session)
                    self.get_token(session)
                    a = self.get_status_new_user(session)
                    if a:
                        self.complete_ref_task(session)
                        await asyncio.sleep(randint(1, 3))
                        self.get_user_rewards(session)
                    await asyncio.sleep(randint(3, 5))

                    session.cookies.clear_session_cookies()
                else:
                    logger.info(f"{self.session_name} | Attempting to login...")
                    self.login(session)
                    self.get_token(session)
                    a = self.get_status(session)
                    if a:
                        self.get_user_rewards(session)
                        await asyncio.sleep(randint(2, 4))
                        self.get_ref_stats(session)
                    session.cookies.clear_session_cookies()


                if self.logged_in:
                    await self.complete_not_repeat_tasks(session)
                    await self.complete_repeat_tasks(session)


                if self.multi_thread:
                    sleep_ = randint(settings.SLEEP_TIME_BETWEEN_EACH_ROUND[0], settings.SLEEP_TIME_BETWEEN_EACH_ROUND[1])
                    logger.info(f"{self.session_name} | Sleep {sleep_}s...")
                    await asyncio.sleep(sleep_)
                else:
                    await http_client.close()
                    session.close()
                    break
            except InvalidSession as error:
                raise error

            except Exception as error:
                traceback.print_exc()
                logger.error(f"{self.session_name} | Unknown error: {error}")
                await asyncio.sleep(delay=randint(60, 120))


async def run_tapper(tg_client: Client, proxy: str | None):
    try:
        sleep_ = randint(1, 15)
        logger.info(f"{tg_client.name} | start after {sleep_}s")
        await asyncio.sleep(sleep_)
        await Tapper(tg_client=tg_client, multi_thread=True).run(proxy=proxy)
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")


async def run_tapper1(tg_clients: list[Client], proxies):
    proxies_cycle = cycle(proxies) if proxies else None
    while True:
        for tg_client in tg_clients:
            try:
                await Tapper(tg_client=tg_client, multi_thread=False).run(
                    next(proxies_cycle) if proxies_cycle else None)
            except InvalidSession:
                logger.error(f"{tg_client.name} | Invalid Session")

            sleep_ = randint(settings.DELAY_EACH_ACCOUNT[0], settings.DELAY_EACH_ACCOUNT[1])
            logger.info(f"Sleep {sleep_}s...")
            await asyncio.sleep(sleep_)

        sleep_ = randint(settings.SLEEP_TIME_BETWEEN_EACH_ROUND[0], settings.SLEEP_TIME_BETWEEN_EACH_ROUND[1])
        logger.info(f"<red>Sleep {sleep_}s...</red>")
        await asyncio.sleep(sleep_)
