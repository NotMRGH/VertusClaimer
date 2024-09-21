## Functionality
| Functional                                            | Supported |
|-------------------------------------------------------|:---------:|
| Multithreading                                        |     ✅     |
| Auto-complete tasks (sponsor, community, ads)         |     ✅     |
| Upgrade farm                                          |     ✅     |
| Upgrade storage                                       |     ✅     |
| Upgrade population                                    |     ✅     |
| Upgrade cards                                         |     ✅     |
| Support tdata / pyrogram .session / telethon .session |     ✅     |

## [Settings](https://github.com/NotMRGH/VertusClaimer/blob/master/.env-example)
| Setup                       | Description                                                                                                 |
|-----------------------------|-------------------------------------------------------------------------------------------------------------|
| **API_ID / API_HASH**       | Platform data from which to launch a Telegram session (stock - Android)                                     |
| **COMPLETE_TASK**           | Auto complete tasks (True / False)                                                                          |
| **UPGRADE_FARM**            | Auto upgrade farm (True / False)                                                                            |
| **UPGRADE_POPULATION**      | Auto population (True / False)                                                                              |
| **UPGRADE_CARDS**           | Auto cards (True / False)                                                                                   |
| **MAX_UPGRADE_CARDS_PRICE** | Determines the maximum amount the bot can spend on purchasing cards if it has sufficient balance. _(eg 20)_ |

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
