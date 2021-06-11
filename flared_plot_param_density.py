#!/usr/bin/env python3
from Flared import *

""" Plot density of experimental parameters (from the database) """

if __name__ == "__main__":
    f = Flared()
    f.plot_param_density(f.hprim_vlf, r"H' $[\mathrm{km}]$")
    f.plot_param_density(f.beta_vlf, r"Beta $[\mathrm{km^{-1}}]$")
