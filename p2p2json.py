#!/usr/bin/python


# Copyright 2008, 2013 Pelle Nilsson (perni@lysator.liu.se)
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
#along with this program; if not, write to the Free Software
#Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

DIALOG_JSON_MESSAGE = """
The above data is in JSON format (see http://www.json.org/), very
easy to parse from almost any programming language. To use it in
a Javascript application all you need to do is Copy-Paste the data
into the script.

If you instead run this effect with an output file specified the
resulting JSON data (as shown above) will be put into that file
(overwriting any previous content of the file).

Format of the data:
The JSON data contains of one big object, containing the string 'points'
that as value has an array of points. Each point is itself an object
containing values for 'x1', 'x2', 'y1', 'y2' (all as floats), and
the 'id' string of the point (from its SVG object).
"""

KEEP_STYLES = {
    'fill' : 'none',
    'stroke' : '#000000',
    'marker' : 'none',
    'marker-start' : 'none',
    'marker-mid' : 'none',
    'marker-end' : 'none',
    'stroke-dasharray' : 'none',
}

import inkex
import json
from inkex import NSS
import os
import os.path
import lxml
from lxml import etree
from copy import deepcopy
import sys
import simplepath

class Rectangle:
    def __init__(self, element):
        self.id = element.get('id')
        self.x1 = float(element.get('x'))
        self.y1 = float(element.get('y'))
        self.x2 = self.x1 + float(element.get('width'))
        self.y2 = self.y1 + float(element.get('height'))
        self.style = parseStyle(element)

    def inside(self, x, y):
        return (x >= self.x1
                and y >= self.y1
                and x < self.x2
                and y < self.y2)

    def toDict(self):
        res = {
            'id' : self.id,
            'x1' : self.x1,
            'x2' : self.x2,
            'y1' : self.y1,
            'y2' : self.y2,
            }
        for n, v in self.style.iteritems():
            res[n] = v
        return res

class Connection:
    "Information about a connection between two rectangles."
    def __init__(self, lastR, r, element):
        self.f = lastR
        self.t = r
        self.style = parseStyle(element)

    def toDict(self):
        res = {
            'f' : self.f.id,
            't' : self.t.id,
            }
        for n, v in self.style.iteritems():
            res[n] = v
        return res

def findRect(rects, x, y):
    for r in rects:
        if r.inside(x, y):
            return r
    return None

def parseStyle(element):
    res = {}
    style = element.get('style')
    for part in style.split(';'):
        if part.find(':') > 0:
            [n, v] = part.split(':')
            if n in KEEP_STYLES and v != KEEP_STYLES[n]:
                res[n] = v
    return res

def add_connection(element, r, lastR, connections, connected_rects):
    if r and lastR:
        connection = Connection(lastR, r, element)
        connections.append(connection)
        connected_rects.add(lastR)
        connected_rects.add(r)


class P2P2JsonEffect(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.outfile = None
        self.nextid = 1000000
        self.OptionParser.add_option('-o', '--outfile', action = 'store',
                                     type = 'string', dest = 'outfile')

    def effect(self):
        doc = self.document
        svg = self.document.xpath('//svg:svg', namespaces=NSS)[0]
        if self.options.outfile:
            outfile = open(self.options.outfile, "w")
        else:
            outfile = None
        rects = []
        connections = []
        connected_rects = set()
        for r in self.current_layer.xpath('//svg:rect', namespaces=NSS):
            rect = Rectangle(r)
            rects.append(rect)
        for p in self.current_layer.xpath('//svg:path', namespaces=NSS):
            d = p.get('d')
            path = simplepath.parsePath(d)
            lastCoord = None
            lastR = None
            for c in path:
                outputCommand = c[0]
                params = c[1]
                if outputCommand == 'M':
                    lastR = findRect(rects, params[0], params[1])
                elif outputCommand == 'L':
                    r = findRect(rects, params[0], params[1])
                    add_connection(p, r, lastR,
                                   connections, connected_rects)
                    lastR = r
                elif outputCommand == 'C':
                    r = findRect(rects, params[4], params[5])
                    add_connection(p, r, lastR,
                                   connections, connected_rects)
                    lastR = r
                else:
                    pass
        res = {}
        res['points'] = [r.toDict() for r in connected_rects]
        res['connections'] = [c.toDict() for c in connections]
        jsonres = json.write(res)
        if outfile:
            outfile.write(jsonres)
        else:
            sys.exit(jsonres + '\n\n' + DIALOG_JSON_MESSAGE)

if __name__ == '__main__':
    effect = P2P2JsonEffect()
    effect.affect()
