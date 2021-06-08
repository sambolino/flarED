#!/usr/bin/env python3

import os
from sqlite_utils import *
import math
from collections import defaultdict
import operator
import warnings
from itertools import groupby
from decimal import Decimal
from datetime import datetime
import csv
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.interpolate import interp1d, CubicSpline

class Flared:

    """ parent class for Flare Electron Density calculations """

    def __init__(self):

        """ gets beta and fprim interpolated functions from polyfit,
        sets folder and font """

        self.f_beta, self.f_hprim = self._polyfit()

        self.font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 12,
            }

        self.folder = "%s/%s-%s" % ("results", self.__class__.__name__,
                int(datetime.now().timestamp()))

        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

    def _polyfit(self):

        """ takes experimental values of ix, beta, height from a db,
        make polynomial fit and interpolation of betas and hprim as
        a function of ix """

        database = r"data/flare_vlf.db"
        table_name = 'flares'
        conn = create_connection(database)

        # query for ix,beta,height tuples
        with conn:
            sql = """SELECT ix, beta, reflection_height \
                    FROM %s \
                    ORDER BY ix;""" %(table_name)
            query = custom_query(conn, sql)

        # there might be duplicated values for ix
        # make a new list where all the ix duplicates will condense to a single
        # value while new beta and h get average value from n duplicates
        list_of_averages = []
        for k, g in groupby(query, operator.itemgetter(0)):
            list_of_tuples = list(g)
            listlen = len(list_of_tuples)
            if listlen > 1:
                ix_duplicate = list_of_tuples[0][0]
                beta_sum = 0
                h_sum = 0
                for i in range(listlen):
                    beta_sum += list_of_tuples[i][1]
                    h_sum += list_of_tuples[i][2]
                list_of_averages.append((ix_duplicate, round(beta_sum/listlen, 3),
                    round(h_sum/listlen, 3)))
            elif listlen==1:
                list_of_averages.append(list_of_tuples[0])

        # change the last ix value which was too large and was
        # messing with the interpolation
        list_of_averages[-1] = (0.0001, list_of_averages[-1][1],
                list_of_averages[-1][2])
        ix_values, beta_values, h_values = map(list, zip(*list_of_averages))

        x = ix_values
        y = beta_values
        y2 = h_values

        # we fit first most of the curve as 15th degree polynomial,
        # then skip jumpy parts then fit as 1st (but it looks like it's 2nd??)
        # degree polynomial
        warnings.filterwarnings('ignore')

        xpoly1 = np.linspace(x[0], x[-40], num=100, endpoint=True)
        xpoly2 = np.linspace(x[-10], x[-1], num=100, endpoint=True)

        poly_deg = 15
        ypoly1 = np.polyval(np.polyfit(x, y, poly_deg), xpoly1)
        y2poly1 = np.polyval(np.polyfit(x, y2, poly_deg), xpoly1)

        poly_deg = 1
        ypoly2 = np.polyval(np.polyfit(x, y, poly_deg), xpoly2)
        y2poly2 = np.polyval(np.polyfit(x, y2, poly_deg), xpoly2)

        # glue the dots again
        xpoly = np.concatenate((xpoly1, xpoly2))
        ypoly = np.concatenate((ypoly1, ypoly2))
        y2poly = np.concatenate((y2poly1, y2poly2))

        # interpolate and calculate x and y's for the whole range
        f_beta = interp1d(xpoly, ypoly)
        f_hprim = interp1d(xpoly, y2poly)

        return f_beta, f_hprim

    def _write_to_csv(self, dict_of_lists):

        """writes data from dict to csv"""

        ed_filename = "%s/data_table.csv" % (self.folder)
        with open(ed_filename, mode='w', newline='') as f:

            fieldnames = dict_of_lists.keys()
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            # convert dict with list values to list of dicts
            list_of_dicts = [dict(zip(dict_of_lists, i)) for i in zip(*dict_of_lists.values())]
            for d in list_of_dicts:
                writer.writerow(d)

    @staticmethod
    def _extract_column(rows, column):

        """returns a specific column from a list of rows"""
        return [row[column] for row in rows]

