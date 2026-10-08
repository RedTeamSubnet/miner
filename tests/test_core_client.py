import base64
import json

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from miner._base import CoreApiClient, SubmissionStore


class _Response:
    def __init__(self, payload=None, *, content=b"", status_code=200):
        self._payload = payload
        self.content = content
        self.status_code = status_code
        self.text = json.dumps(payload or {})

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(response=self)


class _Hotkey:
    ss58_address = "5" * 48

    @staticmethod
    def sign(data):
        return b"signature:" + data


class _Wallet:
    hotkey = _Hotkey()


class _Session:
    def __init__(self, public_key):
        self.public_key = public_key
        self.requests = []

    def post(self, url, **kwargs):
        self.requests.append(("POST", url, kwargs))
        if url.endswith("/challenge"):
            return _Response({"nonce": "nonce-value"})
        return _Response(
            {
                "access_token": "jwt",
                "expires_in": 900,
                "scopes": [
                    "commits:submit",
                    "miner-docker-registries:upsert-own",
                ],
            }
        )

    def get(self, url, **kwargs):
        self.requests.append(("GET", url, kwargs))
        return _Response(content=self.public_key)

    def request(self, method, url, **kwargs):
        self.requests.append((method, url, kwargs))
        return _Response({"id": "reg-1", "state": "COMMITTED"})


def test_wallet_auth_and_rsa_pat_encryption():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    session = _Session(public_pem)
    client = CoreApiClient(
        "https://core.example/api/v1", _Wallet(), session=session, timeout=3
    )

    client.authenticate()
    result = client.upsert_registry("alice", "pat-secret")

    assert result["id"] == "reg-1"
    verify_call = session.requests[1]
    assert verify_call[2]["json"]["signature"] == (
        b"signature:nonce-value".hex()
    )
    encrypted = session.requests[-1][2]["json"]["encrypted_pat"]
    plaintext = private_key.decrypt(
        base64.b64decode(encrypted),
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    assert plaintext == b"pat-secret"


def test_submission_store_is_private_and_round_trips(tmp_path):
    path = tmp_path / "submissions.json"
    store = SubmissionStore(str(path))
    store.entries["challenge"] = {"plain_commit": "secret"}
    store.save()

    assert path.stat().st_mode & 0o777 == 0o600
    loaded = SubmissionStore(str(path))
    assert loaded.entries["challenge"]["plain_commit"] == "secret"
