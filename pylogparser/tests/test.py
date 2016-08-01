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
from collections import OrderedDict
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
from pylogparser import load_log_es
from pylogparser import tree
from pylogparser import match


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

    @mock.patch("elasticsearch.client.indices.IndicesClient.put_mapping")
    @mock.patch("elasticsearch.Elasticsearch.index")
    def test_dump_es(self, mock_es_index, mock_mapping):
        """ Test the dump ElasticSearch function.
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

    @mock.patch("elasticsearch.client.indices.IndicesClient.get_aliases")
    @mock.patch("elasticsearch.Elasticsearch.search")
    def test_load_es(self, mock_es_search, mock_aliases):
        """ Test the load ElasticSearch function.
        """
        mock_es_search.return_value = {
            "took": 23,
            "timed_out": False,
            "_shards": {
                "total": 1,
                "successful": 1,
                "failed": 0
            },
            "hits": {
                "total": 1,
                "max_score": 1.0,
                "hits": [{
                    "_index": "index1",
                    "_type": "0001",
                    "_id": "1",
                    "_score": 1.0,
                    "_source": {
                        "test": "ok",
                    }
                }]
            }
        }
        mock_aliases.return_value = {"index1": None}
        data = load_log_es("dummy", "dummy", url="dummy", port=0, verbose=2)
        self.assertEqual(data["index1"]["0001"]["1"]["test"], "ok")

    @mock.patch("pylogparser.manager.load_log_es")
    def test_match_es(self, mock_load):
        """ Test the match ElasticSearch function.
        """
        input_data = OrderedDict()
        input_data["index1"] = OrderedDict()
        input_data["index1"]["0001"] = OrderedDict()
        input_data["index1"]["0001"]["1"] = OrderedDict()
        input_data["index1"]["0001"]["1"]["timestamp"] = "1"
        input_data["index1"]["0001"]["1"]["exitcode"] = "1"
        input_data["index1"]["0001"]["2"] = OrderedDict()
        input_data["index1"]["0001"]["2"]["timestamp"] = "2"
        input_data["index1"]["0001"]["2"]["exitcode"] = "0"
        input_data["index1"]["0002"] = OrderedDict()
        input_data["index1"]["0002"]["1"] = OrderedDict()
        input_data["index1"]["0002"]["1"]["timestamp"] = "3"
        input_data["index1"]["0002"]["1"]["exitcode"] = "0"
        mock_load.return_value = input_data
        data = match(match_name="exitcode", login="dummy", password="dummy",
                     url="dummy", port=0, match_value=None, index="index1",
                     doc_type=None, verbose=0)
        self.assertEqual(data["index1"]["0001"], "1")
        self.assertEqual(data["index1"]["0002"], "0")


if __name__ == "__main__":
    unittest.main()
