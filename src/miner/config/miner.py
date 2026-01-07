import os
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from pydantic import Field, model_validator, field_validator
from pydantic_settings import SettingsConfigDict

from redteam_core.config import BaseConfig, ENV_PREFIX_MINER, ENV_PREFIX


class MinerMainConfig(BaseConfig):
    WALLET_DIR: str = Field(
        default="~/.bittensor/wallets",
        min_length=2,
        description="Directory where wallets are stored",
    )
    WALLET_NAME: str = Field(
        default="miner", description="Name of the wallet to use for mining."
    )
    HOTKEY_NAME: str = Field(
        default="default", description="Name of the hotkey to use for mining."
    )
    # HOTKEY_ADDRESS: Optional[str] = Field(
    #     default=None,
    #     description="SS58 address of the hotkey to use for mining (overrides HOTKEY_NAME if set)",
    # )
    AXON_PORT: int = Field(
        default=8091,
        description="Port on which the axon will listen for incoming connections.",
    )
    DATA_DIR: str = Field(
        default="/var/lib/agent-miner",
        min_length=1,
        description="Path to store miner data.",
    )
    COMMIT_STORAGE_DIR: str = Field(
        default="{data_dir}/commits",
        min_length=3,
        description="Path to store commit data for the miner.",
    )

    @field_validator("WALLET_DIR")
    @classmethod
    def _check_wallet_dir(cls, val: str) -> str:

        _wallet_dir_env = f"{ENV_PREFIX}BTCLI_WALLET_DIR"
        if _wallet_dir_env in os.environ:
            val = os.getenv(_wallet_dir_env, "")

        if "~" in val:
            val = os.path.expanduser(val)

        return val

    @model_validator(mode="after")
    def _check_all(self) -> Self:

        if not os.path.isdir(self.DATA_DIR):
            os.makedirs(self.DATA_DIR, exist_ok=True)

        if "{data_dir}" in self.COMMIT_STORAGE_DIR:
            self.COMMIT_STORAGE_DIR = self.COMMIT_STORAGE_DIR.format(
                data_dir=self.DATA_DIR
            )

        if not os.path.isdir(self.COMMIT_STORAGE_DIR):
            os.makedirs(self.COMMIT_STORAGE_DIR, exist_ok=True)

        return self

    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX_MINER)


__all__ = [
    "MinerMainConfig",
]
