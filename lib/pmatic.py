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
import string
import sys

import yaml


META_DIR_NAME = '.pmatic'


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
        self.meta_path = os.path.join(self.context, META_DIR_NAME)
        self.verbose = verbose
        self.params = params
        self.pipeline = None
        self.pipeline_loader = PipelineLoader(pmatic_base)
        self.event_log = EventLog(self.meta_path)
        self.dependency_finder = DependencyFinder(pmatic_base)

    def run(self):
        """Main starting point. Will attempt to start or restart the
        pipeline."""
        self.debug('running %(pipeline_name)s in %(context)s', self.__dict__)
        insure_directory_exists(self.meta_path)
        # TODO: Add command-line support for creating context directory.
        self.load_pipeline()
        self.event_log.insure_log_exists()
        self.event_log.read_log()
        current_pipeline = self.event_log.get_current_pipeline_name()
        if current_pipeline and current_pipeline != self.pipeline_name:
            fail(
                'Cannot run, because another pipeline (%r) '
                + 'is currently running',
                current_pipeline
            )
        dependencies = self.pipeline.get_dependencies()
        unlisted = set(dependency for dependency in dependencies
                  if not self.dependency_finder.check_listed(dependency))
        missing = set(dependency for dependency in (dependencies - unlisted)
                  if not self.dependency_finder.check_exists(dependency))
        bad_type = set(dependency for dependency
                   in (dependencies - unlisted - missing)
                   if not self.dependency_finder.check_type(dependency))
        if unlisted or missing or bad_type:
            fail_dependencies(
                self.dependency_finder, unlisted, missing, bad_type
            )
        pass  # TODO

    def status(self):
        """Print to stderr and set exit code if error state."""
        pass  # TODO

    def load_pipeline(self):
        """Load the pipeline designated by self.pipeline_name."""
        self.pipeline = self.pipeline_loader.load_pipeline(self.pipeline_name)

    def debug(self, message='', *args):
        """Format and print to stderr if verbose."""
        if self.verbose:
            print_err(message, *args)


class EventLog(object):
    """Manages recording a reading of pipeline events."""
    def __init__(self, meta_path):
        super(EventLog, self).__init__()
        self.meta_path = meta_path
        self.log_data = None

    def insure_log_exists(self):
        """Create empty log inside self.meta_path if it is missing."""
        pass  # TODO

    def read_log(self):
        """Read or re-read log from disk"""
        pass  # TODO

    def get_current_pipeline_name(self):
        pass  # TODO
        # return 'spam'


class DependencyFinder(object):
    """Keeps track of where the dependencies are located on disk."""
    def __init__(self, pmatic_base):
        super(DependencyFinder, self).__init__()
        self.pmatic_base = pmatic_base
        deployments_path = deployment_file_path(pmatic_base)
        with open(deployments_path) as fin:
            deployment_data = yaml.load(fin)
        file_type = deployment_data.pop('file_type')
        assert file_type == 'deployments-1', 'bad type of ' + deployments_path
        dependency_paths = {}
        for name, version_map in deployment_data.iteritems():
            for version, path in version_map.iteritems():
                dependency_paths[(name, version)] = self.construct_path(path)
        self.dependency_paths = dependency_paths

    def check_listed(self, dependency):
        """Verify that dependency is listed in deployments file."""
        name, version, dependency_type = dependency
        result = (name, version) in self.dependency_paths
        return result

    def check_exists(self, dependency):
        """Verify that dependency exists.
        Assumes dependency is listed in the deployments file."""
        path = self.path(dependency)
        result = os.path.exists(path)
        return result

    def check_type(self, dependency):
        """Verify that dependency has correct type.
        Assumes dependency is listed and exists."""
        path, dependency_type = self.path_and_type(dependency)
        test = {
            'directory': os.path.isdir,
            'file': os.path.isfile,
            'executable': is_executable,
            'link': os.path.islink,
        }[dependency_type]
        result = test(path)
        return result

    def path(self, dependency):
        """Return absolute path to dependency."""
        return self.path_and_type(dependency)[0]

    def path_and_type(self, dependency):
        """Return pair of (absolute path & type)."""
        name, version, dependency_type = dependency
        return self.dependency_paths[(name, version)], dependency_type

    def construct_path(self, path):
        """Return absolute value of path."""
        t = string.Template(path)
        result = abspath(t.substitute(dict(pmatic_base=self.pmatic_base)))
        return result


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

    @abc.abstractmethod
    def get_dependencies(self):
        """Recursively generate a set of all
        (dependency, version, dependency_type) triplets."""
        raise NotImplementedError


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

    def get_dependencies(self):
        """Requirement of AbstractPipeline"""
        return set([(self.executable, self.version, 'executable')])


def fail_dependencies(dependency_finder, unlisted, missing, bad_type):
    if unlisted:
        print_err('The following dependencies are not listed in %s:',
                  deployment_file_path(dependency_finder.pmatic_base))
        for dependency in sorted(unlisted):
            print_err('%r', dependency)
    if missing:
        print_err('The following dependencies are missing:')
        for dependency in sorted(missing):
            print_err('%r', dependency_finder.path(dependency))
    if bad_type:
        print_err('The following dependencies have the wrong type:')
        for dependency in sorted(bad_type):
            path, dependency_type = dependency_finder.path_and_type(dependency)
            print_err('need %r: %r', dependency_type, path)
    exit(1)


def fail(message, *args):
    """Format message to stderr and exit with a code of 1."""
    print_err(message, *args)
    exit(1)


def print_err(message, *args):
    """Format and print to stderr"""
    if len(args) == 1:
        args = args[0]
    message_str = message % args
    print >>sys.stderr, message_str


def exit(code):
    sys.exit(code)


def insure_directory_exists(dir_path):
    if not os.path.isdir(dir_path):
        os.mkdir(dir_path)


def is_executable(path):
    """Return True if path is an executable. (Unix only)"""
    return os.path.isfile(path) and os.access(path, os.X_OK)


def deployment_file_path(pmatic_base):
    return os.path.join(pmatic_base, 'deployments.yaml')


def pipeline_path(pmatic_base, pipeline_name):
    """Return the path to the specified pipeline."""
    return os.path.join(pmatic_base, 'pipelines', pipeline_name + '.yaml')


def abspath(path):
    """Convenience composition of os.path.abspath and os.path.expanduser"""
    return os.path.abspath(os.path.expanduser(path))


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
