# -*- coding: utf-8 -*-
"""
This module provides all functionality for extending Python's suite class of functionality.

The module defines the class PyvsgenSuite.  The PyvsgenSuite class groups the different functionalities into a single class.
"""
import os

from pyvsgen.solution import PyvsgenSolution
from pyvsgen.project import PyvsgenProject
from pyvsgen.interpreter import PyvsgenInterpreter
from pyvsgen.writer import PyWriteCommand
from pyvsgen.register import PyRegisterCommand
from pyvsgen.util.config import PyvsgenConfigParser

class PyvsgenSuite(object):
    
    def __init__(self, filename):
        """
        Constructor.

        :param str filename:  The fully qualified path to the Pyvsgen configuration file.
        """ 
        # Read the configuration file
        config = PyvsgenConfigParser()
        if filename not in config.read(filename):
            raise ValueError('Could not read Pyvsgen configuration file %s.' % filename)

        # Resolve the root path
        root = config.get('pyvsgen', 'root', fallback=None)
        if not root:
            raise ValueError('Expected option "root" in section [pyvsgen].')

        root = os.path.normpath(os.path.join(os.path.dirname(filename), root))
        config.set('pyvsgen', 'root', root)

        # Build the Pyvsgen Solutions
        self._solutions = [self._getsolution(config, s) for s in config.sections() if 'pyvsgen.solution' in s]

        return super(PyvsgenSuite, self).__init__()
    
    def _getsolution(self, config, section, **kwargs):
        """
        Creates a Pyvsgen solution from a configparser instance.

        :param obj config: The instance of the configparser class
        :param str section: The section name to read.
        :param **kwargs:  List of additional keyworded arguments to be passed into the PyvsgenSolution.
        :return: A valid PyvsgenSolution instance if succesful; None otherwise.
        """
        if section not in config:
            raise ValueError('Section [{}] not found in [{}]'.format(section, ', '.join(config.sections())))

        s = PyvsgenSolution(**kwargs)

        s.Name = config.get(section, 'name', fallback=s.Name)
        s.FileName = os.path.normpath(config.get(section, 'filename', fallback=s.FileName))
        s.VSVersion = config.getfloat(section, 'visual_studio_version', fallback=s.VSVersion)
        if not s.VSVersion:
            raise ValueError('Solution section [%s] requires a value for Visual Studio Version (visual_studio_version)' % section)

        project_sections = config.getlist(section, 'projects', fallback=[])
        for project_section in project_sections:
            project = self._getproject(config, project_section, VSVersion=s.VSVersion)
            s.Projects.append(project)
        
        return s

    def _getproject(self, config, section, **kwargs):
        """
        Creates a Pyvsgen project from a configparser instance.

        :param obj config: The instance of the configparser class
        :param str section: The section name to read.
        :param **kwargs:  List of additional keyworded arguments to be passed into the PyvsgenProject.
        :return: A valid PyvsgenProject instance if succesful; None otherwise.
        """
        if section not in config:
            raise ValueError('Section [{}] not found in [{}]'.format(section, ', '.join(config.sections())))

        p = PyvsgenProject(**kwargs)
            
        p.Name = config.get(section, 'name', fallback=p.Name)
        p.FileName = config.getfile(section, 'filename', fallback=p.FileName)
        p.SearchPath = config.getdirs(section, 'search_path', fallback=p.SearchPath)
        p.OutputPath = config.getdir(section, 'output_path', fallback=p.OutputPath)
        p.WorkingDirectory = config.getdir(section, 'working_directory', fallback=p.WorkingDirectory)
        p.RootNamespace = config.get(section, 'root_namespace', fallback=p.RootNamespace)
        p.ProjectHome = config.getdir(section, 'project_home', fallback=p.ProjectHome)
        p.StartupFile = config.getfile(section, 'startup_file', fallback=p.StartupFile)
        p.CompileFiles = config.getlist(section, 'compile_files', fallback=p.CompileFiles)
        p.ContentFiles = config.getlist(section, 'content_files', fallback=p.ContentFiles)
        p.CompileInFilter = config.getlist(section, 'compile_in_filter', fallback=p.CompileInFilter)
        p.CompileExFilter = config.getlist(section, 'compile_ex_filter', fallback=p.CompileExFilter)
        p.ContentInFilter = config.getlist(section, 'content_in_filter', fallback=p.ContentInFilter)
        p.ContentExFilter = config.getlist(section, 'content_ex_filter', fallback=p.ContentExFilter)
        p.DirectoryInFilter = config.getdirs(section, 'directory_in_filter', fallback=p.DirectoryInFilter)
        p.DirectoryExFilter = config.getdirs(section, 'directory_ex_filter', fallback=p.DirectoryExFilter)
        p.IsWindowsApplication =  config.getboolean(section, 'is_windows_application', fallback=p.IsWindowsApplication)
        p.PythonInterpreterArgs = config.getlist(section, 'python_interpreter_args', fallback=p.PythonInterpreterArgs)

        interpreter = config.get(section, 'python_interpreter', fallback=None)
        interpreters = {n:[i for i in self._getinterpreter(config, n, VSVersion=p.VSVersion)] for n in config.getlist(section, 'python_interpreters')}        
        p.PythonInterpreters = [i for v in interpreters.values() for i in v]
        p.PythonInterpreter = next((i for i in interpreters.get(interpreter, [])), None)

        virtual_environments = config.getlist(section, 'python_virtual_environments', fallback=[])
        p.VirtualEnvironments = [ve for n in virtual_environments for ve in self._getvirtualenvironment(config, n, VSVersion=p.VSVersion) ]

        root_path = config.get(section, 'root_path', fallback="")
        p.insert_files(root_path)

        return p


    def _getinterpreter(self, config, section, **kwargs):
        """
        Creates a Pyvsgen Interpreter from a configparser instance.

        :param obj config: The instance of the configparser class
        :param str section: The section name to read.
        :param **kwargs:  List of additional keyworded arguments to be passed into the PyvsgenInterpreter.
        :return: A valid PyvsgenInterpreter instance if succesful; None otherwise.
        """
        if section not in config:
            raise ValueError('Section [{}] not found in [{}]'.format(section, ', '.join(config.sections())))

        interpreters = []
        interpreter_paths = config.getdirs(section, 'interpreter_paths', fallback=[])
        if interpreter_paths:
            interpreters = [PyvsgenInterpreter.from_python_installation( p, **kwargs) for p in interpreter_paths]

        for i in interpreters:
            i.Description = config.get(section, 'description', fallback=i.Description)
        
        return interpreters

    def _getvirtualenvironment(self, config, section, **kwargs):
        """
        Creates a Pyvsgen Interpreter (Virtual Environment) from a configparser instance.

        :param obj config: The instance of the configparser class
        :param str section: The section name to read.
        :param **kwargs:  List of additional keyworded arguments to be passed into the PyvsgenInterpreter.
        :return: A valid PyvsgenInterpreter instance if succesful; None otherwise.
        """
        if section not in config:
            raise ValueError('Section [{}] not found in [{}]'.format(section, ', '.join(config.sections())))
        
        environments = []
        environment_paths = config.getdirs(section, 'environment_paths', fallback=[])
        if environment_paths:
            environments = [PyvsgenInterpreter.from_virtual_environment( p, **kwargs ) for p in environment_paths]

        for e in environments:
            e.Description = config.get(section, 'description', fallback=e.Description)

        return environments

    def write(self, parallel=True):
        """
        Writes the configuration to disk.
        """
        # Write the Solution files
        solutions = sorted(self._solutions, key=lambda x: x.Name)
        with PyWriteCommand('Writing Pyvsgen Solution', solutions, parallel) as command:
            command.execute()

        # Write the Projects files
        projects = set(sorted((p for s in solutions for p in s.Projects), key=lambda x: x.Name))
        with PyWriteCommand('Writing Pyvsgen Projects', projects, parallel) as command:
            command.execute()

        # Write the Interpreters files
        interpreters = set(i for p in projects for i in p.PythonInterpreters)
        with PyRegisterCommand('Registering Python Interpreters', interpreters) as command:
            command.execute()
