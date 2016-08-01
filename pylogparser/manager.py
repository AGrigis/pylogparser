##########################################################################
# pylogparser - Copyright (C) AGrigs, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
from pprint import pprint
from collections import OrderedDict
from elasticsearch import Elasticsearch
from dateutil import parser

# Pylogparser imports.
from pylogparser import tree


def match(match_name, login, password, url="localhost", port=9200,
          match_value=None, index=None, doc_type=None, verbose=0):
    """ Match the first occurence of an element in ElasticSearch (ES).

    Parameters
    ----------
    match_name: str (mandatory)
        the element name to be matched.
    login: str (mandatory)
        the login used to contact ES.
    password: str (mandatory)
        the password used to contact ES.
    url: str (optional, default 'localhost')
        the ES URL.
    port: int (optional, default 9200)
        the port ES is listen to.
    match_value: object (optional, default None)
        the element value to be matched.
    index: str (optional, default None)
        an ES index.
    doc_type: str (optional, default None)
        an ES type.
    verbose: int (optional, default 0)
        the verbosity level.

    Return
    ------
    matches: dict
        the requested matches.
    """
    # Get all the data
    data = load_log_es(login, password, url=url, port=port, verbose=verbose)
    if index is not None:
        if doc_type is not None:
            data = {index: {doc_type: data[index][doc_type]}}
        else:
            data = {index: data[index]}
    if verbose > 1:
        print("Data...")
        tree(data, level=2, display_content=False)

    # Get all matches
    matches = {}
    for index, index_struct in data.items():
        for doc_type, doc_type_struct in index_struct.items():
            for timestamp, record in doc_type_struct.items():
                value = record.get(match_name, None)
                if match_value is not None and value != match_value:
                    continue
                if index not in matches:
                    matches[index] = {}
                if doc_type not in matches[index]:
                    matches[index][doc_type] = value
                break
    if verbose > 0:
        print("Matches for '{0}={1}'...".format(match_name, match_value))
        pprint(matches)

    return matches


def dump_log_es(data, login, password, url="localhost", port=9200,
                verbose=0):
    """ Dump log data in an elesticsearch (ES) database.

    Parameters
    ----------
    data: dict (mandatory)
        a dictionary containing the parsed log data.
    login: str (mandatory)
        the login used to contact ES.
    password: str (mandatory)
        the password used to contact ES.
    url: str (optional, default 'localhost')
        the ES URL.
    port: int (optional, default 9200)
        the port ES is listen to.
    verbose: int (optional, default 0)
        control the verbosity level.
    """
    # Create a connection
    es = Elasticsearch([url], http_auth=(login, password), port=port)

    # Define a mapping
    mapping = {
        "properties": {
            "timestamp": {
                "type": "date"
            }
        }
    }

    # Parse and save log data
    for index, index_struct in data.items():
        for dtype, dtype_struct in index_struct.items():
            for timestamp, sdata in dtype_struct.items():
                if verbose > 1:
                    print("[info] Inserting '{0}-{1}-{2}' in ES.".format(
                        index, dtype, timestamp))
                date = parser.parse(timestamp)
                timestamp = date.isoformat()
                sdata["timestamp"] = timestamp
                result = es.index(index=index, doc_type=dtype, id=timestamp,
                                  body=sdata)
                if verbose > 0 and not result["created"]:
                    print(
                        "[warn] '{0}-{1}-{2}' ES path already exists.".format(
                            index, dtype, timestamp))
            es.indices.put_mapping(dtype, mapping, [index])


def load_log_es(login, password, url="localhost", port=9200, verbose=0):
    """ Load all the data of an elasticsearch (ES) database.

    Parameters
    ----------
    login: str (mandatory)
        the login used to contact ES.
    password: str (mandatory)
        the password used to contact ES.
    url: str (optional, default 'localhost')
        the ES URL.
    port: int (optional, default 9200)
        the port ES is listen to.
    verbose: int (optional, default 0)
        control the verbosity level.

    Returns
    -------
    data: dict
        a dictionary containing the ES log data.
    """
    # Create a connection
    es = Elasticsearch([url], http_auth=(login, password), port=port)

    # Define the query
    query = {
        "query": {
            "match_all": {}
        },
        "sort": [{
            "timestamp": {
                "order": "desc",
            }
        }]
    }

    # Get all data
    data = OrderedDict()
    for index in es.indices.get_aliases().keys():
        result = es.search(index=index, body=query)
        if verbose > 1:
            print("[info] '{0} hits found.".format(result["hits"]["total"]))
        for hit in result["hits"]["hits"]:
            _data = data
            for key in (hit["_index"], hit["_type"], hit["_id"]):
                if key not in _data:
                    _data[key] = OrderedDict()
                _data = _data[key]
            _data.update(hit["_source"])

    return data
