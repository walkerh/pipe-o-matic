"""Top level package for the Pipe-o-matic pipeline framework."""

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

import collections
import itertools
import os
import sys


class PipelineEngine(object):
    def __init__(
            self, pipeline, pmatic_path, context_path,
            verbose=False, params=None
        ):
        """command is a Namespace from parsing the command line.
        Typical values:
        pipeline='foo-1',
        pmatic_path='/...pipe-o-matic/test/pmatic_base',
        context='/.../pipe-o-matic/target/test/case01/execute',
        verbose=False,
        params=None
        """
        super(PipelineEngine, self).__init__()
        self.pipeline = pipeline
        self.pmatic_path = abspath(pmatic_path)
        self.context = abspath(context_path)
        self.verbose = verbose
        self.params = params

    def run(self):
        """Main starting point. Will attempt to start or restart the
        pipeline."""
        if self.verbose:
            print >>sys.stderr, (
                "running %(pipeline)s in %(context)s" % self.__dict__
            )
        pass  # TODO

    def status(self):
        """Print to stderr and set exit code if error state."""
        pass  # TODO


def abspath(path):
    """Convenience composition of os.path.abspath and os.path.expanduser"""
    return os.path.abspath(os.path.expanduser(path))


def pipeline_path(pmatic_path, pipeline):
    """Return the path to the specified pipeline."""
    return os.path.join(pmatic_path, 'pipelines', pipeline + '.yaml')


class Namespace(collections.Mapping):
    """Holds arbitrary attributes. Access either as an object or a mapping."""
    def __init__(self, *mappings, **kwds):
        super(Namespace, self).__init__()
        # Cannot use normal self.x=y, because we have __setattr__.
        mapping = ChainMap(*mappings, **kwds)
        super(Namespace, self).__setattr__('mapping', mapping)

    def __setattr__(self, name, value):
        self.mapping[name] = value

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.mapping)

    def __getattr__(self, name):
        return self.mapping[name]

    def __getitem__(self, key):
        return self.mapping[key]

    def __setitem__(self, key, value):
        self.mapping[key] = value

    def __delitem__(self, key):
        del self.mapping

    def __contains__(self, key):
        return key in self.mapping

    def __len__(self):
        return len(self.mapping)

    def __iter__(self):
        return iter(self.mapping)


class ChainMap(collections.Mapping):
    """Simple wrapper around a list of dicts. Last wins. Modifications apply
    to the possibly empty kwds mapping."""
    def __init__(self, *mappings, **kwds):
        super(ChainMap, self).__init__()
        self.mappings = list(mappings)
        self.mappings.append(kwds)

    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.mappings)

    def __getitem__(self, key):
        for mapping in self.mappings[::-1]:
            if key in mapping:
                return mapping[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        self.mappings[-1][key] = value

    def __delitem__(self, key):
        del self.mappings[-1][key]

    def __contains__(self, key):
        for mapping in self.mappings:
            if key in mapping:
                return True
        return False

    def __iter__(self):
        return iter(set(itertools.chain(*self.mappings)))

    def __len__(self):
        return len(set(itertools.chain(*self.mappings)))
