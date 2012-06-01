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

import os
import shutil
import stat
import sys
import unittest

import pmatic


class TestSingleTaskPipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Nuke and re-create directory for entire class first.
        make_test_dir('SingleTaskPipeline')

    def setUp(self):
        self.umask = os.umask(022)
        self.uuid_mocker = GenUuidStrMocker()
        self.pmatic_base = os.path.join(
            os.environ['PROJECT_ROOT'], 'test/pmatic_base'
        )
        self.dependency_finder = pmatic.DependencyFinder(self.pmatic_base)
        self.test_dir = make_test_dir('SingleTaskPipeline',
                                      self.id().rsplit('.', 1)[1])
        self.meta_path = pmatic.meta_path(self.test_dir)
        self.event_log = pmatic.EventLog(self.meta_path)
        self.pipeline_loader = pmatic.PipelineLoader(
            self.pmatic_base, self.dependency_finder, self.event_log
        )
        self.cwd = os.getcwd()
        os.chdir(self.test_dir)
        self.orig_stdout = sys.stdout
        os.mkdir('foo')
        os.mkdir('.pmatic')
        sys.stdout = open('.pmatic/out.txt', 'w')  # capture diagnostic prints
        write_file('foo/spam', 'hello\nworld!!!')
        os.symlink('foo/spam', 'eggs')
        if hasattr(os, 'lchmod'):
            os.lchmod('eggs', 00777)
        print self.id().rsplit('.', 1)[1]
        print self.id()
        print os.getcwd()

    def tearDown(self):
        fout = sys.stdout
        sys.stdout = self.orig_stdout
        fout.close()
        os.chdir(self.cwd)
        self.uuid_mocker.close()
        os.umask(self.umask)

    def test_basic(self):
        write_probe('''#!/usr/bin/env bash
                    echo hello world from probe!!!
                    echo example error >&2''')
        pipeline = self.pipeline_loader.load_pipeline('run-probe-1')
        namespace = pmatic.Namespace()
        pipeline.run(namespace)
        scan = pmatic.scan_directory('.')
        # For reproducibility, strip inode out of scan.
        result = {k: (f, m, s, l) for k, (f, m, s, i, l) in scan.iteritems()}
        self.maxDiff = None
        self.assertEqual(
            result,  # TODO: minor portability concerns...
            {'eggs':        ('LNK', 0777,  8L, 'foo/spam'),
             'foo':         ('DIR', 0755,  0L, None),
             'foo/spam':    ('REG', 0444, 15L, None),
             'probe':       ('REG', 0544, 74L, None),
             'probe.err':   ('REG', 0644, 14L, None),
             'probe.out':   ('REG', 0644, 45L, None)}
        )

    def test_revert(self):
        print 'hello'
        write_probe('''#!/usr/bin/env bash
                    echo hello world from probe! | tee bar
                    mv eggs eggs2
                    ls -l foo/spam
                    rm foo/spam
                    ''')
        pipeline = self.pipeline_loader.load_pipeline('run-probe-1')
        namespace = pmatic.Namespace()
        scan1 = pmatic.scan_directory('.')
        pipeline.run(namespace)
        scan2 = pmatic.scan_directory('.')
        self.assertNotEqual(scan1, scan2)
        import pprint
        pprint.pprint(scan1)
        pprint.pprint(scan2)
        pmatic.restore_snapshot(scan1)
        scan3 = pmatic.scan_directory('.')
        pprint.pprint(scan3)
        self.maxDiff = None
        self.assertEqual(scan1, scan3)


class TestEventLog(unittest.TestCase):
    def setUp(self):
        self.uuid_mocker = GenUuidStrMocker()
        self.test_dir = make_test_dir('EventLog')
        self.event_log = pmatic.EventLog(self.test_dir)

    def tearDown(self):
        self.uuid_mocker.close()

    def test_basic(self):
        event_log = self.event_log
        self.assertEqual(event_log.get_status(), 'never_run')
        event_log.record_pipeline_started('test-pipeline-1')
        self.assertEqual(event_log.get_status(), 'started')
        event_log.record_pipeline_finished('test-pipeline-1')
        self.assertEqual(event_log.get_status(), 'finished')


class GenUuidStrMocker(object):
    """During construction, will replace pmatic.gen_uuid_str with a mock.
    Restores original function during close."""
    def __init__(self):
        self.original_gen = pmatic.gen_uuid_str
        gen = ('00000000-0000-0000-0000-%012d' % i for i in xrange(20)).next
        pmatic.gen_uuid_str = gen

    def close(self):
        """Restore original value to pmatic.gen_uuid_str."""
        pmatic.gen_uuid_str = self.original_gen


def make_test_dir(test_dir_name, *subdirs):
    """Compute test_dir_path from test_dir_name. Recursively delete
    test_dir_path if it exists, then create it. Return test_dir_path."""
    test_dir_path = os.path.join(
        os.environ['PROJECT_ROOT'], 'target/test/unit', test_dir_name, *subdirs
    )
    if os.path.isdir(test_dir_path):
        shutil.rmtree(test_dir_path)
    os.makedirs(test_dir_path)
    return test_dir_path


def write_probe(payload):
    """Write an executable file named probe to the working directory."""
    write_file('probe', payload)
    os.chmod('probe', os.stat('probe').st_mode | stat.S_IXUSR)


def write_file(file_path, payload):
    """Convenience method, mainly for writing triple-quoted strings
    that are indented."""
    lines = payload.split('\n')
    dedented_lines = get_dedented_lines(lines)
    with open(file_path, 'w') as fout:
        for line in dedented_lines:
            fout.write(line)
            fout.write('\n')


def get_dedented_lines(lines):
    """Return list of dedented lines"""
    result = []
    first_line_indented, block_value = get_block_indentation(lines)
    if first_line_indented:
        result.append(lines[0][block_value:])
    else:
        result.append(lines[0])
    result.extend(line[block_value:] for line in lines[1:])
    return result


def get_block_indentation(lines):
    """Return amount of first nonzero indentation"""
    first_line_value = get_indentation(lines[0])
    if first_line_value:
        first_line_indented = True
        block_value = first_line_value
    else:
        first_line_indented = False
        remainder = lines[1:]
        if remainder:
            indentations = (get_indentation(line) for line in remainder)
            real_indents = (i for i in indentations if i is not None)
            block_value = min(real_indents)
        else:
            block_value = 0
    return first_line_indented, block_value


def get_indentation(line):
    """Return the number of spaces at the start of line. (1 tab = 8 spaces.)
    Returning None for empty lines."""
    t = line.expandtabs().rstrip()
    if t:
        result = len(t) - len(t.lstrip())
    else:
        result = None
    return result


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
