##########################################################################
# pylogparser - Copyright (C) AGrigs, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

"""
System imports.
"""
from __future__ import print_function
import os
import tempfile

"""
Pylogparser imports.
"""
import pylogparser
from pylogparser import LogParser
from pylogparser import dump_log_es
from pylogparser import load_log_es
from pylogparser import tree
from pylogparser import match

"""
First we define where to find the demonstration data.
"""
demodir = os.path.abspath(os.path.join(os.path.dirname(pylogparser.__file__),
                          "demo"))

"""
We create a log parser. All the parser data will be stored in the 'data'
instance parameter.
"""
parser = LogParser()

"""
We examplify here the parser object singleton property .
"""
print(parser)
for i in range(3):
    p = LogParser()
    print(p)

"""
We parse data from log files containing multiple processings of the same type.
"""
for basename in ("fsreconall_1.txt", "fsreconall_2.txt"):
    logfile = os.path.join(demodir, basename)
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
    print("-------", basename)
    tree(parser.data, level=2, display_content=False)
"""
We obtain 3 FreeSurfer records from 'fsreconall_1.txt':

------- fsreconall_1.txt
 +-project1_freesurfer
 | +-0001
 | | +-2015-11-10T01:33
 | +-0002
 | | +-2015-11-10T01:35
 | +-0003
 | | +-2015-11-10T01:38

And 1 more from 'fsreconall_2.txt':

------- fsreconall_2.txt
 +-project1_freesurfer
 | +-0001
 | | +-2015-11-10T01:33
 | +-0002
 | | +-2015-11-10T01:35
 | +-0003
 | | +-2015-12-03T17:04
 | | +-2015-11-10T01:38

"""

"""
We now parse JSON struct generated from two processings.
"""
for name in ("dtifit_0001", "dtifit_0002"):
    dirfiles = {
        os.path.join(demodir, name, "runtime.json"): True,
        os.path.join(demodir, name, "inputs.json"): False,
        os.path.join(demodir, name, "outputs.json"): False
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
    print("-------", name)
    tree(parser.data, level=2, display_content=False)
"""
We obtain 2 DTIFit extra records:

------- dtifit_0001
 +-project1_dtifit
 | +-0001
 | | +-2016-07-13T09:20:00.007074
 +-project1_freesurfer
 | +-0001
 | | +-2015-11-10T01:33
 | +-0002
 | | +-2015-11-10T01:35
 | +-0003
 | | +-2015-12-03T17:04
 | | +-2015-11-10T01:38

------- dtifit_0002
 +-project1_dtifit
 | +-0001
 | | +-2016-07-13T09:20:00.007074
 | +-0002
 | | +-2016-07-13T09:16:32.993929
 +-project1_freesurfer
 | +-0001
 | | +-2015-11-10T01:33
 | +-0002
 | | +-2015-11-10T01:35
 | +-0003
 | | +-2015-12-03T17:04
 | | +-2015-11-10T01:38
"""

"""
We show how to organize the presneted parsing in a single Json configuration
file.
"""
descfile = os.path.join(demodir, "pylogparser_demo.json")
modify_descfile = tempfile.NamedTemporaryFile(suffix=".json").name
with open(descfile, "rt") as open_file:
    jbuffer = open_file.read().replace("DEMODIR", demodir)
with open(modify_descfile, "wt") as open_file:
    open_file.write(jbuffer)
LogParser.load(modify_descfile, verbose=0)
print("------- load 'project2' from description")
tree(parser.data, level=2, display_content=False)
"""
The same data are parsed and associated to 'project2':

------- load 'project2' from description
 +-project1_dtifit
 | +-0001
 | | +-2016-07-13T09:20:00.007074
 | +-0002
 | | +-2016-07-13T09:16:32.993929
 +-project2_dtifit
 | +-0001
 | | +-2016-07-13T09:20:00.007074
 | +-0002
 | | +-2016-07-13T09:16:32.993929
 +-project2_freesurfer
 | +-0001
 | | +-2015-11-10T01:33
 | +-0002
 | | +-2015-11-10T01:35
 | +-0003
 | | +-2015-12-03T17:04
 | | +-2015-11-10T01:38
 +-project1_freesurfer
 | +-0001
 | | +-2015-11-10T01:33
 | +-0002
 | | +-2015-11-10T01:35
 | +-0003
 | | +-2015-12-03T17:04
 | | +-2015-11-10T01:38
"""

"""
We now interact with ElasticSearch and save the log parsed data.
"""
print("------- save data in elasticsearch")
dump_log_es(parser.data, "boss", "alpine", url="localhost", port=9200,
            verbose=2)

"""
We now dump all the saved datain elasticsearch and check everything is all
right.
"""
data = load_log_es("boss", "alpine", url="localhost", port=9200, verbose=1)
print("------- load data from elasticsearch")
tree(parser.data, level=2, display_content=False)
record1 = data["project1_dtifit"]["0001"]["2016-07-13T09:20:00.007074"]
record2 = parser.data["project1_dtifit"]["0001"]["2016-07-13T09:20:00.007074"]
assert record1 == record2

"""
All right, now search all jobs final status.
"""
print("------- check status")
status = match(
    match_name="exitcode", match_value=None, login="boss", password="alpine",
    url="localhost", port=9200, index=None, doc_type=None, verbose=1)
"""
------- check status
Matches for 'exitcode=None'...
{u'project1_dtifit': {u'0001': None, u'0002': None},
 u'project1_freesurfer': {u'0001': u'0', u'0002': u'0', u'0003': u'0'},
 u'project2_dtifit': {u'0001': None, u'0002': None},
 u'project2_freesurfer': {u'0001': u'0', u'0002': u'0', u'0003': u'0'}}
"""

"""
Focus now on a specific processing.
"""
print("------- check status of one processing")
status = match(
    match_name="exitcode", match_value=None, login="boss", password="alpine",
    url="localhost", port=9200, index="project1_freesurfer", doc_type=None,
    verbose=1)
"""
------- check status of one processing
Matches for 'exitcode=None'...
{'project1_freesurfer': {u'0001': u'0', u'0002': u'0', u'0003': u'0'}}

"""

"""
Finally search where an error occured during processings.
"""
print("------- check errors")
status = match(
    match_name="exitcode", match_value="1", login="boss", password="alpine",
    url="localhost", port=9200, index=None, doc_type=None, verbose=1)
"""
------- check errors
Matches for 'exitcode=1'...
{u'project1_freesurfer': {u'0003': u'1'},
 u'project2_freesurfer': {u'0003': u'1'}}
"""
