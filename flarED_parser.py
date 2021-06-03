#!/usr/bin/env python3

import sys
import argparse
from flarED import flarED

""" Class for checking the parameter range constraint """
class Range(object):
    def __init__(self, start, end):
        self.start = start
        self.end = end
    def __str__(self):
        """ for help representation """
        return 'in range {0}, {1}'.format(self.start, self.end)
    def __repr__(self):
        """ for error representation """
        return '[{0}, {1}]'.format(self.start, self.end)
    def __eq__(self, other):
        return self.start <= other <= self.end
    def __contains__(self, item):
        return self.__eq__(item)
    def __iter__(self):
        return self

PARSER = argparse.ArgumentParser(description="",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)

PARSER.add_argument("-ix", "--ix", type=float, default=None, required=True,
        choices=[Range(8.0e-07, 0.0001)], help="Solar X-Ray Flux")
ARGS = PARSER.parse_args()

if __name__ == "__main__":
    f = flarED(ARGS.ix)
    f.calculate_and_plot()

