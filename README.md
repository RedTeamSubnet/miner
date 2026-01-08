# RedTeam subnet - Miner (Agent)

This repository is for miner of RedTeam subnet.

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
        - <https://docs.learnbittensor.org/getting-started/install-btcli>
        - <https://docs.learnbittensor.org/btcli>
    - Create miner wallet:
        - <https://docs.learnbittensor.org/keys/working-with-keys>
        - <https://docs.learnbittensor.org/btcli/btcli-permissions>
    - Register miner wallet to RedTeam subnet:
        - <https://docs.learnbittensor.org/miners>
        - <https://docs.learnbittensor.org/miners/miners-btcli-guide>
- Install [**docker** and **docker compose**](https://docs.docker.com/engine/install)
    - Docker [intstallation script](https://github.com/docker/docker-install)
    - Docker [post-installation steps](https://docs.docker.com/engine/install/linux-postinstall)
- Prepare your own challenge commit as solution for RedTeam subnet challenges:
    - Choose challenges to solve from [RedTeam subnet - Docs](https://docs.theredteam.io).
    - Implement your own solution for the challenges.
    - Build and push docker image to Docker Hub.
    - Get the commit hash of your pushed docker image.

[OPTIONAL] For **DEVELOPMENT** environment:

- Install [**git**](https://git-scm.com/downloads)
- Setup an [**SSH key**](https://docs.github.com/en/github/authenticating-to-github/connecting-to-github-with-ssh)

---

### 2. 📥 Download or clone the repository

**2.1.** Prepare projects directory (if not exists):

```sh
# Create projects directory:
mkdir -pv ~/workspaces/projects

# Enter into projects directory:
cd ~/workspaces/projects
```

**2.2.** Follow one of the below options **[A]**, **[B]** or **[C]**:

**OPTION A.** Clone the repository:

```sh
git clone https://github.com/RedTeamSubnet/miner.git && \
    cd miner
```

**OPTION B.** Clone the repository (for **DEVELOPMENT**: git + ssh key):

```sh
git clone git@github.com:RedTeamSubnet/miner.git && \
    cd miner
```

**OPTION C.** Download source code:

1. Download archived **zip** or **tar.gz** file from [**releases**](https://github.com/RedTeamSubnet/miner/releases).
2. Extract it into the projects directory.
3. Enter into the extracted project directory.

### 3. 🔧 Configure active commit file

**[IMPORTANT]** Make sure to change the **commit hash** to your own value in the **`active_commit.yaml`** file:

```sh
# Copy template active commit file:
cp -v ./templates/configs/active_commit.yaml ./volumes/configs/agent-miner/active_commit.yaml

# Update active commit file with your own commit hash:
nano ./volumes/configs/agent-miner/active_commit.yaml
```

### 4. 🌎 Configure environment variables

[NOTE] Please, check **[environment variables](#-environment-variables)** section for more details.

**[IMPORTANT]** Make sure to change the **wallet directory and wallet name variables** to your own values in the **`.env`** file:

```sh
# Copy '.env.example' file to '.env' file:
cp -v ./.env.example ./.env

# Edit environment variables to fit in your environment:
nano ./.env
```

### 5. ✅ Check configuration

```sh
## Check docker compose configuration is valid:
./compose.sh validate
# Or:
docker compose config
```

### 6. 🏁 Run miner node

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
RT_MINER_COMMIT_FILE_PATH="./volumes/configs/agent-miner/active_commit.yaml" # !!! CHANGE THIS TO REAL COMMIT FILE PATH !!!
RT_MINER_WALLET_NAME="miner" # !!! CHANGE THIS TO REAL MINER WALLET NAME !!!
RT_MINER_HOTKEY_NAME="default" # !!! CHANGE THIS TO REAL MINER HOTKEY NAME !!!
RT_MINER_AXON_PORT=8091
# RT_MINER_LOGS_DIR="/var/log/agent-miner"
# RT_MINER_DATA_DIR="/var/lib/agent-miner"
```

### 🔧 Active commit file

[**`active_commit.yaml`**](./volumes/configs/agent-miner/active_commit.yaml):

```yaml
# - text_detection---vietbeu/text-detection-miner@sha256:7be64b1a0b938951c6361195c58299540a21ff4ac8c34e5cc18bcae634e254b0
# - webui_auto---asadbekk/rest.rt-wu-miner@sha256:b8cd274c0fbb4b30b98274465424025a8b0d070c9cca4e80e0d79f69f49a5c17
- response_quality_adversarial_v2---bangbang123/response_quality_adversarial@sha256:a5fff733d574ae0c9c93d9029a7fc2aaaeeac07793fb6ef4683236579f1bf857
- ada_detection_v1---vietbeu/response_quality_ranker@sha256:5b468ec48eae57907f1ba91de12bfe78f709351b0421e14a3b105dcb00844103
- ab_sniffer_v5---asadbey/rest.rt-hb-v1-miner@sha256:f84f4d5a179908214121e071906357ddbfaee30fb6da2e896d404fc00acd20e3
```

## 🏗️ Build Docker Image

Before building the docker image, make sure you have installed **docker** and **docker compose**.

To build the docker image, run the following command:

```sh
# Build docker image:
./scripts/build.sh
# Or:
docker compose build
```

## 📚 Documentation

- <https://docs.theredteam.io>

---

## 📑 References

- Bittensor docs: <https://docs.learnbittensor.org>
- Bittensor CLI: <https://docs.learnbittensor.org/btcli>
- Bittensor CLI GitHub: <https://github.com/opentensor/btcli>
- Bittensor CLI PyPI: <https://pypi.org/project/bittensor-cli>
- The RedTeam subnet: <https://www.theredteam.io>
