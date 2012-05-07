"""Top level test package for the Pipe-o-matic pipeline framework."""

# Author: Walker Hale (hale@bcm.edu), 2012
#         Human Genome Sequencing Center, Baylor College of Medicine
#
# This file is part of Pipe-o-matic.
#
# Pipe-o-matic is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pipe-o-matic is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pipe-o-matic.  If not, see <http://www.gnu.org/licenses/>.

import unittest

import pmatic


class TestNamespace(unittest.TestCase):
    def setUp(self):
        m1, m2 = make_maps()
        self.n0 = pmatic.Namespace()
        self.n1 = pmatic.Namespace(m1, b=5, c=6)
        self.n2 = pmatic.Namespace(m1, m2, d=7)

    def test_empty(self):
        n0 = self.n0
        self.assertEqual(len(n0), 0)
        n0.a = 41
        n0.b = 42
        self.assertEqual(len(n0), 2)
        self.assertEqual(n0.a, 41)
        self.assertEqual(n0, dict(a=41, b=42))
        self.assertEqual(n0.mapping, dict(a=41, b=42))
        self.assertEqual(n0.mapping, pmatic.ChainMap(a=41, b=42))
        self.assertEqual(list(n0), ['a', 'b'])
        self.assertEqual(sorted(n0.iteritems()), [('a', 41), ('b', 42)])

    def test_full(self):
        n2 = self.n2
        self.assertEqual(len(n2), 4)
        n2.a = 41
        n2.b = 42
        self.assertEqual(len(n2), 4)
        self.assertEqual(n2.a, 41)
        self.assertEqual(n2, dict(a=41, b=42, c=4, d=7))

    def test_deep(self):
        n2 = self.n2
        n2.e = 8
        self.assertEqual(
            n2.mapping,
            pmatic.ChainMap(
                dict(a=1, b=2),
                dict(a=3, c=4),
                dict(d=7, e=8)
            )
        )


class TestChainMap(unittest.TestCase):
    def setUp(self):
        m1, m2 = make_maps()
        self.c0 = pmatic.ChainMap()
        self.c1 = pmatic.ChainMap(m1, b=5, c=6)
        self.c2 = pmatic.ChainMap(m1, m2, d=7)

    def test_empty(self):
        c0 = self.c0
        self.assertFalse('z' in c0)
        self.assertRaises(StopIteration, iter(c0).next)
        self.assertEqual(len(c0), 0)
        self.assertEqual(sorted(c0), [])

    def test_kwds(self):
        c = pmatic.ChainMap(a=41, b=42)
        self.assertEqual(c, dict(a=41, b=42))
        self.assertEqual(c.mappings, [dict(a=41, b=42)])

    def test_equality(self):
        self.assertEqual(self.c0, {})
        self.assertEqual(self.c1, dict(a=1, b=5, c=6))
        self.assertEqual(self.c2, dict(a=3, b=2, c=4, d=7))

    def test_containment(self):
        c1 = self.c1
        self.assertTrue('a' in c1)
        self.assertTrue('b' in c1)
        self.assertTrue('c' in c1)
        self.assertFalse('z' in c1)

    def test_lookup(self):
        c1 = self.c1
        self.assertEqual(c1['a'], 1)
        self.assertEqual(c1['b'], 5)
        self.assertEqual(c1['c'], 6)

    def test_iteration(self):
        c1 = self.c1
        c2 = self.c2
        self.assertEqual(len(c1), 3)
        self.assertEqual(sorted(c1), ['a', 'b', 'c'])
        self.assertEqual(
            sorted(c1.iteritems()), [('a', 1), ('b', 5), ('c', 6)]
        )
        self.assertEqual(
            sorted(c2.iteritems()), [('a', 3), ('b', 2), ('c', 4), ('d', 7)]
        )

    def test_modify(self):
        c2 = self.c2
        c2['e'] = 8
        self.assertEqual(
            sorted(c2.iteritems()),
            [('a', 3), ('b', 2), ('c', 4), ('d', 7), ('e', 8)]
        )
        del c2['d'], c2['e']
        self.assertEqual(
            sorted(c2.iteritems()), [('a', 3), ('b', 2), ('c', 4)]
        )

    def test_deep(self):
        c2 = self.c2
        c2['e'] = 8
        self.assertEqual(
            c2.mappings,
            [
                dict(a=1, b=2),
                dict(a=3, c=4),
                dict(d=7, e=8)
            ]
        )


def make_maps():
    """Generate some maps for testing"""
    m1 = dict(a=1, b=2)
    m2 = dict(a=3, c=4)
    return m1, m2
