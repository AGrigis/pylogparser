##########################################################################
# pylogparser - Copyright (C) AGrigs, 2016
# Distributed under the terms of the CeCILL-B license, as published by
# the CEA-CNRS-INRIA. Refer to the LICENSE file or to
# http://www.cecill.info/licences/Licence_CeCILL-B_V1-en.html
# for details.
##########################################################################

# System import
from __future__ import print_function
from elasticsearch import Elasticsearch


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

    # Parse and save log data
    for index, index_struct in data.items():
        for dtype, dtype_struct in index_struct.items():
            for timestamp, sdata in dtype_struct.items():
                if verbose > 1:
                    print("[info] Inserting '{0}-{1}-{2}' in ES.".format(
                        index, dtype, timestamp))
                result = es.index(index=index, doc_type=dtype, id=timestamp,
                                  body=sdata)
                if verbose > 0 and not result["created"]:
                    print(
                        "[warn] '{0}-{1}-{2}' ES path already exists.".format(
                            index, dtype, timestamp))


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

    # Get all data
    data = {}
    for index in es.indices.get_aliases().keys():
        result = es.search(index=index, body={"query": {"match_all": {}}})
        if verbose > 1:
            print("[info] '{0} hits found.".format(result["hits"]["total"]))
        for hit in result["hits"]["hits"]:
            _data = data
            for key in (hit["_index"], hit["_type"], hit["_id"]):
                if key not in _data:
                    _data[key] = {}
                _data = _data[key]
            _data.update(hit["_source"])

    return data
