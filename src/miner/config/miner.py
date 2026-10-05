import os
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from pydantic import Field, model_validator
from pydantic_settings import SettingsConfigDict
from redteam_core.config import BaseConfig, ENV_PREFIX_MINER


class MinerMainConfig(BaseConfig):
    WALLET_DIR: str = Field(
        default="~/.bittensor/wallets",
        min_length=2,
        validation_alias="RT_BTCLI_WALLET_DIR",
    )
    WALLET_NAME: str = Field(default="miner", min_length=1)
    HOTKEY_NAME: str = Field(default="default", min_length=1)
    DATA_DIR: str = Field(default="/var/lib/agent-miner", min_length=1)
    CONFIG_DIR: str = Field(default="/etc/agent-miner", min_length=1)
    COMMIT_STORAGE_DIR: str = Field(default="{data_dir}/commits", min_length=3)
    COMMIT_FILE_PATH: str | None = Field(
        default="{config_dir}/active_commit.yaml", min_length=1
    )
    PAT_FILE_PATH: str | None = Field(
        default="{config_dir}/personal_access_token.txt", min_length=1
    )
    CORE_API_URL: str = Field(
        default="https://storage-api.theredteam.io/api/v1",
        min_length=8,
    )
    CORE_API_TIMEOUT: float = Field(default=10.0, gt=0, le=120)
    SYNC_INTERVAL: float = Field(default=3600 * 24, gt=0, le=3600 * 24)
    METAGRAPH_SYNC_INTERVAL: float = Field(default=600.0, gt=0, le=86400)
    MAX_RETRY_DELAY: float = Field(default=300.0, gt=0, le=3600)

    @model_validator(mode="after")
    def _resolve_paths(self) -> Self:
        self.WALLET_DIR = os.path.expanduser(self.WALLET_DIR)
        self.DATA_DIR = os.path.expanduser(self.DATA_DIR)
        self.CONFIG_DIR = os.path.expanduser(self.CONFIG_DIR)

        if "{data_dir}" in self.COMMIT_STORAGE_DIR:
            self.COMMIT_STORAGE_DIR = self.COMMIT_STORAGE_DIR.format(
                data_dir=self.DATA_DIR
            )
        if "{config_dir}" in self.COMMIT_FILE_PATH:
            self.COMMIT_FILE_PATH = self.COMMIT_FILE_PATH.format(
                config_dir=self.CONFIG_DIR
            )
        if "{config_dir}" in self.PAT_FILE_PATH:
            self.PAT_FILE_PATH = self.PAT_FILE_PATH.format(config_dir=self.CONFIG_DIR)

        self.COMMIT_STORAGE_DIR = os.path.expanduser(self.COMMIT_STORAGE_DIR)
        self.COMMIT_FILE_PATH = os.path.expanduser(self.COMMIT_FILE_PATH)
        self.PAT_FILE_PATH = os.path.expanduser(self.PAT_FILE_PATH)

        self.CORE_API_URL = self.CORE_API_URL.rstrip("/")
        return self

    model_config = SettingsConfigDict(env_file=".env", env_prefix=ENV_PREFIX_MINER)


__all__ = ["MinerMainConfig"]
