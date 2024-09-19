from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_ignore_empty=True)

    API_ID: int
    API_HASH: str
    COMPLETE_TASK: bool = False
    UPGRADE_FARM: bool = False
    UPGRADE_STORAGE: bool = False
    UPGRADE_POPULATION: bool = False
    UPGRADE_CARDS: bool = False


settings = Settings()
