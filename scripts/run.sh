#!/usr/bin/env bash
set -euo pipefail


## --- Base --- ##
_SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-"$0"}")" >/dev/null 2>&1 && pwd -P)"
_PROJECT_DIR="$(cd "${_SCRIPT_DIR}/.." >/dev/null 2>&1 && pwd)"
cd "${_PROJECT_DIR}" || exit 2


# shellcheck disable=SC1091
[ -f .env ] && . .env


if ! command -v python >/dev/null 2>&1; then
	echo "[ERROR]: Not found 'python' command, please install it first!" >&2
	exit 1
fi
## --- Base --- ##


## --- Main --- ##
main()
{
	echo "[INFO]: Starting agent miner..."
	python -u -m src.miner \
		--wallet.name "${RT_MINER_WALLET_NAME:-miner}" \
		--wallet.path "${RT_BTCLI_WALLET_DIR:-${RT_BTCLI_DATA_DIR:-/var/lib/sidecar-btcli}/wallets}" \
		--wallet.hotkey "default" \
		--subtensor.network "${RT_BT_SUBTENSOR_NETWORK:-${RT_BT_SUBTENSOR_WS_SCHEME:-ws}://${RT_BT_SUBTENSOR_HOST:-subtensor}:${RT_BT_SUBTENSOR_WS_PORT:-9944}}" \
		--netuid "${RT_BT_SUBNET_NETUID:-2}" \
		--axon.port "${RT_MINER_PORT:-8088}" || exit 2

	echo "[OK]: Done."
	exit 0
}

main
## --- Main --- ##