class Flared_t(Flared):

    """ Child class for flarED time series """

    def __init__(self, h):

        """ initializes parent constructor, sets input h parameter,
        calculates ED's with flared and easyfit methods """

        super().__init__()
        self.h = h
        self.ed_list, self.ix_list, self.beta_list, self.hprim_list, \
                self.stamp_list = self._calculate_flared()
        self.ed_easy_list = self._calculate_easyfit(self.ix_list)

    def write_and_plot(self):

        """ method which invokes writing and plotting methods """

        # write data to a csv file
        self._write_to_csv({
                    'Height(km)': [self.h]*len(self.stamp_list),
                    'Time(H:M)': self.stamp_list,
                    'Electron Density(m^-3)': self.ed_list,
                    'Electron Density(m^-3) easyfit': self.ed_easy_list,
                    'Solar Flux(W*m^-2)': self.ix_list,
                    'Beta(km^-1)': self.beta_list,
                    "H'(km)": self.hprim_list})

        # plot data
        self.plot()

    def plot(self):

        """ plots and saves a figure """

        # convert to timestamps then to times suitable for plotting
        timestamp_list = [datetime.strptime(a, '%H:%M') for a in self.stamp_list]
        x = matplotlib.dates.date2num(timestamp_list)


        y = self.ed_list
        y_easy = self.ed_easy_list
        y_ix = self.ix_list

        # plot flared and easyfit ed's as y(log)
        # plot ix's as y2(log)
        # plot times as x
        fig, ax = plt.subplots()
        ax.set_yscale('log')
        lns1 = ax.plot(x, y, '-o', color="thistle", markersize=4,
                mec='blue', mfc='white', label="flarED method")
        lns2 = ax.plot(x, y_easy, '-o', color="thistle", markersize=4,
                mec='red', mfc='white', label="easyFit method")

        plt.title(r"H=%s" %(self.h))
        myFmt = matplotlib.dates.DateFormatter('%H:%M')
        plt.gca().xaxis.set_major_formatter(myFmt)

        ax.set_xlabel(r"time $[\mathrm{h:m}]$", fontdict=self.font)
        ax.set_ylabel(r"Electron Density $[\mathrm{m^{-3}}]$", fontdict=self.font)

        ax2=ax.twinx()
        lns3 = ax2.plot(x, y_ix, '-', color="purple", markersize=4, label="Ix")
        ax2.set_ylabel(r"Flux Intensity $[\mathrm{W*m^{-2}}]$", fontdict=self.font)
        ax2.set_yscale('log')

        lns = lns1+lns2+lns3
        labs = [l.get_label() for l in lns]
        ax.legend(lns, labs, loc=0)

        plt.savefig("%s/figure.png" % (self.folder))
        plt.show()

    def _calculate_flared(self):

        """ calculate ED's with flarED method """

        # open with times, ix's and control ed values
        a_file = open("data/time_series.csv")
        reader = csv.reader(a_file)
        header = next(reader, None)
        rows = list(reader)
        a_file.close()

        stamps = self._extract_column(rows, 0)
        ix_list = self._extract_column(rows, 1)
        ix_list = [float(i) for i in ix_list]

        # control ed values, used for comparison
        #ed_control = self._extract_column(rows, 2)
        #ed_control = [float(i) for i in ed_control]

        ed_list = []
        beta_list = []
        hprim_list = []

        # if ix values are out of range, apply fixed beta and hprim
        # calculate ED's for given parameters
        for ix in ix_list:
            if ix<8e-07:
                beta = 0.3
                hprim = 74
            elif ix>0.0001:
                beta = float(self.f_beta(0.0001))
                hprim = float(self.f_hprim(0.0001))
            else:
                beta = float(self.f_beta(ix))
                hprim = float(self.f_hprim(ix))
            beta_list.append(beta)
            hprim_list.append(hprim)
            ed_list.append(1.43*10**13*math.exp(-0.15*hprim)*\
                    math.exp((beta-0.15)*(self.h-hprim)))

        return ed_list, ix_list, beta_list, hprim_list, stamps

    def _calculate_easyfit(self, ixs):

        """ calculate ED's with easyfit method """

        # find a row with a matching h
        with open("data/easyfit.csv", 'r') as a_file:
            reader = csv.reader(a_file)
            rows = list(reader)
            matched_row = [row for row in rows if row[0] == str(self.h)][0]

        matched_row = [float(i) for i in matched_row]
        ed_list=[]

        # calculate ED's for given parameters
        for ix in ixs:
            ed_list.append(10**(matched_row[1]+matched_row[2]*math.log10(ix)+\
                    matched_row[3]*math.log10(ix)**2))

        return ed_list

