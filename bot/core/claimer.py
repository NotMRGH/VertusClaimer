import asyncio
from urllib.parse import unquote
import aiohttp
import random
from aiohttp_proxy import ProxyConnector

from pyrogram import Client
from better_proxy import Proxy
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
from .agents import generate_random_user_agent

from bot.utils import logger
from bot.config import settings
from bot.exceptions import InvalidSession
from .headers import headers


class Claimer:
    def __init__(self, tg_client: Client, proxy: str):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.token = None
        self.proxy = proxy
        self.balance = None
        self.ref_id = None

    async def check_proxy(self, http_client: aiohttp.ClientSession) -> None:
        response = await http_client.get("https://httpbin.org/ip", timeout=aiohttp.ClientTimeout(5))
        response.raise_for_status()
        data = await response.json()

        ip = data.get('origin')
        logger.info(f"{self.session_name} | Proxy IP: {ip}")

    async def get_tg_web_data(self) -> str:
        if self.proxy:
            proxy = Proxy.from_str(self.proxy)
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
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            peer = await self.tg_client.resolve_peer('Vertus_App_bot')
            if settings.USE_REF_ID:
                self.ref_id = settings.REF_ID
            else:
                self.ref_id = "5527112150"

            web_view = await self.tg_client.invoke(RequestAppWebView(
                peer=peer,
                app=InputBotAppShortName(bot_id=peer, short_name="app"),
                platform='android',
                write_allowed=True,
                start_param=self.ref_id
            ))

            auth_url = web_view.url
            tg_web_data = unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def login(self, http_client: aiohttp.ClientSession):
        is_first = False
        try:
            async with http_client.get("https://api3.thevertus.app/balance") as response:
                response.raise_for_status()
                data = await response.json()
                data = data.get("tonResponse")
                data = data.get("isSuccess")
                if not data:
                    is_first = True
        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request balance: {e}")

        body = {}
        if is_first:
            try:
                async with http_client.post("https://api.thevertus.app/users/create-wallet", json=body) as response:
                    data = await response.json()
                    if not data.get("walletAddress"):
                        return
            except Exception as e:
                logger.error(f"{self.session_name} | Failed to Request create-wallet: {e}")

            try:
                async with http_client.get("https://api.thevertus.app/queue/check") as response:
                    response.raise_for_status()
                    data = await response.json()
                    data = data.get("isSuccess")
                    if not data:
                        return
            except Exception as e:
                logger.error(f"{self.session_name} | Failed to Request check: {e}")

            try:
                async with http_client.post("https://api.thevertus.app/game-service/collect-first",
                                            json=body) as response:
                    data = await response.json()
                    if not data.get("newBalance"):
                        return
            except Exception as e:
                logger.error(f"{self.session_name} | Failed to Request collect-first: {e}")

        try:
            async with http_client.post("https://api.thevertus.app/users/get-data", json=body) as response:
                data = await response.json()
                balance = int(data.get("user").get("balance")) / 10 ** 18
                self.balance = balance
                farm_b = data.get("user").get("vertStorage") / 10 ** 18
                pph = data.get("user").get("valuePerHour") / 10 ** 18
                eo = data.get("user").get("earnedOffline") / 10 ** 18
                logger.info(f"{self.session_name} | Vert Balance: {balance:.3f} | Earned Offline: {eo:.4f}")
                logger.info(f"{self.session_name} | Farm Balance: {farm_b:.5f} | PPH: {pph:.4f}")
        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request login: {e}")

    async def collect(self, http_client: aiohttp.ClientSession):
        url = "https://api.thevertus.app/game-service/collect"
        body = {}

        try:
            async with http_client.post(url, json=body) as response:
                data = await response.json()
                new_balance = data.get("newBalance")
                a_b = new_balance / 10 ** 18 if new_balance is not None else 0
                self.balance = a_b
                logger.info(f"{self.session_name} | Collecting from storage")
                logger.info(f"{self.session_name} | New vert Balance: {a_b:.3f}")
        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request login: {e}")

    async def daily_bonus(self, http_client: aiohttp.ClientSession):
        url = "https://api.thevertus.app/users/claim-daily"
        body = {}

        try:
            async with http_client.post(url, json=body) as response:
                data = await response.json()
                success = data.get("success")
                n_balance = data.get("balance") / 10 ** 18 if data.get("balance") is not None else 0
                self.balance = n_balance
                message = data.get("msg", "")
                reward = data.get("claimed") / 10 ** 18 if data.get("claimed") is not None else 0
                day = data.get("consecutiveDays", 0)

                if success:
                    logger.info(f"{self.session_name} | Day {day} Daily Bonus {reward} Claimed Successfully")
                    logger.info(f"{self.session_name} | New Balance: {n_balance}")
                else:
                    logger.warning(f"{self.session_name} | {message}")
        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request dailyBonus: {e}")

    async def ads(self, http_client: aiohttp.ClientSession):
        url_1 = "https://api.thevertus.app/missions/check-adsgram"
        body = {}

        try:
            async with http_client.post(url_1, json=body) as response:
                data = await response.json()
                is_success = data.get("isSuccess")
                message = data.get("msg")

                if is_success:
                    logger.info(f"{self.session_name} | Ads Reward Claiming.....")
                    await asyncio.sleep(30)
                    url_2 = "https://api.thevertus.app/missions/complete-adsgram"
                    async with http_client.post(url_2, json={}) as response_2:
                        data_2 = await response_2.json()
                        is_success = data_2.get("isSuccess")
                        new_balance = data_2.get("newBalance") / 10 ** 18 if data_2.get(
                            "newBalance") is not None else 0
                        self.balance = new_balance
                        total_claim = data_2.get("completion")

                        if is_success:
                            logger.info(f"{self.session_name} | Ads Reward Claimed Successfully")
                            logger.info(
                                f"{self.session_name} | New Balance: {new_balance:.3f} | Total Claim: {total_claim} times")
                        else:
                            logger.warning(f"{self.session_name} | {data_2}")
                else:
                    logger.warning(f"{message}")
        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request ads: {e}")

    async def get_task(self, http_client: aiohttp.ClientSession):
        url = "https://api.thevertus.app/missions/get"
        body = {"isPremium": False, "languageCode": "en"}
        id_list = []
        task_title = []

        try:
            async with http_client.post(url, json=body) as response:
                data = await response.json()
                groups = data.get('groups', [])
                for group in groups:
                    for mission_list in group.get('missions', []):
                        for mission in mission_list:
                            id_list.append(mission.get('_id'))
                            task_title.append(mission.get('title'))

                sponsors = data.get('sponsors', [])
                for sponsor_list in sponsors:
                    for sponsor in sponsor_list:
                        id_list.append(sponsor.get('_id'))
                        task_title.append(sponsor.get('title'))

                sponsors2 = data.get('sponsors2', [])
                if isinstance(sponsors2, list):
                    for sponsor2 in sponsors2:
                        if isinstance(sponsor2, dict):
                            id_list.append(sponsor2.get('_id'))
                            task_title.append(sponsor2.get('title'))
                        else:
                            logger.warning(
                                f"{self.session_name} | Unexpected type in sponsors2: {type(sponsor2)}")
                else:
                    logger.warning(f"{self.session_name} | Unexpected type for sponsors2: {type(sponsors2)}")

                community = data.get('community', [])
                for community_list in community:
                    for community in community_list:
                        id_list.append(community.get('_id'))
                        task_title.append(community.get('title'))

                recommendations = data.get('recommendations', {}).get('missions', [])
                for mission in recommendations:
                    id_list.append(mission.get('_id'))
                    task_title.append(mission.get('title'))

                return id_list, task_title
        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request getTask: {e}")
            return [], []

    async def complete_task(self, id_list, task_title, http_client: aiohttp.ClientSession):
        url = "https://api.thevertus.app/missions/complete"

        try:
            response = await http_client.post("https://api.thevertus.app/users/get-data", json={})
            response.raise_for_status()
            data = await response.json()
            initial_balance = int(data.get("user").get("balance")) / 10 ** 18

            for mission_id, title in zip(id_list, task_title):
                body = {"missionId": mission_id}
                response = await http_client.post(url, json=body)
                response.raise_for_status()
                data = await response.json()
                new_balance = data.get("newBalance") / 10 ** 18
                self.balance = new_balance

                if new_balance > initial_balance:
                    logger.info(f"{self.session_name} | Task Complete: {title}")
                    logger.info(f"{self.session_name} | New Balance: {new_balance:.4f}")
                else:
                    logger.warning(f"{self.session_name} | Task Already Completed: {title}")

        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request completeTask: {e}")

    async def upgrade_farm(self, http_client: aiohttp.ClientSession):
        url = "https://api.thevertus.app/users/upgrade"
        body = {"upgrade": "farm"}

        if settings.MINIMUM_BALANCE != -1:
            if float(self.balance) <= settings.MINIMUM_BALANCE:
                return
        try:
            response = await http_client.post(url, json=body)
            response.raise_for_status()
            data = await response.json()

            success = data.get("success")
            message = data.get("msg")

            abilities = data.get("abilities", {})
            farm = abilities.get("farm", {})
            farm_lvl = farm.get("level", "Unknown")
            farm_des = farm.get("description", "No description available")
            new_balance = data.get("newBalance")

            a_b = new_balance / 10 ** 18 if new_balance is not None else 0
            self.balance = a_b

            if success:
                logger.info(f"{self.session_name} | Farm Upgrade Successful")
                logger.info(f"{self.session_name} | Farm New Level: {farm_lvl} | Farm Ability: {farm_des}")
                logger.info(f"{self.session_name} | Available Balance: {a_b:.3f}")
            else:
                logger.error(f"{self.session_name} | Upgrade Failed: {message}")
        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request upgradeFarm: {e}")

    async def upgrade_storage(self, http_client: aiohttp.ClientSession):
        url = "https://api.thevertus.app/users/upgrade"
        body = {"upgrade": "storage"}

        if settings.MINIMUM_BALANCE != -1:
            if float(self.balance) <= settings.MINIMUM_BALANCE:
                return
        try:
            response = await http_client.post(url, json=body)
            response.raise_for_status()
            data = await response.json()

            success = data.get("success")
            message = data.get("msg")

            abilities = data.get("abilities", {})
            storage = abilities.get("storage", {})
            storage_lvl = storage.get("level", "Unknown")
            storage_des = storage.get("description", "No description available")
            new_balance = data.get("newBalance")

            a_b = new_balance / 10 ** 18 if new_balance is not None else 0
            self.balance = a_b

            if success:
                logger.info(f"{self.session_name} | Storage Upgrade Successful")
                logger.info(
                    f"{self.session_name} | Storage New Level: {storage_lvl} | Storage Ability: {storage_des}")
                logger.info(f"{self.session_name} | Available Balance: {a_b:.3f}")
            else:
                logger.info(f"{self.session_name} | Upgrade Failed: {message}")

        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request upgradeStorage: {e}")

    async def upgrade_population(self, http_client: aiohttp.ClientSession):
        url = "https://api.thevertus.app/users/upgrade"
        body = {"upgrade": "population"}

        if settings.MINIMUM_BALANCE != -1:
            if float(self.balance) <= settings.MINIMUM_BALANCE:
                return
        try:
            response = await http_client.post(url, json=body)
            response.raise_for_status()
            data = await response.json()

            success = data.get("success")
            message = data.get("msg")

            abilities = data.get("abilities", {})
            population = abilities.get("population", {})
            population_lvl = population.get("level", "Unknown")
            population_des = population.get("description", "No description available")
            new_balance = data.get("newBalance")

            a_b = new_balance / 10 ** 18 if new_balance is not None else 0
            self.balance = a_b

            if success:
                logger.info(f"{self.session_name} | Population Upgrade Successful")
                logger.info(
                    f"{self.session_name} | Population New Level: {population_lvl} | Population Ability: {population_des}")
                logger.info(f"{self.session_name} | Available Balance: {a_b:.3f}")
            else:
                logger.info(f"{self.session_name} | Upgrade Failed: {message}")

        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request upgradePopulation: {e}")

    async def get_cards(self, http_client: aiohttp.ClientSession):
        url = "https://api.thevertus.app/upgrade-cards"
        card_details = []

        try:
            response = await http_client.get(url)
            response.raise_for_status()
            data = await response.json()

            for category in ['economyCards', 'militaryCards', 'scienceCards']:
                for card in data.get(category, []):
                    next_value = card.get('nextValue', 0)
                    for level in card.get('levels', []):
                        if next_value != level.get('value', 0):
                            continue
                        cost = level.get('cost', 0) / 10 ** 18
                        if cost > settings.MAX_UPGRADE_CARDS_PRICE:
                            continue
                        if cost > self.balance:
                            continue
                        card_id = card['_id']
                        card_name = card.get('cardName', 'Unknown Name')
                        card_details.append((card_id, card_name))
                        break

        except Exception as e:
            logger.error(f"{self.session_name} | Failed to Request getCards: {e}")

        return card_details

    async def post_card_upgrade(self, card_id, card_name, http_client: aiohttp.ClientSession):
        url = "https://api.thevertus.app/upgrade-cards/upgrade"
        body = {"cardId": card_id}

        if settings.MINIMUM_BALANCE != -1:
            if float(self.balance) <= settings.MINIMUM_BALANCE:
                return
        try:
            response = await http_client.post(url, json=body)
            response.raise_for_status()
            data = await response.json()

            success = data.get("isSuccess")
            message = data.get("msg")

            balance_str = data.get("balance")
            new_pph_str = data.get("newValuePerHour")

            a_balance = int(balance_str) / 10 ** 18 if balance_str is not None else "Balance not provided"
            self.balance = a_balance
            new_pph = int(new_pph_str) / 10 ** 18 if new_pph_str is not None else "New PPH not provided"

            if success:
                logger.info(f"{self.session_name} | {card_name} Card Upgrade Successful")
                logger.info(f"{self.session_name} | Available Balance: {a_balance}")
                logger.info(f"{self.session_name} | New PPH: {new_pph}")
            else:
                logger.error(f"{self.session_name} | {message}")
                logger.error(f"{self.session_name} | {card_name} Card Upgrade Failed")

        except Exception as e:
            logger.error(f"{self.session_name} | Request failed for card ID {card_id}, Card Name: {card_name}: {e}")

    async def run(self) -> None:
        if settings.USE_RANDOM_DELAY_IN_RUN:
            random_delay = random.randint(settings.RANDOM_DELAY_IN_RUN[0], settings.RANDOM_DELAY_IN_RUN[1])
            logger.info(f"{self.session_name} | Bot will start in <y>{random_delay}s</y>")
            await asyncio.sleep(random_delay)

        tg_web_data = await self.get_tg_web_data()
        self.token = tg_web_data
        if not tg_web_data:
            return

        while True:
            try:
                proxy_conn = ProxyConnector().from_url(self.proxy) if self.proxy else None
                async with aiohttp.ClientSession(headers=headers, connector=proxy_conn) as http_client:
                    http_client.headers['authorization'] = "Bearer " + self.token
                    http_client.headers['referer'] = "https://thevertus.app/?tgWebAppStartParam= " + self.ref_id

                    if self.proxy:
                        await self.check_proxy(http_client=http_client)

                    if settings.FAKE_USERAGENT:
                        http_client.headers['user-agent'] = generate_random_user_agent(device_type='android',
                                                                                       browser_type='chrome')

                    await self.login(http_client=http_client)
                    await self.collect(http_client=http_client)
                    await self.daily_bonus(http_client=http_client)
                    await self.ads(http_client=http_client)

                    if settings.COMPLETE_TASK:
                        task_ids, task_titles = await self.get_task(http_client=http_client)
                        if task_ids:
                            await self.complete_task(task_ids, task_titles, http_client=http_client)
                        else:
                            logger.warning(f"{self.session_name} | No tasks available.")
                        await asyncio.sleep(2)

                    if settings.UPGRADE_FARM:
                        await self.upgrade_farm(http_client=http_client)

                    if settings.UPGRADE_STORAGE:
                        await self.upgrade_storage(http_client=http_client)

                    if settings.UPGRADE_POPULATION:
                        await self.upgrade_population(http_client=http_client)

                    if settings.UPGRADE_CARDS:
                        card_details = await self.get_cards(http_client=http_client)
                        for card_id, card_name in card_details:
                            await self.post_card_upgrade(card_id, card_name, http_client=http_client)

            except InvalidSession as error:
                raise error
            logger.info(f"{self.session_name} | sleeping for {settings.SLEEP_TIME} seconds")
            await asyncio.sleep(delay=settings.SLEEP_TIME)


async def run_claimer(tg_client: Client, proxy: str | None):
    try:
        await Claimer(tg_client=tg_client, proxy=proxy).run()
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
