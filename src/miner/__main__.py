#!/usr/bin/env python

from ._core import Miner


if __name__ == "__main__":
    with Miner() as miner:
        try:
            miner.run()
        except KeyboardInterrupt:
            miner.stop()
