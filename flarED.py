#!/usr/bin/env python3

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

class flarED:

    def __init__(self):
        """ get beta and fprim interpolated functions from polyfit """
        self.f_beta, self.f_hprim = self._polyfit()

    def flared_h(self, h):

        self.h = h

        a_file = open("data/kontrolno_74.csv")
        reader = csv.reader(a_file)
        #reader = csv.reader(a_file, quoting=csv.QUOTE_NONNUMERIC)
        #for i in range(0,310):
        #    header = next(reader, None)
        header = next(reader, None)
        rows = list(reader)
        a_file.close()

        stamps = self._extract_column(rows, 0)
        ixs = self._extract_column(rows, 1)
        ixs = [float(i) for i in ixs]
        timestamps = [datetime.strptime(a, '%H:%M') for a in stamps]

        ed_control = self._extract_column(rows, 2)
        ed_control = [float(i) for i in ed_control]

        ed_list = []

        for ix in ixs:
            if ix<8e-07:
                beta = 0.3
                hprim = 74
            elif ix>0.0001:
                beta = float(self.f_beta(0.0001))
                hprim = float(self.f_hprim(0.0001))
            else:
                beta = float(self.f_beta(ix))
                hprim = float(self.f_hprim(ix))
            ed_list.append(1.43*10**13*math.exp(-0.15*hprim)*\
                    math.exp((beta-0.15)*(h-hprim)))
        times = matplotlib.dates.date2num(timestamps)

        #easyfit
        with open("data/easyfit.csv", 'r') as a_file:
            reader = csv.reader(a_file)
            rows = list(reader)
            matched_row = [row for row in rows if row[0] == str(self.h)][0]

        matched_row = [float(i) for i in matched_row]
        ed_easyfit=[]

        for ix in ixs:
            ed_easyfit.append(10**(matched_row[1]+matched_row[2]*math.log10(ix)+\
                    matched_row[3]*math.log10(ix)**2))

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 12,
            }

        fig, ax = plt.subplots()
        ax.set_yscale('log')
        lns1 = ax.plot(times, ed_list, '-o', color="thistle", markersize=4,
                mec='blue', mfc='white', label="flarED method")
        #lns2 = ax.plot(times, ed_control, '-o', color="thistle", markersize=4,
        #        mec='red', mfc='white', label="LWPC")
        lns2 = ax.plot(times, ed_easyfit, '-o', color="thistle", markersize=4,
                mec='red', mfc='white', label="easyFit method")

        plt.title(r"H=74km")
        #ax.legend(loc='best')
        myFmt = matplotlib.dates.DateFormatter('%H:%M')
        plt.gca().xaxis.set_major_formatter(myFmt)

        ax.set_xlabel(r"time $[\mathrm{h:m}]$", fontdict=font)
        ax.set_ylabel(r"Electron Density $[\mathrm{m^{-3}}]$", fontdict=font)

        ax2=ax.twinx()
        lns3 = ax2.plot(times, ixs, '-', color="purple", markersize=4,
                mec='green', mfc='white', label="Ix")
        ax2.set_ylabel(r"Flux Intensity $[\mathrm{W*m^{-2}}]$", fontdict=font)
        ax2.set_yscale('log')

        lns = lns1+lns2+lns3
        labs = [l.get_label() for l in lns]
        ax.legend(lns, labs, loc=0)

        plt.show()

    def calculate_and_plot(self, ix):

        self.ix = ix

        y, x, beta, hprim = self._calculate_flared()
        y_easy, x_easy = self._calculate_easyfit()

        f = interp1d(x, y)
        f_easy = interp1d(x_easy, y_easy)

        # plot flared and easyfit functions with y as log
        xnew = x
        ynew = f(x)
        xnew_easy = x_easy
        ynew_easy = f_easy(x_easy)

        for h in x_easy:
            print("%s, %s" % (f(h), f_easy(h)))

        font = {'family': 'serif',
            'color':  'darkred',
            'weight': 'normal',
            'size': 12,
            }
        plt.yscale('log')
        plt.plot(xnew, ynew, '-o', color="thistle", markersize=4,
                mec='blue', mfc='white', label="flarED method")
        plt.plot(xnew_easy, ynew_easy, '-o', color="purple", markersize=4,
                mec='red', mfc='white', label="easyFit method")

        plt.title(r"Ix=%.2E $[\mathrm{W*m^{-2}}$], $\mathrm{\beta}$=%.2E $\mathrm{[km^{-1}]}$, H'=%.2f $[\mathrm{km}]$" \
                %(Decimal(self.ix), Decimal(beta), hprim), fontdict=font)
        plt.legend(loc='best')
        plt.xlabel(r"Height $[\mathrm{km}]$", fontdict=font)
        plt.ylabel(r"Electron Density $[\mathrm{m^{-3}}]$", fontdict=font)

        plt.show()

    def _calculate_flared(self):

        beta = float(self.f_beta(self.ix))
        hprim = float(self.f_hprim(self.ix))

        ed_list=[]

        # for a fixed range of h's from 50-90
        h_list = np.arange(50,91)

        # calculate electron density values
        for h in np.nditer(h_list):
            ed_list.append(1.43*10**13*math.exp(-0.15*hprim)*\
                    math.exp((beta-0.15)*(h-hprim)))

        # write ix and height tuples to a csv file
        self._write_to_csv("flared", h_list, ed_list)

        # write parameterers to a txt file
        self._write_to_txt(beta, hprim)

        return ed_list, h_list, beta, hprim

    def _calculate_easyfit(self):

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

        # write ix and height tuples to a csv file
        self._write_to_csv("easyfit", h_list, ed_list)

        return ed_list, h_list


    def _polyfit(self):

        """ take experimental values of ix, beta, height from a db,
        make polynomial fit and interpolation of betas and hprim as
        a function of ix """

        database = r"data/flarED.db"
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

    @staticmethod
    def _extract_column(rows, column):
        """return a specific column from a list of rows"""
        return [row[column] for row in rows]

    def _write_to_csv(self, fit_type, h_list, ed_list):
        """write ed's and heights to csv
        flared or easyfit
        """
        ed_filename = "results/ed(ix=%.2E)-%s.csv" % (self.ix, fit_type)
        with open(ed_filename, mode='w', newline='') as f:
            fieldnames = ['Height(km)','Electron Density(m^-3)']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for i in range(len(h_list)):
                writer.writerow({'Height(km)': int(h_list[i]),
                    'Electron Density(m^-3)': ed_list[i]})

    def _write_to_txt(self, beta, hprim):
        """write ix beta and hprim to a parameters.txt """
        params_filename = "results/params(ix=%.2E).txt" % (self.ix)
        with open(params_filename, mode='w') as f:
            f.write("ix = %.2E\n" %(self.ix))
            f.write("beta = %.2E\n" %(beta))
            f.write("hprim = %.2f" %(hprim))
