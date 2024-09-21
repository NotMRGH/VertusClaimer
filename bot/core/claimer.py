import asyncio
from urllib.parse import unquote
import aiohttp

from pyrogram import Client
from pyrogram.errors import Unauthorized, UserDeactivated, AuthKeyUnregistered
from pyrogram.raw.functions.messages import RequestWebView

from bot.utils import logger
from bot.config import settings
from bot.exceptions import InvalidSession


class Claimer:
    def __init__(self, tg_client: Client):
        self.session_name = tg_client.name
        self.tg_client = tg_client
        self.token = None
        self.balance = None

    async def get_tg_web_data(self) -> str:
        try:
            if not self.tg_client.is_connected:
                try:
                    await self.tg_client.connect()
                except (Unauthorized, UserDeactivated, AuthKeyUnregistered):
                    raise InvalidSession(self.session_name)

            peer = await self.tg_client.resolve_peer('Vertus_App_bot')
            web_view = await self.tg_client.invoke(RequestWebView(
                peer=peer,
                bot=peer,
                platform='android',
                from_bot_menu=False,
                url='https://thevertus.app/'
            ))

            auth_url = web_view.url
            tg_web_data = unquote(
                string=auth_url.split('tgWebAppData=', maxsplit=1)[1].split('&tgWebAppVersion', maxsplit=1)[0])

            if self.tg_client.is_connected:
                await self.tg_client.disconnect()

            return tg_web_data

        except InvalidSession as error:
            raise error

        except Exception as error:
            logger.error(f"{self.session_name} | Unknown error during Authorization: {error}")
            await asyncio.sleep(delay=3)

    async def get_headers(self):
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "authorization": f"Bearer {self.token}",
            "content-type": "application/json",
            "sec-ch-ua": "\"Chromium\";v=\"111\", \"Not(A:Brand\";v=\"8\"",
            "sec-ch-ua-mobile": "?1",
            "sec-ch-ua-platform": "\"Android\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site"
        }

    async def login(self):
        url = "https://api.thevertus.app/users/get-data"
        headers = await self.get_headers()
        body = {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body) as response:
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

    async def daily_bonus(self):
        url = "https://api.thevertus.app/users/claim-daily"
        headers = await self.get_headers()
        body = {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body) as response:
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

    async def ads(self):
        url_1 = "https://api.thevertus.app/missions/check-adsgram"
        headers = await self.get_headers()
        body = {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url_1, headers=headers, json=body) as response:
                    data = await response.json()
                    is_success = data.get("isSuccess")
                    message = data.get("msg")

                    if is_success:
                        logger.info(f"{self.session_name} | Ads Reward Claiming.....")
                        await asyncio.sleep(30)
                        url_2 = "https://api.thevertus.app/missions/complete-adsgram"
                        async with session.post(url_2, headers=headers, json={}) as response_2:
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

    async def get_task(self):
        url = "https://api.thevertus.app/missions/get"
        headers = await self.get_headers()
        body = {"isPremium": False, "languageCode": "en"}
        id_list = []
        task_title = []

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=body) as response:
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

    async def complete_task(self, id_list, task_title):
        url = "https://api.thevertus.app/missions/complete"
        headers = await self.get_headers()

        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post("https://api.thevertus.app/users/get-data", headers=headers, json={})
                response.raise_for_status()
                data = await response.json()
                initial_balance = int(data.get("user").get("balance")) / 10 ** 18

            for mission_id, title in zip(id_list, task_title):
                body = {"missionId": mission_id}
                response = await session.post(url, headers=headers, json=body)
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

    async def upgrade_farm(self):
        url = "https://api.thevertus.app/users/upgrade"
        headers = await self.get_headers()
        body = {"upgrade": "farm"}

        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(url, headers=headers, json=body)
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

    async def upgrade_storage(self):
        url = "https://api.thevertus.app/users/upgrade"
        headers = await self.get_headers()
        body = {"upgrade": "storage"}

        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(url, headers=headers, json=body)
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

    async def upgrade_population(self):
        url = "https://api.thevertus.app/users/upgrade"
        headers = await self.get_headers()
        body = {"upgrade": "population"}

        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(url, headers=headers, json=body)
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

    async def get_cards(self):
        url = "https://api.thevertus.app/upgrade-cards"
        headers = await self.get_headers()
        card_details = []

        try:
            async with aiohttp.ClientSession() as session:
                response = await session.get(url, headers=headers)
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

    async def post_card_upgrade(self, card_id, card_name):
        url = "https://api.thevertus.app/upgrade-cards/upgrade"
        headers = await self.get_headers()
        body = {"cardId": card_id}

        try:
            async with aiohttp.ClientSession() as session:
                response = await session.post(url, headers=headers, json=body)
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
        while True:
            try:
                tg_web_data = await self.get_tg_web_data()
                self.token = tg_web_data
                if not tg_web_data:
                    return

                await self.login()
                await self.daily_bonus()
                await self.ads()

                if settings.COMPLETE_TASK:
                    task_ids, task_titles = await self.get_task()
                    if task_ids:
                        await self.complete_task(task_ids, task_titles)
                    else:
                        logger.warning(f"{self.session_name} | No tasks available.")
                    await asyncio.sleep(2)

                if settings.UPGRADE_FARM:
                    await self.upgrade_farm()

                if settings.UPGRADE_STORAGE:
                    await self.upgrade_storage()

                if settings.UPGRADE_POPULATION:
                    await self.upgrade_population()

                if settings.UPGRADE_CARDS:
                    card_details = await self.get_cards()
                    for card_id, card_name in card_details:
                        await self.post_card_upgrade(card_id, card_name)

            except InvalidSession as error:
                raise error
            logger.info(f"{self.session_name} | sleeping for 1800 seconds")
            await asyncio.sleep(delay=1800)


async def run_claimer(tg_client: Client):
    try:
        await Claimer(tg_client=tg_client).run()
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
