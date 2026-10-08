from __future__ import annotations

import base64
import json
from pathlib import Path
import threading
from typing import Any
import logging

import bittensor as bt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
import requests
from redteam_core import MainConfig

from .config import MinerMainConfig

logger = logging.getLogger(__name__)


class CoreApiClient:
    def __init__(
        self,
        base_url: str,
        wallet: bt.Wallet,
        *,
        timeout: float = 10.0,
        session: requests.Session | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.wallet = wallet
        self.timeout = timeout
        self.session = session or requests.Session()
        self._access_token: str | None = None

    @staticmethod
    def _data(payload: Any) -> Any:
        if isinstance(payload, dict) and "data" in payload:
            return payload["data"]
        return payload

    def authenticate(self) -> None:
        hotkey = self.wallet.hotkey.ss58_address
        challenge_response = self.session.post(
            f"{self.base_url}/auth/wallet/challenge",
            json={"ss58_address": hotkey},
            timeout=self.timeout,
        )
        challenge_response.raise_for_status()
        challenge = self._data(challenge_response.json())
        nonce = challenge.get("nonce") if isinstance(challenge, dict) else None
        if not isinstance(nonce, str):
            raise ValueError("Core API wallet challenge did not contain a nonce")

        signature = self.wallet.hotkey.sign(nonce.encode()).hex()
        verify_response = self.session.post(
            f"{self.base_url}/auth/wallet/verify",
            json={
                "nonce": nonce,
                "signature": signature,
                "ss58_address": hotkey,
            },
            timeout=self.timeout,
        )
        verify_response.raise_for_status()
        tokens = self._data(verify_response.json())
        if not isinstance(tokens, dict) or not isinstance(
            tokens.get("access_token"), str
        ):
            raise ValueError("Core API wallet verification returned no access token")
        self._access_token = tokens["access_token"]

    def _request(
        self, method: str, path: str, *, retry_auth: bool = True, **kwargs: Any
    ) -> dict[str, Any]:
        if self._access_token is None:
            self.authenticate()
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {self._access_token}"
        response = self.session.request(
            method,
            f"{self.base_url}{path}",
            headers=headers,
            timeout=self.timeout,
            **kwargs,
        )
        if response.status_code == 401 and retry_auth:
            self._access_token = None
            self.authenticate()
            return self._request(method, path, retry_auth=False, **kwargs)
        response.raise_for_status()
        result = self._data(response.json())
        if not isinstance(result, dict):
            raise ValueError(f"Core API returned invalid data for {path}")
        return result

    def upsert_registry(self, username: str, pat: str) -> dict[str, Any]:
        response = self.session.get(
            f"{self.base_url}/miner-docker-registries/encryption-public-key",
            timeout=self.timeout,
        )
        response.raise_for_status()
        try:
            public_key = serialization.load_pem_public_key(response.content)
        except ValueError as err:
            raise ValueError(
                "Core API returned an invalid registry public key"
            ) from err
        if not isinstance(public_key, rsa.RSAPublicKey):
            raise ValueError("Core API registry public key is not RSA")
        ciphertext = public_key.encrypt(
            pat.encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            ),
        )
        return self._request(
            "PUT",
            "/miner-docker-registries/me",
            json={
                "registry_url": "https://registry-1.docker.io",
                "username": username,
                "encrypted_pat": base64.b64encode(ciphertext).decode(),
            },
        )

    def submit_commit(
        self, challenge_name: str, cipher_commit: str, plain_commit: str
    ) -> dict[str, Any]:
        return self._request(
            "POST",
            "/commits/submit",
            json={
                "challenge_name": challenge_name,
                "cipher_commit": cipher_commit,
                "plain_commit": plain_commit,
            },
        )


class SubmissionStore:
    def __init__(self, path: str):
        self.path = Path(path)
        self.submission_path = self.path.with_suffix(
            self.path.suffix + ".submissions.json"
        )
        self.entries: dict[str, dict[str, Any]] = {}
        self.load()

    def load(self) -> None:
        if not self.submission_path.exists():
            return
        payload = json.loads(self.submission_path.read_text(encoding="utf-8"))
        if not isinstance(payload.get("submissions"), dict):
            raise ValueError(f"Invalid submission state file: {self.submission_path}")
        self.entries = payload["submissions"]

    def save(self) -> None:
        self.submission_path.parent.mkdir(parents=True, exist_ok=True)

        with self.submission_path.open("w", encoding="utf-8") as f:
            json.dump(
                {"submissions": self.entries},
                f,
                sort_keys=True,
            )


class BaseMiner:
    def __init__(self):
        self.config = MainConfig()
        self.miner_config = MinerMainConfig()
        self._stop_event = threading.Event()
        self.setup_logging()
        self.setup_bittensor_objects()
        self.core_api = CoreApiClient(
            self.miner_config.CORE_API_URL,
            self.wallet,
            timeout=self.miner_config.CORE_API_TIMEOUT,
        )

    def setup_logging(self) -> None:
        bt.logging.enable_default()
        bt.logging.enable_info()
        if self.config.BITTENSOR.LOGGING_LEVEL == "DEBUG":
            bt.logging.enable_debug()
        elif self.config.BITTENSOR.LOGGING_LEVEL == "TRACE":
            bt.logging.enable_trace()

    def _create_bittensor_config(self) -> bt.Config:
        bt_config = bt.Config()
        if bt_config.wallet is None:
            bt_config.wallet = bt.Config()
        bt_config.wallet.path = self.miner_config.WALLET_DIR
        bt_config.wallet.name = self.miner_config.WALLET_NAME
        bt_config.wallet.hotkey = self.miner_config.HOTKEY_NAME
        if bt_config.subtensor is None:
            bt_config.subtensor = bt.Config()
        bt_config.subtensor.network = self.config.BITTENSOR.SUBTENSOR_NETWORK
        bt_config.netuid = self.config.BITTENSOR.SUBNET_NETUID
        logger.info(
            f"Using Bittensor config: wallet={bt_config.wallet.path}/{bt_config.wallet.name}/{bt_config.wallet.hotkey}, "
            f"subtensor.network={bt_config.subtensor.network}, netuid={bt_config.netuid}"
        )
        return bt_config

    def setup_bittensor_objects(self) -> None:
        bt_config = self._create_bittensor_config()
        self.wallet = bt.Wallet(config=bt_config)
        self.subtensor = bt.Subtensor(config=bt_config)
        self.metagraph = self.subtensor.metagraph(self.config.BITTENSOR.SUBNET_NETUID)
        self._check_registration()

    def _check_registration(self) -> None:
        hotkey = self.wallet.hotkey.ss58_address
        if hotkey not in self.metagraph.hotkeys:
            raise RuntimeError(
                f"Miner hotkey {hotkey} is not registered on subnet "
                f"{self.config.BITTENSOR.SUBNET_NETUID}"
            )
        self.my_subnet_uid = self.metagraph.hotkeys.index(hotkey)

    def stop(self) -> None:
        self._stop_event.set()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()


__all__ = ["BaseMiner", "CoreApiClient", "SubmissionStore"]
