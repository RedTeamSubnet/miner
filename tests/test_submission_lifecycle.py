from miner._base import SubmissionStore
from miner._core import Miner


class _CoreApi:
    def __init__(self, submit_state: str = "COMMITTED"):
        self.submit_state = submit_state
        self.submissions: list[tuple[str, str, str]] = []

    def submit_commit(self, challenge: str, cipher_commit: str, plain_commit: str):
        self.submissions.append((challenge, cipher_commit, plain_commit))
        return {
            "id": f"commit-{len(self.submissions)}",
            "state": self.submit_state,
            "committed_at": "2026-01-01T00:00:00+00:00",
        }


def _miner(store: SubmissionStore, core_api: _CoreApi) -> Miner:
    miner = Miner.__new__(Miner)
    miner.submissions = store
    miner.core_api = core_api
    return miner


def test_submitted_commit_survives_sync_and_restart(tmp_path):
    store_path = tmp_path / "commits"
    core_api = _CoreApi()
    miner = _miner(SubmissionStore(str(store_path)), core_api)
    first_commit = "challenge---alice/repo@sha256:" + "a" * 64

    miner._submit_current({"challenge": first_commit})
    first_entry = dict(miner.submissions.entries["challenge"])
    miner._submit_current({"challenge": first_commit})
    assert len(core_api.submissions) == 1
    assert miner.submissions.entries["challenge"]["state"] == "COMMITTED"

    restarted = _miner(SubmissionStore(str(store_path)), core_api)
    restarted._submit_current({"challenge": first_commit})
    assert len(core_api.submissions) == 1
    assert restarted.submissions.entries["challenge"]["state"] == "COMMITTED"

    second_commit = "challenge---alice/repo@sha256:" + "b" * 64
    restarted._submit_current({"challenge": second_commit})
    second_entry = restarted.submissions.entries["challenge"]
    assert len(core_api.submissions) == 2
    assert second_entry["plain_commit"] != first_entry["plain_commit"]
    assert second_entry["cipher_commit"] != first_entry["cipher_commit"]


def test_non_committed_submit_response_is_retained(tmp_path):
    core_api = _CoreApi(submit_state="QUEUED")
    miner = _miner(SubmissionStore(str(tmp_path / "commits")), core_api)
    commit = "challenge---alice/repo@sha256:" + "a" * 64

    miner._submit_current({"challenge": commit})
    miner._submit_current({"challenge": commit})

    assert len(core_api.submissions) == 1
    assert miner.submissions.entries["challenge"]["state"] == "QUEUED"
