#!/usr/bin/env python3

import os
from sqlite_utils import *
import math
from collections import defaultdict
import operator
import warnings
from itertools import groupby
from decimal import Decimal
from datetime import datetime, timedelta
import csv
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy.interpolate import interp1d
from scipy.stats import gaussian_kde

class Flared:

    """ parent class for Flare Electron Density calculations """

    def __init__(self):

        """ gets beta and fprim interpolated functions from polyfit,
        sets folder and font """


        self.query, self.ix_vlf, self.beta_vlf, self.hprim_vlf = self._query_db()

        self.f_beta, self.f_hprim, self.ix_vlf_reduced, self.beta_vlf_reduced, \
                self.hprim_vlf_reduced = self._polyfit(self.query)


        self.font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 12,
            }

        self.folder = "%s/%s-%s" % ("results", self.__class__.__name__,
                int(datetime.now().timestamp()))

        if not os.path.exists(self.folder):
            os.mkdir(self.folder)

    def _query_db(self):

        """ queries db for experimental ix, beta and h values """

        database = r"data/flare_vlf.db"
        table_name = 'flares'
        conn = create_connection(database)

        # query for ix,beta,height tuples
        with conn:
            sql = """SELECT ix, beta, reflection_height \
                    FROM %s \
                    ORDER BY ix;""" %(table_name)
            query = custom_query(conn, sql)
        ix_vlf= self._extract_column(query, 0)
        beta_vlf= self._extract_column(query, 1)
        hprim_vlf= self._extract_column(query, 2)

        return query, ix_vlf, beta_vlf, hprim_vlf

    def _polyfit(self, query):

        """ takes experimental values of ix, beta, height from a db,
        make polynomial fit and interpolation of betas and hprim as
        a function of ix """

        ix_values, beta_values, hprim_values = map(list, zip(*self._get_list_of_averages(query)))

        x = ix_values
        y = beta_values
        y2 = hprim_values

        # we fit first most of the curve as 15th degree polynomial,
        # then skip jumpy parts then fit as 1st degree polynomial
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

        return f_beta, f_hprim, x, y, y2

    def _polyfit_linear(self, query):

        """ takes experimental values of ix, beta, height from a db,
        make polynomial fit and interpolation of betas and hprim as
        a function of ix """

        ix_values, beta_values, hprim_values = map(list, zip(*self._get_list_of_averages(query)))

        x = ix_values
        y = beta_values
        y2 = hprim_values

        # we fit first most of the curve as 15th degree polynomial,
        # then skip jumpy parts then fit as 1st degree polynomial
        warnings.filterwarnings('ignore')

        xpoly = np.linspace(x[0], x[-1], num=100, endpoint=True)

        poly_deg = 1
        ypoly = np.polyval(np.polyfit(x, y, poly_deg), xpoly)
        y2poly = np.polyval(np.polyfit(x, y2, poly_deg), xpoly)

        # interpolate and calculate x and y's for the whole range
        f_beta = interp1d(xpoly, ypoly)
        f_hprim = interp1d(xpoly, y2poly)

        return f_beta, f_hprim, x, y, y2

    def _get_list_of_averages(self, query):

        """there might be duplicated values for ix
        make a new list where all the ix duplicates will condense to a single
        value while new beta and h get average value from n duplicates """
        
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
        #list_of_averages[-1] = (0.0001, list_of_averages[-1][1],
        #        list_of_averages[-1][2])

        return list_of_averages

    def plot_polyfit(self):

        """ plot reduced vlf beta and hprim dots (see explanation in _polyfit along with
        interpolated beta and hprim functions of ix """

        x = self.ix_vlf_reduced
        y_l1 = self.beta_vlf_reduced
        y_l2 = self.f_beta(x)
        y_r1 = self.hprim_vlf_reduced
        y_r2 = self.f_hprim(x)

        fig, ax = plt.subplots()
        ax.set_xscale('log')
        lns1 = ax.plot(x, y_l1, 'o', color="thistle", markersize=4,
                mec='blue', mfc='white', label="beta vlf")
        lns2 = ax.plot(x, y_l2, '-', color="thistle", markersize=4,
                mec='red', mfc='white', label="beta interpolation")

        plt.title("Polyfit of beta and hprim")

        ax.set_xlabel(r"Flux Intensity $[\mathrm{W*m^{-2}}]$", fontdict=self.font)
        ax.set_ylabel(r"Beta $[\mathrm{km^{-1}}]$", fontdict=self.font)

        ax2=ax.twinx()
        lns3 = ax2.plot(x, y_r1, 'o', color="green", markersize=4, label="hprim vlf")
        lns4 = ax2.plot(x, y_r2, '-', color="purple", markersize=4, label="hprim interpolation")
        ax2.set_ylabel(r"H' $[\mathrm{km}]$", fontdict=self.font)

        lns = lns1+lns2+lns3+lns4
        labs = [l.get_label() for l in lns]
        ax.legend(lns, labs, loc=1)

        plt.show()

    def plot_param_density(self, data_list, xlabel):

        """ Density and rug plot of a certain parameter (input data list) """

        density = gaussian_kde(data_list)
        xs = np.linspace(min(data_list),max(data_list),200)
        density.covariance_factor = lambda : .25
        density._compute_covariance()
        fig, ax = plt.subplots()
        ax.plot(xs,density(xs))
        ax.plot(data_list, [0.0001]*len(data_list), '|', color='r')
        ax.set_xlabel(xlabel, fontdict=self.font)
        ax.set_ylabel(r"Density(x)", fontdict=self.font)
        plt.title("Density and Rug plot")

        plt.show()

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
                self.timestamp_list, self.timestamp_delta_list = self._calculate_flared()
        self.ed_easy_list = self._calculate_easyfit(self.ix_list)

    def write_and_plot(self):

        """ method which invokes writing and plotting methods """
        timestamp_list_hms = []
        for t in self.timestamp_list:
            timestamp_list_hms += [t.strftime("%H:%M:%S")]

        timestamp_delta_list_hms = []
        for t in self.timestamp_delta_list:
            timestamp_delta_list_hms += [t.strftime("%H:%M:%S")]
        

        # write data to a csv file
        self._write_to_csv({
                    'Height(km)': [self.h]*len(self.timestamp_list),
                    'Time(Ix) (H:M:S)': timestamp_list_hms,
                    'Solar Flux Ix (W*m^-2)': self.ix_list,
                    'Time(ED) (H:M:S)': timestamp_delta_list_hms,
                    'Electron Density(m^-3)': self.ed_list,
                    'Electron Density(m^-3) easyfit': self.ed_easy_list,
                    'Beta(km^-1)': self.beta_list,
                    "H'(km)": self.hprim_list})

        # plot data
        self.plot()

    def plot(self):

        """ plots and saves a figure """

        # convert to times suitable for plotting
        x = matplotlib.dates.date2num(self.timestamp_list)
        x_delta = matplotlib.dates.date2num(self.timestamp_delta_list)

        y = self.ed_list
        y_easy = self.ed_easy_list
        y_ix = self.ix_list

        # plot flared and easyfit ed's as y(log)
        # plot ix's as y2(log)
        # plot times as x
        fig, ax = plt.subplots()
        ax.set_yscale('log')
        lns1 = ax.plot(x_delta, y, '-o', color="thistle", markersize=4,
                mec='blue', mfc='white', label="flarED method")
        lns2 = ax.plot(x_delta, y_easy, '-o', color="thistle", markersize=4,
                mec='red', mfc='white', label="easyFit method")

        plt.title(r"H=%s km" %(self.h))
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

        ix_list = self._extract_column(rows, 1)
        ix_list = [float(i) for i in ix_list]

        # for ED values we incorporate time delay due to the
        # slughiness of the ionosphere, based on statistics of SF events
        stamps = self._extract_column(rows, 0)
        timestamp_list = [datetime.strptime(a, '%H:%M') for a in stamps]
        delta_t = 0.45385 + (-0.44863*math.log10(max(ix_list, 
            key=lambda x:float(x))))
        timestamp_delta_list = []
        for t in timestamp_list: 
            timestamp_delta_list += [t+timedelta(minutes=delta_t)]

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
                beta = min(self.f_beta(ix))
                hprim = min(self.f_hprim(ix))
            else:
                beta = float(self.f_beta(ix))
                hprim = float(self.f_hprim(ix))
            beta_list.append(beta)
            hprim_list.append(hprim)
            ed_list.append(1.43*10**13*math.exp(-0.15*hprim)*\
                    math.exp((beta-0.15)*(self.h-hprim)))

        return ed_list, ix_list, beta_list, hprim_list, timestamp_list, timestamp_delta_list

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
