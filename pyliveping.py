#!/usr/bin/env python
# encoding: utf-8
from __future__ import print_function
from __future__ import division
"""
liveping
"""

import logging
import os
import re
import subprocess
import math

log = logging.getLogger()

TIME_RGX = re.compile(
    r'(\d+) bytes from ([\d.]+): icmp_req=(\d+) ttl=(\d+) time=([\d].+) ms')

from collections import namedtuple
IcmpResponse_ = namedtuple('IcmpResponse', ('bytes', 'addr', 'req', 'ttl', 'time'))
class IcmpResponse(IcmpResponse_):
    def __new__(cls, bytes, addr, req, ttl, time):
        bytes = int(bytes)
        #addr = addr
        req = int(req)
        ttl = int(ttl)
        time = float(time)
        return super(IcmpResponse, cls).__new__(cls, bytes, addr, req, ttl, time)


def run_ping(host, count=0, deadline=0):
    cmd = ('ping', host)
    if count != 0:
        cmd = cmd + ('-c', str(count))
    if deadline != 0:
        cmd = cmd + ('-w', str(deadline))
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    for line in iter(p.stdout.readline, ''):
        line = line.rstrip()
        match_obj = TIME_RGX.match(line)
        if match_obj:
            yield IcmpResponse(*match_obj.groups() )


class PingDist(object):
    def __init__(self):
        self.responses = []
        self.times = []
        self.reqs = []

    def push(self, resp):
        prev = None
        if self.responses:
            prev = self.responses[-1]
        self.responses.append(resp)
        self.times.append(resp.time)
        self.reqs.append(resp.req)

        if prev:
            expected_req = prev.req + 1
            if resp.req != (expected_req):
                if resp.req > expected_req:
                    log.error("skipped req: %r %r" % (resp.req, expected_req))
                elif resp.req < expected_req:
                    log.error("out of order req: %r %r" % (resp.req, expected_req))


class AsciiChart(object):
    """
    what do i want to do here?

    i want to [re-]draw an ascii chart
    within a terminal window (80 x ??)
    of (positive) values
    with something like a binned/rolling average
    so that all of the data is displayed
    in the screen
    with full screen redraw


    screen_height = 80
    screen_width = 80


    """
    def __init__(self, screen_width=80, screen_height=34):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.data = []
        self.min = 0
        self.max = 0
        self.scale_factor = 1

    def add_point(self, point):
        self.data.append(point)
        if point > self.max:
            self.max = point
            self.scale_factor = self.screen_width / self.max
        #elif point < self.min:
        #    self.min = point

    def bin_data(self):
        data = self.data
        bin_width = math.ceil( len(data) / self.screen_height )  # 'stride'
        bin_count = int( (len(data) / bin_width) )

        log.debug("width: %d, scale: %d, count: %d", bin_width, self.scale_factor, bin_count)
        for n in xrange(bin_count):
            start = int( n * bin_width )
            end = int( (n + 1) * bin_width )
            points = data[start:end]
            #log.debug("%d %d %r" % (start, end, points))
            avg = sum(points) / len(points)
            yield avg

    def rescale_data(self, value):
        # proportional equality: screen_height / data_max == x / data_value
        # ... x = data_value * (screen_height / data_max)
        return value * (self.screen_width / self.max) # self.scale_factor

    def draw(self):
        os.system('clear')  # no curses yet
        #print('---')
        bar_char = '-'
        tip_char = '*'
        for value in self.bin_data():
            y_coord = self.rescale_data(value)
            # Transposed, for now
            print("%s%s" % (bar_char * int(y_coord - 1), tip_char))





def liveping(host):
    """
    mainfunc
    """
    dist = PingDist()
    chart = AsciiChart()

    for resp in run_ping(host): # TODO: passthrough args
        dist.push(resp)
        chart.add_point(resp.time)
        chart.draw()


import unittest
class Test_liveping(unittest.TestCase):
    def test_run_ping(self):
        for resp in run_ping('127.0.0.1', deadline=5):
            print(resp)

    def test_liveping(self):
        pass


def main():
    import optparse
    import logging

    prs = optparse.OptionParser(usage="./%prog : args")

    prs.add_option('-v', '--verbose',
                    dest='verbose',
                    action='store_true',)
    prs.add_option('-q', '--quiet',
                    dest='quiet',
                    action='store_true',)
    prs.add_option('-t', '--test',
                    dest='run_tests',
                    action='store_true',)

    (opts, args) = prs.parse_args()

    if not opts.quiet:
        logging.basicConfig()

        if opts.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

    if opts.run_tests:
        import sys
        sys.argv = [sys.argv[0]] + args
        import unittest
        sys.exit(unittest.main())

    host = args[0]
    liveping(host)

if __name__ == "__main__":
    main()
