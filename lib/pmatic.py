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

import abc
import collections
import itertools
import os
import sys

import yaml


class PipelineEngine(object):
    def __init__(
            self, pipeline_name, pmatic_base, context_path,
            verbose=False, params=None
        ):
        """command is a Namespace from parsing the command line.
        Typical values:
        pipeline_name='foo-1',
        pmatic_base='/...pipe-o-matic/test/pmatic_base',
        context='/.../pipe-o-matic/target/test/case01/execute',
        verbose=False,
        params=None
        """
        super(PipelineEngine, self).__init__()
        self.pipeline_name = pipeline_name
        self.pmatic_base = abspath(pmatic_base)
        self.context = abspath(context_path)
        self.meta_path = os.path.join(self.context, '.pmatic')
        self.verbose = verbose
        self.params = params
        self.pipeline = None
        self.pipeline_loader = PipelineLoader(pmatic_base)

    def run(self):
        """Main starting point. Will attempt to start or restart the
        pipeline."""
        if self.verbose:
            print >>sys.stderr, (
                "running %(pipeline_name)s in %(context)s" % self.__dict__
            )
        if os.path.isdir(self.meta_path):
            os.mkdir(self.meta_path)
            # TODO: Add command-line support for creating context directory.
        self.load_pipeline()
        pass  # TODO

    def status(self):
        """Print to stderr and set exit code if error state."""
        pass  # TODO

    def load_pipeline(self):
        """Load the pipeline designated by self.pipeline_name."""
        self.pipeline = self.pipeline_loader.load_pipeline(self.pipeline_name)
        import pprint
        pprint.pprint(vars(self.pipeline))


class PipelineLoader(object):
    """Maintains a registry of Pipeline classes and constructs pipelines from
    files."""
    def __init__(self, pmatic_base):
        super(PipelineLoader, self).__init__()
        self.pmatic_base = pmatic_base

    def load_pipeline(self, pipeline_name):
        """Return pipeline object."""
        with open(pipeline_path(self.pmatic_base, pipeline_name)) as fin:
            data = yaml.load(fin)
        try:
            meta_map = data[0]
        except KeyError:
            meta_map = data
        file_type = meta_map['file_type']
        pipeline_class_name, version = file_type.rsplit('-', 1)
        # TODO: Select class based on pipeline_class_name
        klass = SingleTaskPipeline
        return klass(version, data, pipeline_name)


class AbstractPipeline(object):
    """Abstract base class for all pipeline classes."""
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(AbstractPipeline, self).__init__()


class SingleTaskPipeline(AbstractPipeline):
    """Pipelines that wrap just one executable."""
    def __init__(self, version, data, pipeline_name=None):
        super(SingleTaskPipeline, self).__init__()
        assert version == '1', 'SingleTaskPipeline currently only version 1'
        self.pipeline_name = pipeline_name
        self.executable = None
        self.version = None
        self.arguments = []
        self.stdout = None
        self.stdin = None
        self.__dict__.update(data)
        assert self.executable
        assert self.version
        pass  # TODO


def abspath(path):
    """Convenience composition of os.path.abspath and os.path.expanduser"""
    return os.path.abspath(os.path.expanduser(path))


def pipeline_path(pmatic_base, pipeline_name):
    """Return the path to the specified pipeline."""
    return os.path.join(pmatic_base, 'pipelines', pipeline_name + '.yaml')


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
