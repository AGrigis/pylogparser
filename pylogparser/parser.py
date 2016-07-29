##########################################################################
# pylogparser - Copyright (C) AGrigs, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System modules
from __future__ import print_function
import os
import re
import sys
import collections
import json
from pprint import pprint

# Module import
from .utils import Singleton
from .utils import with_metaclass


@with_metaclass(Singleton)
class LogParser(object):
    """ A class to parse and reorganize formatted logs.

    Attributes
    ----------
    `data`: dict {node_name: node}
        a dictionary containing the parsed log data.

    Methods
    -------
    parse_logfile
    parse_logdir
    """
    # Shared class data parameter
    data = {}

    def __init__(self):
        """ Initialize the 'LogParser' class.
        """
        pass

    @classmethod
    def load(cls, json_file, verbose=0):
        """ Load data from a Json configuration file.
        See the demonstration file for the synthax of this file. Briefly the
        same parameters as the 'parse_logfile' and 'parse_logdir' functions
        must be specified, with an extra 'type' parameters. The latter must be
        in ('logfile', 'logdir') and enables us to switch between the parsing
        methods.

        Parameters
        ----------
        json_file: str
            a Json file with the description of the data to be parsed by the
            system.
        verbose: int
            parameter to ccontrol the verbosity.

        Raises
        ------
        ValueError: if the parsing method is not recognize.
        """
        # Check the input log file exists
        if not os.path.isfile(json_file):
            raise ValueError(
                "'{0}' is not a valid description file.".format(json_file))

        # Open the description
        with open(json_file, "rt") as open_file:
            description = json.load(open_file)

        # Parse the data
        for name, log_struct in description.items():
            if verbose > 0:
                print("[info] Parsing '{0}'...".format(name))
            if verbose > 1:
                pprint(log_struct)
            ptype = log_struct.pop("type")
            if ptype == "logfile":
                cls.parse_logfile(**log_struct)
            elif ptype == "logdir":
                cls.parse_logdir(**log_struct)
            else:
                raise ValueError(
                    "Unrecognize '{0}' parsing type.".format(ptype))

    @classmethod
    def parse_logfile(cls, logfile, job_pattern, timestamp_pattern,
                      custom_patterns, hierarchy=None, jobs_alias=None):
        """ Parse a log file that is composed of multiple jobs. This log file
        is supposed to be organized, thus it is possible to grab information
        using regular expressions.

        Parameters
        ----------
        logfile : str (mandatory)
            a log file to be parsed.
        job_pattern : str (mandatory)
            the regular expression used to detect the job IDs.
        timestamp_pattern : str (mandatory)
            the regular expression used to detect the timestamps.
        custom_patterns : dict of dict (mandatory)
            a dict with custom names as keys and values that are dictionaries
            with one mandatory 'regex' item that will be used to identify some
            data of interest in the log and an optional 'splitter' item
            containing a 2-uplet of the form (splitter, position) that will be
            used to keep only a part of the matched data. If not specified
            or None, no filter is applied.
        hierarchy: dict (optional, default None)
            the parsed log final organization. If None, the job IDs ('job_id'
            key) followed by the timestamps ('timestamp' key) and finally the
            custom data ('custom_data' key).
        jobs_alias: str (optional, default None)
            if the log file concerns a single job, replace the job ID by this
            alias.
        """
        # Check the input log file exists
        if not os.path.isfile(logfile):
            raise ValueError(
                "'{0}' is not a valid log file.".format(logfile))
        if not isinstance(custom_patterns, dict):
            raise ValueError("A dictionary with 'custom_patterns' is "
                             "expected.")

        # Class parameters
        _job_pattern = re.compile(job_pattern)
        _timestamp_pattern = re.compile(timestamp_pattern)
        _custom_patterns = collections.OrderedDict(
            (name, {"regex": re.compile(value["regex"]),
                    "splitter": value.get("splitter", None)})
            for name, value in custom_patterns.items())
        if hierarchy is None:
            hierarchy = {"job_id": {"timestamp": {"custom_data": None}}}

        # Parse all the input log files
        final_struct, hierarchy_level = cls._parse(
            logfile, _job_pattern, _timestamp_pattern, _custom_patterns,
            hierarchy, jobs_alias)

        # Concatenante the new struct
        cls._concatenate(cls.data, final_struct, hierarchy_level)

    @classmethod
    def parse_logdir(cls, logfiles, job_name, timestamp_key, hierarchy=None,
                     extract_keys=None):
        """ Parse a log folder containing files describing a job. These files
        are expected in Json format containing dictionaries with meaningful
        keys.

        Parameters
        ----------
        logfiles : dict (mandatory)
            the log directory files to be parsed as keys and a boolean
            associated value specifying if the structure needs to be flatten.
            If not, the file name (without extension) is used as a key in the
            data structure.
        job_name : str (mandatory)
            the job name.
        timestamp_key : str (mandatory)
            the key used to retrieve the timestamp.
        hierarchy: dict (optional, default None)
            the parsed log final organization. If None, the job name (
            'job_name' key) followed by the timestamp ('timestamp' key) and
            finally the custom data ('custom_data' key).
        extract_keys: list of str (optiona, default None)
            a list of attributes that will be flatten even if the flatten
            key is set to False.
        """
        # Check the input log file exists
        if not isinstance(logfiles, dict):
            raise ValueError("A dictionary with 'logfiles' is expected.")
        struct = {job_name: {}}
        temporary_struct = {}
        extract_keys = extract_keys or []
        for path, to_flatten in logfiles.items():
            if not os.path.isfile(path):
                raise ValueError(
                    "'{0}' is not a valid log file.".format(path))
            with open(path, "rt") as open_file:
                data = json.load(open_file)
            if to_flatten:
                temporary_struct.update(data)
            else:
                for key, value in data.items():
                    if key in extract_keys:
                        temporary_struct[key] = value
                temporary_struct[os.path.basename(path).split(".")[0]] = data
        timestamp = temporary_struct.pop(timestamp_key)
        struct[job_name][timestamp] = temporary_struct

        # Class parameters
        if hierarchy is None:
            hierarchy = {"job_name": {"timestamp": {"custom_data": None}}}

        # Store information in requested format
        final_struct = {}
        for job_name, timestamp_struct in struct.items():
            for timestamp, data in timestamp_struct.items():
                data["job_name"] = job_name
                data["timestamp"] = timestamp
                hierarchy_level = cls._get_data(final_struct, data, hierarchy)

        # Concatenante the new struct
        cls._concatenate(cls.data, final_struct, hierarchy_level)

    @classmethod
    def _parse(cls, logfile, job_pattern, timestamp_pattern, custom_patterns,
               hierarchy=None, jobs_alias=None):
        """ Parse a log file.

        Parameters
        ----------
        logfile : str (mandatory)
            the path to the log file that will be parsed.
        job_pattern : str (mandatory)
            the regular expression used to detect the job IDs.
        timestamp_pattern : str (mandatory)
            the regular expression used to detect the timestamps.
        custom_patterns : dict of dict (mandatory)
            a dict with custom names as keys and values that are dictionaries
            with one mandatory 'regex' item that will be used to identify some
            data of interest in the log and an optional 'splitter' item
            containing a 2-uplet of the form (splitter, position) that will be
            used to keep only a part of the matched data. If not specified
            or None, no filter is applied.
        hierarchy: dict (optional, default None)
            the parsed log final organization. If None, the job IDs ('job_id'
            key) followed by the timestamps ('timestamp' key) and finally the
            custom data ('custom_data' key).
        jobs_alias: str (optional, default None)
            if the log file concerns a single job, replace the job ID by this
            alias.

        Returns
        -------
        final_struct : dict of dict of dict
            the reorganized log:
                * the first keys are the job ids.
                * the second keys are the processings timestamps.
                * the last dict contains the requested information.
        hierarchy_level: int (optional, defaul 0)
            the hierarchy level, ie. number of dictionaries.

        Raises
        ------
        ValueError: if multiple matches are found for a pattern or
                    if multiple patterns are detected in the same row or
                    if the timestamp or the job id can't be retrieved in a
                    row with a match or
                    if the log is currupted.
        """
        # Parse the log file
        with open(logfile, "rt") as open_file:
            lines = open_file.readlines()

        # Go through each line in the log file, detect requested patterns, and
        # fill the returned structure
        all_patterns = [job_pattern, timestamp_pattern]
        for name, struct in custom_patterns.items():
            all_patterns.append(struct["regex"])
        struct = {}
        for index, row in enumerate(lines):

            # Detect matches
            all_matches = {}
            for cnt, pattern in enumerate(all_patterns):
                matches = pattern.findall(row)
                if len(matches) == 0:
                    continue
                elif len(matches) > 1:
                    raise ValueError("Multiple matches found for pattern "
                                     "'{0}' on log file '{1}' line {2}: "
                                     "'{3}'.".format(pattern.pattern, logfile,
                                                     index, row))
                if cnt > 1 and len(all_matches) < 2:
                    raise ValueError("Can't detect timestamp or job id from "
                                     "patterns '{0}', '{1}' on log file '{2}' "
                                     "line {3}: '{4}'.".format(
                                         timestamp_pattern.pattern,
                                         job_pattern.pattern,
                                         logfile, index, row))
                if cnt > 1 and len(all_matches) > 2:
                    raise ValueError(
                        "Multiple matches found for patterns '{0}' on log "
                        "file '{1}' line {2}: '{3}'.".format(
                            [p.pattern for p in custom_patterns],
                            logfile, index, row))
                all_matches[str(cnt)] = matches[0]

            # Organize matches
            if len(all_matches) == 3:

                # > get information
                job_id = all_matches.pop("0")
                timestamp = all_matches.pop("1")
                custom_index, custom_data = list(all_matches.items())[0]
                name = list(custom_patterns.keys())[int(custom_index) - 2]
                if custom_patterns[name]["splitter"] is not None:
                    splitter, pos = custom_patterns[name]["splitter"]
                    custom_data = custom_data.split(splitter)[pos]

                # > store information
                struct.setdefault(job_id, {}).setdefault(timestamp, {})
                if name in struct[job_id][timestamp]:
                    raise ValueError("The triplet '{0}-{1}-{2}' has been "
                                     "detected multiple times in log file "
                                     "'{3}'. The log file might be "
                                     "corrupted.".format(job_id, timestamp,
                                                         name, logfile))
                struct[job_id][timestamp][name] = custom_data

        # Store information in requested format
        final_struct = {}
        for job_id, timestamp_struct in struct.items():
            if jobs_alias is not None:
                job_id = jobs_alias
            for timestamp, data in timestamp_struct.items():
                data["job_id"] = job_id
                data["timestamp"] = timestamp
                hierarchy_level = cls._get_data(final_struct, data, hierarchy)

        return final_struct, hierarchy_level

    @classmethod
    def _get_data(cls, struct, data, hierarchy, hierarchy_level=0):
        """ Organize some unstructured data.

        Parameters
        ----------
        struct: dict (mandatory)
            the final structure that is modified in place.
        data: dict (mandatory)
            unstructured data.
        hierarchy: dict (mandatory)
            the parsed log final organization. Keys must be in the data
            structure.
        hierarchy_level: int (optional, defaul 0)
            the hierarchy level, ie. number of dictionaries.

        Returns
        -------
        hierarchy_level: int (optional, defaul 0)
            the hierarchy level, ie. number of dictionaries.

        Raises
        ------
        ValueError: if leaf structure is not empty in order to avoid data
                    overwriting.
                    if the hierarchy format is not supported.
        """
        hierarchy_level += 1
        for key, value in hierarchy.items():
            if value is None:
                if struct != {}:
                    raise ValueError("Can't process data without lose.")
                struct.update(data)
            elif isinstance(value, dict):
                inner_value = data.pop(key)
                if inner_value not in struct:
                    struct[inner_value] = {}
                hierarchy_level = cls._get_data(
                    struct[inner_value], data, value, hierarchy_level)
            else:
                raise ValueError(
                    "'{0}' hierarchy format not supported.".format(hierarchy))
        return hierarchy_level

    @classmethod
    def _concatenate(cls, data, new_data, hierarchy_level, current_level=0):
        """ Concatenate a the class dataset with a new dataset.

        Parameters
        ----------
        data: dict (mandatory)
            the class dataset.
        new_data: dict (mandatory)
            a new dataset to be concatenated without lose.
        hierarchy_level: int (mandatory)
            the hierarchy level, ie. number of dictionaries.
        current_level: int (optional, default 0)
            the current hierarchy level.

        Raises
        ------
        ValueError: if leaf structure is not empty in order to avoid data
                    overwriting.
        """
        current_level += 1
        for key, value in new_data.items():
            if current_level < (hierarchy_level - 1):
                if key not in data:
                    data[key] = {}
                cls._concatenate(data[key], value, hierarchy_level,
                                 current_level)
            else:
                if key not in data:
                    data[key] = {}
                elif data[key] != {}:
                    raise ValueError("Can't process data without lose.")
                data[key].update(value)
