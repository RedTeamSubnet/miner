from typing import Optional
from pydantic import Field
from pydantic_settings import SettingsConfigDict

from redteam_core.config import BaseConfig, ENV_PREFIX_MINER


class MinerMainConfig(BaseConfig):
    WALLET_NAME: str = Field(
        default="miner", description="Name of the wallet to use for mining"
    )
    HOTKEY_NAME: str = Field(
        default="default", description="Name of the hotkey to use for mining"
    )
    HOTKEY_ADDRESS: Optional[str] = Field(
        default=None,
        description="SS58 address of the hotkey to use for mining (overrides HOTKEY_NAME if set)",
    )
    COMMIT_STORAGE_DIR: str = Field(
        default="/var/lib/agent-miner/commits",
        description="Path to store commit data for the miner",
    )
    AXON_PORT: int = Field(
        default=8091,
        description="Port on which the axon will listen for incoming connections",
    )
    model_config = SettingsConfigDict(env_prefix=ENV_PREFIX_MINER)


__all__ = ["MinerMainConfig"]
