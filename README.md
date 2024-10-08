## Functionality
| Functional                                            | Supported |
|-------------------------------------------------------|:---------:|
| Multithreading                                        |     ✅     |
| Proxy binding to session                              |     ✅     |
| Auto Referral                                         |     ✅     |
| Auto-complete tasks (sponsor, community, ads)         |     ✅     |
| Auto-collect storage                                  |     ✅     |
| Upgrade farm                                          |     ✅     |
| Upgrade storage                                       |     ✅     |
| Upgrade population                                    |     ✅     |
| Upgrade cards                                         |     ✅     |
| Support tdata / pyrogram .session / telethon .session |     ✅     |

## [Settings](https://github.com/NotMRGH/VertusClaimer/blob/master/.env-example)
| Setup                       | Description                                                                                                                                |
|-----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------|
| **API_ID / API_HASH**       | Platform data from which to launch a Telegram session (stock - Android)                                                                    |
| **USE_RANDOM_DELAY_IN_RUN** | Whether to use random delay at startup (True / False)                                                                                      |
| **RANDOM_DELAY_IN_RUN**     | Random delay at startup (e.g. [0, 15])                                                                                                     |
| **COMPLETE_TASK**           | Auto complete tasks (True / False)                                                                                                         |
| **UPGRADE_FARM**            | Auto upgrade farm (True / False)                                                                                                           |
| **UPGRADE_POPULATION**      | Auto population (True / False)                                                                                                             |
| **UPGRADE_CARDS**           | Auto cards (True / False)                                                                                                                  |
| **MAX_UPGRADE_CARDS_PRICE** | Determines the maximum amount the bot can spend on purchasing cards if it has sufficient balance. _(e.g. 20)_                              |
| **MINIMUM_BALANCE**         | This parameter defines the minimum balance that the bot is guaranteed to keep without spending it on upgrades or purchases. _(disable -1)_ |
| **SLEEP_TIME**              | Pauses the bot in second for each session after completing all operations. This is to replicate human activity. _(e.g. 1800)_              |
| **FAKE_USERAGENT**          | When this option is enabled, the bot will use random User-Agents for each account. This is to replicate human activity. (True / False)     |
| **USE_REF_ID**              | Use Referral system (True / False)                                                                                                         |
| **REF_ID**                  | Your referral id after startapp= (Your telegram ID)                                                                                        |
| **USE_PROXY_FROM_FILE**     | Whether to use a proxy from the `bot/config/proxies.txt` file (True / False)                                                               |

## Installation
You can download [**Repository**](https://github.com/NotMRGH/VertusClaimer) by cloning it to your system and installing the necessary dependencies:
```shell
~ >>> git clone https://github.com/NotMRGH/VertusClaimer.git
~ >>> cd VertusClaimer

# If you are using Telethon sessions, then clone the "converter" branch
~ >>> git clone https://github.com/NotMRGH/VertusClaimer.git -b converter
~ >>> cd VertusClaimer

#Linux
~/VertusClaimer >>> python3.10 -m venv venv
~/VertusClaimer >>> source venv/bin/activate
~/VertusClaimer >>> python3.10 -m pip install -r requirements.txt
~/VertusClaimer >>> cp .env-example .env
~/VertusClaimer >>> nano .env # Here you must specify your API_ID and API_HASH , the rest is taken by default
~/VertusClaimer >>> python3.10 main.py

#Windows
~/VertusClaimer >>> python -m venv venv
~/VertusClaimer >>> venv\Scripts\activate
~/VertusClaimer >>> pip install -r requirements.txt
~/VertusClaimer >>> copy .env-example .env
~/VertusClaimer >>> # Specify your API_ID and API_HASH, the rest is taken by default
~/VertusClaimer >>> python main.py
```

Also for quick launch you can use arguments, for example:
```shell
~/VertusClaimer >>> python3.10 main.py --action (1/2)
# Or
~/VertusClaimer >>> python3.10 main.py -a (1/2)

#1 - Create session
#2 - Run clicker
```