class Flared_h(Flared):

    """ Child class for flarED altitude profile for a given solar flux intensity """

    def __init__(self, ix):

        """ initializes parent constructor + sets input ix parameter,
        calculates ED's with flared and easyfit methods """


        super().__init__()
        self.ix = ix
        self.ed_list, self.h_list, self.beta, self.hprim = self._calculate_flared()
        self.ed_easy_list, self.h_easy_list = self._calculate_easyfit()


    def write_and_plot(self):

        """ method which calls writing and plotting methods """

        # write data to a csv file
        self._write_to_csv({
                    'Height(km)': [int(a) for a in self.h_list],
                    'Electron Density(m^-3)': self.ed_list,
                    'Electron Density(m^-3) easyfit': self.ed_easy_list,
                    'Solar Flux(W*m^-2)': [self.ix]*len(self.ed_list),
                    'Beta(km^-1)': [self.beta]*len(self.ed_list),
                    "H'(km)": [self.hprim]*len(self.ed_list)})

        # plot data
        self.plot()

    def plot(self):

        """ plots and saves a figure """

        x = self.h_list
        y = self.ed_list
        y_easy = self.ed_easy_list
        # plot flared and easyfit functions with y as log

        plt.yscale('log')
        plt.plot(x, y, '-o', color="thistle", markersize=4,
                mec='blue', mfc='white', label="flarED method")
        plt.plot(x, y_easy, '-o', color="purple", markersize=4,
                mec='red', mfc='white', label="easyFit method")

        plt.title(r"Ix=%.2E $[\mathrm{W*m^{-2}}$], $\mathrm{\beta}$=%.2E $\mathrm{[km^{-1}]}$, H'=%.2f $[\mathrm{km}]$" \
                %(Decimal(self.ix), Decimal(self.beta), self.hprim), fontdict=self.font)
        plt.legend(loc='best')
        plt.xlabel(r"Height $[\mathrm{km}]$", fontdict=self.font)
        plt.ylabel(r"Electron Density $[\mathrm{m^{-3}}]$", fontdict=self.font)

        plt.savefig("%s/figure.png" % (self.folder))
        plt.show()

    def _calculate_flared(self):

        """ calculate ED's with flarED method """

        beta = float(self.f_beta(self.ix))
        hprim = float(self.f_hprim(self.ix))

        ed_list=[]

        # for a fixed range of h's from 50-90
        h_list = np.arange(50,91)

        # calculate electron density values
        for h in np.nditer(h_list):
            ed_list.append(1.43*10**13*math.exp(-0.15*hprim)*\
                    math.exp((beta-0.15)*(h-hprim)))

        return ed_list, h_list, beta, hprim

    def _calculate_easyfit(self):

        """ calculate ED's with easyfit method """

        a_file = open("data/easyfit.csv")
        reader = csv.reader(a_file, quoting=csv.QUOTE_NONNUMERIC)
        header = next(reader, None)
        rows = list(reader)

        ed_list = []

        # extract first column of each row
        h_list = self._extract_column(rows, 0)

        for row in rows:
            ed_list.append(10**(row[1]+row[2]*math.log10(self.ix)+\
                    row[3]*math.log10(self.ix)**2))

        return ed_list, h_list
