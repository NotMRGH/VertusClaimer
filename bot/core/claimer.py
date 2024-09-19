import asyncio
from urllib.parse import unquote
import requests
import time

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
            response = requests.post(url, headers=headers, json=body, allow_redirects=True)
            response.raise_for_status()
            data = response.json()
            balance = int(data.get("user").get("balance")) / 10 ** 18
            farm_b = data.get("user").get("vertStorage") / 10 ** 18
            pph = data.get("user").get("valuePerHour") / 10 ** 18
            eo = data.get("user").get("earnedOffline") / 10 ** 18
            logger.info(f"Vert Balance: {balance:.3f} | Earned Offline: {eo:.4f}")
            logger.info(f"Farm Balance: {farm_b:.5f} | PPH: {pph:.4f}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

    async def daily_bonus(self):
        url = "https://api.thevertus.app/users/claim-daily"
        headers = await self.get_headers()
        body = {}

        try:
            response = requests.post(url, headers=headers, json=body, allow_redirects=True)
            response.raise_for_status()
            data = response.json()

            success = data.get("success")
            n_balance = data.get("balance") / 10 ** 18 if data.get("balance") is not None else 0
            massage = data.get("msg", "")
            reward = data.get("claimed") / 10 ** 18 if data.get("claimed") is not None else 0
            day = data.get("consecutiveDays", 0)

            if success:
                logger.info(f"Day {day} Daily Bonus {reward} Claimed Successfully")
                logger.info(f"New Balance: {n_balance}")
            else:
                logger.warning(f"{massage}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

    async def ads(self):
        url_1 = "https://api.thevertus.app/missions/check-adsgram"
        headers = await self.get_headers()
        body = {}

        try:
            response = requests.post(url_1, headers=headers, json=body, allow_redirects=True)
            response.raise_for_status()
            data = response.json()
            isSuccess = data.get("isSuccess")
            massage = data.get("msg")

            if isSuccess:
                logger.info("Ads Reward Claiming.....")
                time.sleep(30)
                url_2 = "https://api.thevertus.app/missions/complete-adsgram"
                body_2 = {}
                response_2 = requests.post(url_2, headers=headers, json=body_2, allow_redirects=True)
                response_2.raise_for_status()
                data_2 = response_2.json()

                isSuccess = data_2.get("isSuccess")
                new_balance = data_2.get("newBalance") / 10 ** 18 if data_2.get("newBalance") is not None else 0
                total_claim = data_2.get("completion")

                if isSuccess:
                    new_balance = f"{new_balance:.3f}"
                    logger.info("Ads Reward Claimed Successfully")
                    logger.info(f"New Balance: {new_balance} | Total Claim: {total_claim} times")
                else:
                    logger.warning(f"{data_2}")

            else:
                logger.warning(f"{massage}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

    async def get_task(self):
        get_task_url = "https://api.thevertus.app/missions/get"
        headers = await self.get_headers()
        body = {"isPremium": False, "languageCode": "en"}
        id_list = []
        task_title = []

        try:
            response = requests.post(get_task_url, headers=headers, json=body, allow_redirects=True)
            response.raise_for_status()
            data = response.json()

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
                        logger.warning(f"Unexpected type in sponsors2: {type(sponsor2)}")
            else:
                logger.warning(f"Unexpected type for sponsors2: {type(sponsors2)}")

            communitys = data.get('community', [])
            for community_list in communitys:
                for community in community_list:
                    id_list.append(community.get('_id'))
                    task_title.append(community.get('title'))

            recommendations = data.get('recommendations', {}).get('missions', [])
            for mission in recommendations:
                id_list.append(mission.get('_id'))
                task_title.append(mission.get('title'))

            return id_list, task_title

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            return [], []

    async def comp_task(self, id_list, task_title):
        url = "https://api.thevertus.app/missions/complete"
        headers = await self.get_headers()

        try:
            response = requests.post("https://api.thevertus.app/users/get-data", headers=headers, json={},
                                     allow_redirects=True)
            response.raise_for_status()
            data = response.json()
            initial_balance = int(data.get("user").get("balance")) / 10 ** 18
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get initial balance: {e}")
            return

        for mission_id, title in zip(id_list, task_title):
            body = {"missionId": mission_id}

            try:
                response = requests.post(url, headers=headers, json=body, allow_redirects=True)
                response.raise_for_status()
                data = response.json()
                new_balance = data.get("newBalance") / 10 ** 18

                if new_balance > initial_balance:
                    logger.info(f"Task Complete: {title}")
                    logger.info(f"New Balance: {new_balance:.4f}")
                else:
                    logger.warning(f"Task Already Completed: {title}")

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed for missionId {mission_id} ({title}): {e}")
                if response:
                    logger.error(f"Response content: {response.text}")

    async def upgrade_farm(self):
        url = "https://api.thevertus.app/users/upgrade"
        headers = await self.get_headers()
        body = {"upgrade": "farm"}

        try:
            response = requests.post(url, headers=headers, json=body, allow_redirects=True)
            response.raise_for_status()
            data = response.json()

            success = data.get("success")
            message = data.get("msg")

            abilities = data.get("abilities", {})
            farm = abilities.get("farm", {})
            farm_lvl = farm.get("level", "Unknown")
            farm_des = farm.get("description", "No description available")
            new_balance = data.get("newBalance")

            a_b = new_balance / 10 ** 18 if new_balance is not None else 0

            if success:
                logger.info("Farm Upgrade Successful")
                logger.info(f"Farm New Level: {farm_lvl} | Farm Ability: {farm_des}")
                logger.info(f"Available Balance: {a_b:.3f}")
            else:
                logger.error(f"Upgrade Failed: {message}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

    async def upgrade_storage(self):
        url = "https://api.thevertus.app/users/upgrade"
        headers = await self.get_headers()
        body = {"upgrade": "storage"}

        try:
            response = requests.post(url, headers=headers, json=body, allow_redirects=True)
            response.raise_for_status()
            data = response.json()

            success = data.get("success")
            message = data.get("msg")

            abilities = data.get("abilities", {})
            storage = abilities.get("storage", {})
            storage_lvl = storage.get("level", "Unknown")
            storage_des = storage.get("description", "No description available")
            new_balance = data.get("newBalance")

            a_b = new_balance / 10 ** 18 if new_balance is not None else 0

            if success:
                logger.info("Storage Upgrade Successful")
                logger.info(f"Storage New Level: {storage_lvl} | Storage Ability: {storage_des}")
                logger.info(f"Available Balance: {a_b:.3f}")
            else:
                logger.info(f"Upgrade Failed: {message}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

    async def upgrade_population(self):
        url = "https://api.thevertus.app/users/upgrade"
        headers = await self.get_headers()
        body = {"upgrade": "population"}

        try:
            response = requests.post(url, headers=headers, json=body, allow_redirects=True)
            response.raise_for_status()
            data = response.json()

            success = data.get("success")
            message = data.get("msg")

            abilities = data.get("abilities", {})
            population = abilities.get("population", {})
            population_lvl = population.get("level", "Unknown")
            population_des = population.get("description", "No description available")
            new_balance = data.get("newBalance")

            a_b = new_balance / 10 ** 18 if new_balance is not None else 0

            if success:
                logger.info("Population Upgrade Successful")
                logger.info(f"Population New Level: {population_lvl} | Population Ability: {population_des}")
                logger.info(f"Available Balance: {a_b:.3f}")
            else:
                logger.info(f"Upgrade Failed: {message}")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

    async def get_cards(self):
        url = "https://api.thevertus.app/upgrade-cards"
        headers = await self.get_headers()
        card_details = []

        try:
            response = requests.get(url, headers=headers, allow_redirects=True)
            response.raise_for_status()
            data = response.json()

            for category in ['economyCards', 'militaryCards', 'scienceCards']:
                for card in data.get(category, []):
                    card_id = card['_id']
                    card_name = card.get('cardName', 'Unknown Name')
                    card_details.append((card_id, card_name))

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")

        return card_details

    async def post_card_upgrade(self, card_id, card_name):
        url = "https://api.thevertus.app/upgrade-cards/upgrade"
        headers = {'Authorization': f'Bearer {self.token}'}
        body = {"cardId": card_id}

        try:
            response = requests.post(url, headers=headers, json=body)
            response.raise_for_status()
            data = response.json()

            success = data.get("isSuccess")
            message = data.get("msg")

            balance_str = data.get("balance")
            new_pph_str = data.get("newValuePerHour")

            if balance_str is not None:
                try:
                    a_balance = int(balance_str) / 10 ** 18
                except (ValueError, TypeError):
                    a_balance = "Invalid balance value"
            else:
                a_balance = "Balance not provided"

            if new_pph_str is not None:
                try:
                    new_pph = int(new_pph_str) / 10 ** 18
                except (ValueError, TypeError):
                    new_pph = "Invalid new PPH value"
            else:
                new_pph = "New PPH not provided"

            if success:
                logger.info(f"{card_name} Card Upgrade Successful")
                logger.info(f"Available Balance: {a_balance}")
                logger.info(f"New PPH: {new_pph}")
            else:
                logger.error(f"{message}")
                logger.error(f"{card_name} Card Upgrade Failed")

        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for card ID {card_id}, Card Name: {card_name}: {e}")

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
                        await self.comp_task(task_ids, task_titles)
                    else:
                        logger.warning("No tasks available.")
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
            logger.info("sleeping for 1800 seconds")
            await asyncio.sleep(delay=1800)


async def run_claimer(tg_client: Client):
    try:
        await Claimer(tg_client=tg_client).run()
    except InvalidSession:
        logger.error(f"{tg_client.name} | Invalid Session")
