##########################################################################
# pylogparser - Copyright (C) AGrigis, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
import unittest
import os
import sys
import tempfile
# COMPATIBILITY: since python 3.3 mock is included in unittest module
python_version = sys.version_info
if python_version[:2] <= (3, 3):
    import mock
else:
    import unittest.mock as mock

# Pylogparser import
import pylogparser
from pylogparser import LogParser
from pylogparser import dump_log_es
from pylogparser import tree


class LogParserTests(unittest.TestCase):
    """ Test the module functionalities.
    """
    def setUp(self):
        """ Define function parameters.
        """
        self.demodir = os.path.abspath(
            os.path.join(os.path.dirname(pylogparser.__file__), "demo"))

    def test_singleton(self):
        """ Test the singleton pattern.
        """
        parser1 = LogParser()
        parser2 = LogParser()
        self.assertEqual(id(parser1), id(parser2))

    def test_logfile(self):
        """ Test the logfile parser.
        """
        parser = LogParser()
        parser.data.clear()
        for basename in ("fsreconall_1.txt", "fsreconall_2.txt"):
            logfile = os.path.join(self.demodir, basename)
            parser.parse_logfile(
                logfile=logfile,
                job_pattern="job_\d+",
                timestamp_pattern="\d{4}-\d{2}-\d{2}T\d{2}:\d{2}",
                custom_patterns={
                    "code_in_study": {
                        "regex": "subjectid = \d{4}",
                        "splitter": (" = ", 1)
                    },
                    "cmd": {
                        "regex": "cmd = .*",
                        "splitter": (" = ", 1)
                    },
                    "exitcode": {
                        "regex": "exitcode = \d",
                        "splitter": (" = ", 1)
                    },
                    "hostname": {
                        "regex": "hostname = .*",
                        "splitter": (" = ", 1)
                    }
                },
                hierarchy={
                    "job_id": {
                        "code_in_study": {
                            "timestamp": {
                                "custom_data": None
                            }
                        }
                    }
                },
                jobs_alias="project1_freesurfer")
        self.assertEqual(sorted(parser.data.keys()), ["project1_freesurfer"])

    def test_logdir(self):
        """ Test the logdir parser.
        """
        parser = LogParser()
        parser.data.clear()
        for name in ("dtifit_0001", "dtifit_0002"):
            dirfiles = {
                os.path.join(self.demodir, name, "runtime.json"): True,
                os.path.join(self.demodir, name, "inputs.json"): False,
                os.path.join(self.demodir, name, "outputs.json"): False
            }
            parser.parse_logdir(
                logfiles=dirfiles,
                job_name="project1_dtifit",
                timestamp_key="timestamp",
                hierarchy={
                    "job_name": {
                        "subjectid": {
                            "timestamp": {
                                "custom_data": None
                            }
                        }
                    }
                },
                extract_keys=["subjectid"])
        self.assertEqual(sorted(parser.data.keys()), ["project1_dtifit"])

    def test_load(self):
        """ Test the load method.
        """
        parser = LogParser()
        parser.data.clear()
        descfile = os.path.join(self.demodir, "pylogparser_demo.json")
        modify_descfile = tempfile.NamedTemporaryFile(suffix=".json").name
        with open(descfile, "rt") as open_file:
            jbuffer = open_file.read().replace("DEMODIR", self.demodir)
        with open(modify_descfile, "wt") as open_file:
            open_file.write(jbuffer)
        LogParser.load(modify_descfile, verbose=0)
        os.remove(modify_descfile)
        self.assertEqual(sorted(parser.data.keys()),
                         ["project2_dtifit", "project2_freesurfer"])

    def test_tree(self):
        """ Test the tree command.
        """
        parser = LogParser()
        parser.data.clear()
        name = "dtifit_0001"
        dirfiles = {
            os.path.join(self.demodir, name, "runtime.json"): True,
            os.path.join(self.demodir, name, "inputs.json"): False,
            os.path.join(self.demodir, name, "outputs.json"): False
        }
        parser.parse_logdir(
            logfiles=dirfiles,
            job_name="project1_dtifit",
            timestamp_key="timestamp",
            hierarchy={
                "job_name": {
                    "subjectid": {
                        "timestamp": {
                            "custom_data": None
                        }
                    }
                }
            },
            extract_keys=["subjectid"])
        tree(parser.data, level=10, display_content=True)

    @mock.patch("elasticsearch.Elasticsearch.index")
    def test_es(self, mock_es_index):
        """ Test the ElasticSearch functions.
        """
        parser = LogParser()
        parser.data.clear()
        name = "dtifit_0001"
        dirfiles = {
            os.path.join(self.demodir, name, "runtime.json"): True,
            os.path.join(self.demodir, name, "inputs.json"): False,
            os.path.join(self.demodir, name, "outputs.json"): False
        }
        parser.parse_logdir(
            logfiles=dirfiles,
            job_name="project1_dtifit",
            timestamp_key="timestamp",
            hierarchy={
                "job_name": {
                    "subjectid": {
                        "timestamp": {
                            "custom_data": None
                        }
                    }
                }
            },
            extract_keys=["subjectid"])
        dump_log_es(parser.data, "dummy", "dummy", url="dummy", port=0,
                    verbose=2)
        self.assertEqual(len(mock_es_index.call_args_list), 1)


if __name__ == "__main__":
    unittest.main()
