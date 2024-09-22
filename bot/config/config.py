from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str
    USE_RANDOM_DELAY_IN_RUN: bool = True
    RANDOM_DELAY_IN_RUN: list[int] = [0, 15]
    COMPLETE_TASK: bool = False
    UPGRADE_FARM: bool = False
    UPGRADE_STORAGE: bool = False
    UPGRADE_POPULATION: bool = False
    UPGRADE_CARDS: bool = False
    MAX_UPGRADE_CARDS_PRICE: int = 20
    MINIMUM_BALANCE: int = -1
    SLEEP_TIME: int = 1800
    USE_PROXY_FROM_FILE: bool = False


settings = Settings()
