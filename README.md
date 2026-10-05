# RedTeam subnet - Miner (Agent)

This repository runs a RedTeam miner that authenticates its Bittensor wallet with Core API and submits encrypted challenge commits. For developing challenges please use dedicated repositories and separate machine to protect submissions.

## ✨ Features

- Miner node
- Independent
- Easy configuration
- Dockerized setup
- Docker Compose support

---

## Getting Started

### 1. 🚧 Prerequisites

- Prepare miner wallet (skip if you already have one):
    - Install **Bittensor CLI**:
        - [Installing Bittensor CLI](https://docs.learnbittensor.org/getting-started/install-btcli)
        - [Bittensor CLI: `btcli` Reference Document](https://docs.learnbittensor.org/btcli)
    - Create miner wallet:
        - [Working with Keys](https://docs.learnbittensor.org/keys/working-with-keys)
        - [Bittensor CLI Permissions](https://docs.learnbittensor.org/btcli/btcli-permissions)
    - Register miner wallet to RedTeam subnet:
        - [Mining in Bittensor](https://docs.learnbittensor.org/miners)
        - [Miner's Guide to `BTCLI`](https://docs.learnbittensor.org/miners/miners-btcli-guide)
- Install [**docker** and **docker compose**](https://docs.docker.com/engine/install)
    - Docker [installation script](https://github.com/docker/docker-install)
    - Docker [post-installation steps](https://docs.docker.com/engine/install/linux-postinstall)
- Prepare your own challenge commit as solution for RedTeam subnet challenges:
    - Choose challenges to solve from [RedTeam subnet - Docs](https://docs.theredteam.io).
    - Implement your own solution for the challenges.
    - Build and push docker image to Docker Hub.
    - Get the commit hash of your pushed docker image.

---

### 2. 📥 Download or clone the repository

**2.1.** Prepare projects directory (if not exists):

```sh
# Create projects directory:
mkdir -pv ~/workspaces/projects

# Enter into projects directory:
cd ~/workspaces/projects
```

**2.2.** Follow one of the below options **[A]** or **[B]**:

**OPTION A.** Clone the repository:

```sh
git clone https://github.com/RedTeamSubnet/miner.git && \
    cd miner
```

**OPTION B.** Download source code:

1. Download archived **zip** or **tar.gz** file from [**releases**](https://github.com/RedTeamSubnet/miner/releases).
2. Extract it into the projects directory.
3. Enter into the extracted project directory.

### 3. 🔧 Configure active commit file

**[IMPORTANT]** Make sure to change the **commit hash** to your own value in the **`active_commit.yaml`** file:

```sh
# Copy template active commit file:
cp -v ./templates/configs/active_commit.yaml ./volumes/configs/agent-miner/active_commit.yaml
cp -v ./templates/configs/personal_access_token.txt ./volumes/configs/agent-miner/personal_access_token.txt
```

### 4. Update commit file and personal access token file

1. Update the **commit hash** in the **`active_commit.yaml`** file to your own value.

    ```sh
        # Edit active commit file to fit in your environment
        nano ./volumes/configs/agent-miner/active_commit.yaml
    ```

2. Update the **personal access token** in the **`personal_access_token.txt`** file to your own value.

    ```sh
        # Edit personal access token file to fit in your environment
        nano ./volumes/configs/agent-miner/personal_access_token.txt
    ```

### 5. 🌎 Configure environment variables

[NOTE] Please, check **[environment variables](#-environment-variables)** section for more details.

**[IMPORTANT]** Make sure to change the **wallet directory and wallet name variables** to your own values in the **`.env`** file:

```sh
# Copy '.env.example' file to '.env' file:
cp -v ./.env.example ./.env

# Edit environment variables to fit in your environment
nano ./.env
```

### 6. ✅ Check configuration

```sh
## Check docker compose configuration is valid:
./compose.sh validate
# Or:
docker compose config
```

### 7. 🏁 Run miner node

```sh
## Start docker compose:
./compose.sh start -l
# Or:
docker compose up -d --remove-orphans --force-recreate && \
    docker compose logs -f --tail 100
```

### (OPTIONAL) 🛑 Stop miner node

```sh
# Stop docker compose:
./compose.sh stop
# Or:
docker compose down --remove-orphans
```

👍

---

## ⚙️ Configuration

### 🌎 Environment Variables

[**`.env.example`**](./.env.example):

```sh
## --- Environment variable --- ##
ENV=PRODUCTION
DEBUG=false
# TZ=UTC
# PYTHONDONTWRITEBYTECODE=1


## -- Bittensor configs -- ##
# RT_BT_SUBTENSOR_NETWORK="wss://entrypoint-finney.opentensor.ai:443"


## -- Subnet configs -- ##
# ! WARNING: Do not use `~` character, it will not be expand properly! Use absolute path or ${HOME} instead:
RT_BTCLI_WALLET_DIR="${HOME}/.bittensor/wallets" # !!! CHANGE THIS TO REAL WALLET DIRECTORY !!!
# RT_BT_SUBNET_NETUID=61


## - Miner configs -- ##
RT_MINER_WALLET_NAME="miner" # !!! CHANGE THIS TO REAL MINER WALLET NAME !!!
RT_MINER_HOTKEY_NAME="default" # !!! CHANGE THIS TO REAL MINER HOTKEY NAME !!!
# RT_MINER_CORE_API_URL="https://storage-api.theredteam.io/api/v1"
# RT_MINER_SYNC_INTERVAL=86400
# RT_MINER_DATA_DIR="/var/lib/agent-miner"
# RT_MINER_CONFIG_DIR="/etc/agent-miner"
```

### 🔧 Template active commit file

[**`active_commit.yaml`**](./templates/configs/active_commit.yaml):

```yaml
- ab_sniffer_v4---redteamsubnet61/template-ab_sniffer_v4@sha256:a5fff733d574ae0c9c93d9029a7fc2aaaeeac07793fb6ef4683236579f1bf857
- ada_detection_v1---redteamsubnet61/template-ada_detection_v1@sha256:5b468ec48eae57907f1ba91de12bfe78f709351b0421e14a3b105dcb00844103
- humanize_behaviou_v4---redteamsubnet61/template-humanize_behaviou_v4@sha256:f84f4d5a179908214121e071906357ddbfaee30fb6da2e896d404fc00acd20e3
```

Each entry follows the format:

```text
<challenge_name>---<docker_username>/<repository>@sha256:<digest>
```

- **`challenge_name`**: RedTeam challenge identifier (2-64 chars)
- **`docker_username`**: Docker Hub username (must be the same for all entries)
- **`repository`**: Docker Hub repository name (must be **private**)
- **`digest`**: SHA256 digest of the pushed Docker image

### 🔧 Personal access token file

[**`personal_access_token.txt`**](./templates/configs/personal_access_token.txt):

Store your Docker Hub personal access token (PAT) in this file. The miner uses it to:

1. Verify all referenced repositories are private.
2. Encrypt and upload the PAT to the Core API so validators can pull your challenge images.

### 📋 Configuration reference

All configuration is loaded via environment variables with the `RT_MINER_` prefix (see [`src/miner/config/miner.py`](./src/miner/config/miner.py)).

| Variable | Default | Description |
| --- | --- | --- |
| `RT_BTCLI_WALLET_DIR` | `~/.bittensor/wallets` | Bittensor wallet directory |
| `RT_MINER_WALLET_NAME` | `miner` | Wallet name |
| `RT_MINER_HOTKEY_NAME` | `default` | Hotkey name |
| `RT_MINER_DATA_DIR` | `/var/lib/agent-miner` | Data directory for submission state |
| `RT_MINER_CONFIG_DIR` | `/etc/agent-miner` | Config directory (commit file, PAT file) |
| `RT_MINER_COMMIT_FILE_PATH` | `{config_dir}/active_commit.yaml` | Path to active commit file |
| `RT_MINER_PAT_FILE_PATH` | `{config_dir}/personal_access_token.txt` | Path to Docker Hub PAT file |
| `RT_MINER_CORE_API_URL` | `https://storage-api.theredteam.io/api/v1` | RedTeam Core API base URL |
| `RT_MINER_CORE_API_TIMEOUT` | `10.0` | Core API request timeout in seconds (max 120) |
| `RT_MINER_SYNC_INTERVAL` | `86400` | Sync loop interval in seconds (max 86400) |
| `RT_MINER_METAGRAPH_SYNC_INTERVAL` | `600` | Metagraph refresh interval in seconds |
| `RT_MINER_MAX_RETRY_DELAY` | `300` | Max retry backoff delay in seconds |

---

## 🏗️ Project structure

```text
agent-miner/
├── src/miner/               # Miner package
│   ├── __main__.py          # Entrypoint: Miner().run()
│   ├── __version__.py       # Version string
│   ├── _base.py             # BaseMiner, CoreApiClient, SubmissionStore
│   ├── _core.py             # Miner implementation (sync, submit, reveal)
│   └── config/
│       └── miner.py         # MinerMainConfig (pydantic settings)
├── tests/                   # pytest test suite
├── scripts/                 # Build, test, release, version scripts
│   └── docker/
│       └── docker-entrypoint.sh
├── templates/               # Config & compose templates
│   ├── configs/             # active_commit.yaml, personal_access_token.txt
│   └── compose/             # Dev & prod compose override templates
├── volumes/                 # Runtime data (configs, storage, logs)
├── compose.yml              # Docker Compose service definition
├── compose.sh               # Docker Compose wrapper script
├── Dockerfile               # Multi-stage build (builder → base → app)
├── Makefile                 # Common commands (make help)
└── requirements.txt         # Python dependencies
```

---

## 💻 Development

### Prerequisites

- Python 3.10+
- [pre-commit](https://pre-commit.com)

### Setup

```sh
# Install dev dependencies:
python -m pip install -r ./requirements/requirements.dev.txt

# Install pre-commit hooks:
pre-commit install
```

### Running tests

```sh
# Via Makefile:
make test

# Via script (with coverage and verbose output):
./scripts/test.sh -c -v

# Directly:
python -m pytest -v
```

### Running the miner locally (without Docker)

```sh
# Copy and edit environment:
cp -v ./.env.example ./.env
nano ./.env

# Run:
./scripts/run.sh
# Or:
python -u -m src.miner
```

### Docker Compose commands

```sh
./compose.sh start -l    # Start and follow logs
./compose.sh stop         # Stop all services
./compose.sh restart      # Restart all services
./compose.sh logs         # View logs
./compose.sh validate     # Validate compose config
./compose.sh enter         # Enter container shell
./compose.sh update        # Pull latest image
```

---

## 🚀 CI/CD

Releases are automated via four sequential GitHub Actions workflows:

1. **Bump Version** (`1.bump-version.yml`) — manually triggered, bumps semver and pushes a tag.
2. **Build and Publish** (`2.build-publish.yml`) — builds the Docker image and pushes to Docker Hub.
3. **Create Release** (`3.create-release.yml`) — creates a GitHub release with auto-generated notes.
4. **Update Changelog** (`4.update-changelog.yml`) — updates `CHANGELOG.md` and `docs/release-notes.md`.

### Manual release

```sh
# Bump version (patch/minor/major), commit, tag, and push:
./scripts/bump-version.sh -b=patch -c -t -p

# Build and push Docker image:
./scripts/build.sh -p amd64 -u

# Create GitHub release:
./scripts/release.sh

# Update changelog:
./scripts/changelog.sh -c -p
```

---

## 📚 Documentation

- RedTeam subnet docs: <https://docs.theredteam.io>
- Architecture: [ARCHITECTURE.md](./ARCHITECTURE.md)
- Contributing: [CONTRIBUTING.md](./CONTRIBUTING.md)
- Changelog: [CHANGELOG.md](./CHANGELOG.md)
- Release notes: [docs/release-notes.md](./docs/release-notes.md)

---

## 📑 References

- Bittensor docs: <https://docs.learnbittensor.org>
- Bittensor CLI: <https://docs.learnbittensor.org/btcli>
- Bittensor CLI GitHub: <https://github.com/opentensor/btcli>
- Bittensor CLI PyPI: <https://pypi.org/project/bittensor-cli>
- The RedTeam subnet: <https://www.theredteam.io>
- RedTeam Core API: <https://storage-api.theredteam.io/api/v1>
