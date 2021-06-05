#!/usr/bin/env python3

import sys
import argparse
from flarED import flarED
from Range import Range

PARSER = argparse.ArgumentParser(description="",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

PARSER.add_argument("-ix", "--ix", type=float, default=None, required=True,
        choices=[Range(8.0e-07, 0.0001)], help="Solar X-Ray Flux")
ARGS = PARSER.parse_args()

if __name__ == "__main__":
    f = flarED()
    f.calculate_and_plot(ARGS.ix)

