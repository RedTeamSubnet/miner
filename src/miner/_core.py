from __future__ import annotations

import hashlib
import os
import re
import time

import bittensor as bt
from cryptography.fernet import Fernet
import requests
import yaml

from ._base import BaseMiner, SubmissionStore

_COMMIT_RE = re.compile(
    r"^(?P<challenge>.{2,64})---(?P<username>[A-Za-z0-9][A-Za-z0-9_.-]{0,127})/"
    r"(?P<repository>[A-Za-z0-9][A-Za-z0-9_./-]{0,191})@sha256:"
    r"(?P<digest>[0-9a-fA-F]{64})$"
)


class Miner(BaseMiner):
    def __init__(self):
        super().__init__()
        self.submissions = SubmissionStore(self.miner_config.COMMIT_STORAGE_DIR)
        self._registry_fingerprint: str | None = None
        self._last_metagraph_sync = time.monotonic()

    def _load_active_commits(self) -> dict[str, str]:
        path = self.miner_config.COMMIT_FILE_PATH
        if not os.path.isfile(path):
            raise ValueError(f"Active commit file not found: {path}")
        with open(path, encoding="utf-8") as stream:
            raw = yaml.safe_load(stream)
        if raw is None:
            return {}
        if not isinstance(raw, list):
            raise ValueError("active_commit.yaml must contain a list of commit strings")

        commits: dict[str, str] = {}
        for value in raw:
            if not isinstance(value, str):
                raise ValueError("Every active commit must be a string")
            match = _COMMIT_RE.fullmatch(value.strip())
            if match is None:
                raise ValueError(f"Invalid commit format: {value}")
            challenge = match.group("challenge")
            if challenge in commits:
                raise ValueError(f"Duplicate challenge in active commits: {challenge}")
            commits[challenge] = value.strip()
        return commits

    def _load_pat(self) -> str:
        path = self.miner_config.PAT_FILE_PATH
        if not os.path.isfile(path):
            raise ValueError(f"PAT file not found: {path}")
        with open(path, encoding="utf-8") as stream:
            pat = stream.read().strip()
        if not pat:
            raise ValueError("Docker Hub PAT is empty")
        return pat

    @staticmethod
    def _docker_username(commits: dict[str, str]) -> str:
        usernames = {
            _COMMIT_RE.fullmatch(commit).group("username")  # type: ignore[union-attr]
            for commit in commits.values()
        }
        if not usernames:
            raise ValueError("At least one active commit is required")
        if len(usernames) != 1:
            raise ValueError("All active commits must use one Docker Hub username")
        return next(iter(usernames))

    def _verify_docker_access(
        self, username: str, pat: str, commits: dict[str, str]
    ) -> None:
        response = requests.post(
            "https://hub.docker.com/v2/users/login/",
            json={"username": username, "password": pat},
            timeout=self.miner_config.CORE_API_TIMEOUT,
        )
        if response.status_code != 200:
            raise ValueError(
                f"Docker Hub PAT verification failed with status {response.status_code}"
            )
        for commit in commits.values():
            match = _COMMIT_RE.fullmatch(commit)
            assert match is not None
            repository = match.group("repository")
            visibility = requests.get(
                f"https://registry-1.docker.io/v2/{username}/{repository}/tags/list",
                timeout=self.miner_config.CORE_API_TIMEOUT,
            )
            if visibility.status_code == 200:
                raise ValueError(f"Docker repository must be private: {repository}")
            if visibility.status_code != 401:
                raise ValueError(
                    f"Could not verify Docker repository {repository}: "
                    f"status {visibility.status_code}"
                )

    def _sync_registry(self, username: str, pat: str, commits: dict[str, str]) -> None:
        fingerprint = hashlib.sha256(
            (f"{username}\0{pat}\0" + "\0".join(sorted(commits.values()))).encode()
        ).hexdigest()
        if fingerprint == self._registry_fingerprint:
            return
        self._verify_docker_access(username, pat, commits)
        self.core_api.upsert_registry(username, pat)
        self._registry_fingerprint = fingerprint
        bt.logging.success("Docker registry credentials synced to Core API.")

    def _new_pending(self, challenge: str, plain_commit: str) -> dict[str, str]:
        key = Fernet.generate_key()
        return {
            "challenge_name": challenge,
            "cipher_commit": Fernet(key).encrypt(plain_commit.encode()).decode(),
            "plain_commit": plain_commit,
        }

    def _submit_current(self, commits: dict[str, str]) -> None:
        for challenge, plain_commit in commits.items():
            pending = self.submissions.entries.get(challenge)
            pending_commit = pending.get("plain_commit") if pending else None
            if pending_commit != plain_commit:
                pending = self._new_pending(challenge, plain_commit)
                self.submissions.entries[challenge] = pending
                self.submissions.save()

            if pending.get("commit_id"):
                continue
            result = self.core_api.submit_commit(
                challenge,
                pending["cipher_commit"],
                pending["plain_commit"],
            )
            state = result["state"]
            pending["commit_id"] = result["id"]
            pending["state"] = state
            pending["committed_at"] = result["committed_at"]
            self.submissions.save()
            bt.logging.success(f"Submitted commit for challenge {challenge}.")

    def sync_once(self) -> None:
        commits = self._load_active_commits()
        username = self._docker_username(commits)
        pat = self._load_pat()
        self._sync_registry(username, pat, commits)
        self._submit_current(commits)

    def _sync_metagraph_if_due(self) -> None:
        if (
            time.monotonic() - self._last_metagraph_sync
            < self.miner_config.METAGRAPH_SYNC_INTERVAL
        ):
            return
        self.metagraph.sync(subtensor=self.subtensor)
        self._check_registration()
        self._last_metagraph_sync = time.monotonic()

    def run(self) -> None:
        # Fail fast on invalid local configuration before entering retry mode.
        self._docker_username(self._load_active_commits())
        self._load_pat()
        retry_delay = self.miner_config.SYNC_INTERVAL
        while not self._stop_event.is_set():
            try:
                self._sync_metagraph_if_due()
                self.sync_once()
                bt.logging.success("All commits submitted; shutting down.")
                self._stop_event.set()
            except requests.HTTPError as err:
                status = err.response.status_code if err.response is not None else None
                detail = err.response.text if err.response is not None else str(err)
                if status is not None and status < 500 and status not in {409, 429}:
                    raise RuntimeError(
                        f"Core API rejected request ({status}): {detail}"
                    ) from err
                bt.logging.error(f"Core API sync failed; retrying: {detail}")
                retry_delay = min(
                    max(self.miner_config.SYNC_INTERVAL, retry_delay * 2),
                    self.miner_config.MAX_RETRY_DELAY,
                )
            except requests.RequestException as err:
                bt.logging.error(f"Network sync failed; retrying: {err}")
                retry_delay = min(
                    max(self.miner_config.SYNC_INTERVAL, retry_delay * 2),
                    self.miner_config.MAX_RETRY_DELAY,
                )
            self._stop_event.wait(retry_delay)


__all__ = ["Miner"]
