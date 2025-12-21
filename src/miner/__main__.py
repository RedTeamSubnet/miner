#!/usr/bin/env python

import time

import bittensor as bt

from ._core import Miner


if __name__ == "__main__":
    with Miner() as miner:
        while True:
            bt.logging.info("Miner is running.")
            time.sleep(10)
