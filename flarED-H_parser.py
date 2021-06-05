#!/usr/bin/env python3

import sys
import argparse
from flarED import flarED
from Range import Range

PARSER = argparse.ArgumentParser(description="",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

PARSER.add_argument("-he", "--height", type=float, default=None, required=True,
        choices=[Range(50, 90)], help="Altitudes [km]")
ARGS = PARSER.parse_args()

if __name__ == "__main__":
    f = flarED()
    f.flared_h(ARGS.height)

