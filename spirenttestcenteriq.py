#!/usr/bin/env python
"""Provides a Python front-end for the Spirent TestCenter IQ ReST API.
    
"""

import sys
import os.path
import time
import datetime
import pkg_resources
import json
import re
import copy
import csv
import dateutil.parser
from distutils.version import LooseVersion

import requests

import pprint

__author__ = "Matthew Jefferson"
__copyright__ = "Copyright 2019, Spirent Communications"
__credits__ = ["Matthew Jefferson"]
__version__ = "0.0.1"
__maintainer__ = "Matthew Jefferson"
__email__ = "matt.jefferson@spirent.com"

# "Prototype", "Development", or "Production"
__status__ = "Prototype"

def timeit(method):
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            print('%r  %2.2f ms' % \
                  (method.__name__, (te - ts) * 1000))
        return result
    return timed

# Copyright Ferry Boender, released under the MIT license.
def deepupdate(target, src):
    """Deep update target dict with src
    For each k,v in src: if k doesn't exist in target, it is deep copied from
    src to target. Otherwise, if v is a list, target[k] is extended with
    src[k]. If v is a set, target[k] is updated with v, If v is a dict,
    recursively deep-update it.

    Examples:
    >>> t = {'name': 'Ferry', 'hobbies': ['programming', 'sci-fi']}
    >>> deepupdate(t, {'hobbies': ['gaming']})
    >>> print t
    {'name': 'Ferry', 'hobbies': ['programming', 'sci-fi', 'gaming']}
    """
    for k, v in src.items():
        if type(v) == list:
            if not k in target:
                target[k] = copy.deepcopy(v)
            else:
                target[k].extend(v)
        elif type(v) == dict:
            if not k in target:
                target[k] = copy.deepcopy(v)
            else:
                deepupdate(target[k], v)
        elif type(v) == set:
            if not k in target:
                target[k] = v.copy()
            else:
                target[k].update(v.copy())
        else:
            target[k] = copy.copy(v)
        
class SpirentTestCenterIQ:
    def __init__(self, iq_server_ip=None, iq_server_port=9199, verbose=False, log_path=None, log_level="INFO", query_definitions_file=None, stc_api_instance=None):

        self.query_definitions = {}        

        if iq_server_ip:
            self.spirent_iq_rest_api_url = "http://" + iq_server_ip + ":" + str(iq_server_port)

        self.module_path = os.path.dirname(os.path.abspath(__file__))            

        if not query_definitions_file:
            query_definitions_file = os.path.join(self.module_path, "spirent_iq_query_definitions.json")

        if os.path.isfile(query_definitions_file):
            self.__load_json_from_file(query_definitions_file)

        self.stc = stc_api_instance        

        self.subscribe()

        self.db_list = []
        self.refresh_database_list()

        self.set_current_db()

        return

    def subscribe(self, retention_duration=15, subscribe_type="ALL", config_subscribe_type="ALL"):
        """If the Spirent TestCenter API is loaded, this will enable the IQ results.

        Parameters
        ----------
        retention_duration: int
            The number of minutes worth of data that is retained in the database.

        subscribe_type: str
            Use this argument to control which statistics are stored in the database.

        config_subscribe_type: str
            Use this argument to control what configuration information is stored in the database.

        """
        erp = None

        if self.stc:
            erp = stc.get("system1", "children-spirent.results.EnhancedResultsSelectorProfile")
            if erp == "":        
                # This is required in order to enable the enhanced results.
                # If you don't set the SubscribeType to "ALL", then you must create some EnhancedResultsGroupFilter objects 
                # for the results you want to have collected.
                erp = stc.create("spirent.results.EnhancedResultsSelectorProfile", under="system1", 
                                                                                   SubscribeType=subscribe_type,
                                                                                   ConfigSubscribeType=config_subscribe_type,
                                                                                   EnableLiveDataRetention=True,
                                                                                   LiveDataRetentionInterval=retention_duration)

        return erp

    def get_result_url(self):
        """Get the URL of the ReST server URL of the Spirent IQ results API.

        Returns
        -------
        str
            Returns the URL of the ReST API.
        """ 

        if not self.spirent_iq_rest_api_url:
            self.spirent_iq_rest_api_url = stc.get("system1.TemevaResultsConfig", "ServiceUrl")

        return(self.spirent_iq_rest_api_url)        

    def execute_query(self, query, mode="once", db_id=None):
        """Returns the raw results based on the specified query.

        You may pass the query from the Spirent TestCenter IQ GUI into this method.
        You can find the query in the IQ GUI by selecting the three lines at the top of the 
        desired results view, and then selecting "View Query".

        Parameters
        ----------
        query: dict
            The Spirent IQ query to execute.

        mode: set
            Not entirely sure what this does. :-)

        db_id: str
            The database ID that the query will be executed against. The current DB ID will
            be used if one is not specified.

        Returns
        -------
        dict
            Dictionary containing the raw results for the query.

        """
        
        full_query = {}

        full_query["database"] = {}
        if db_id is None:
            full_query["database"]["id"] = self.get_session_db_id()
        else:
            full_query["database"]["id"] = db_id
        
        full_query["mode"] = mode
        full_query["definition"] = query

        response = self.__execute("post", "queries", full_query)

        return(response)        

    def execute_view_query(self, view_name, db_id=None):        
        """Returns results based on the specified pre-defined query.

        By default, queries are located in a JSON file, loaded when this class is instantiated.        
        
        Parameters
        ----------
        view_name: str
            The name of the pre-defined query. These queries are stored in the file self.query_definitions_file.

        db_id: str
            The database ID that the query will be executed against. The current DB ID will
            be used if one is not specified.

        Returns
        -------
        dict
            Dictionary containing the results for the query.

        """        
        if db_id is None:
            db_id = self.get_session_db_id()          

        response = None
        if view_name in self.query_definitions.keys():
            query = self.query_definitions[view_name]
            response = self.execute_query(query, db_id=db_id)            
        else:
            print("ERROR: The view '" + view_name + "' is not defined. Please use one of the following views:")
            for view in self.query_definitions.keys():
                print("  " + view)

        return response

    def refresh_database_list(self):

        for db in self.db_list:
            del db

        self.db_list = []

        all_db_info = self.get_all_db_info(summary=True)

        for db_info in all_db_info:
            if "application.name" in db_info["metadata"].keys() and db_info["metadata"]["application.name"] == "TestCenter":
                db = IqDatabase(self, db_info["id"])
                self.db_list.append(db)

        return

    def get_session_db_id(self):
        """Returns the Spirent IQ results database ID for the current session (if there is one).

        This only works if the Spirent TestCenter API is loaded, and the STC API class is pointed to by "stc".

        Returns
        -------
        str
            Results database ID.

        """    

        db_id = None

        try:
            db_id = self.stc.get("system1.project.testinfo", "ResultDbId") 
        except:
            pass

        return db_id

    def set_current_db(self, name=None, db_id=None):
        """Set the current database to the database specified by name or DB ID. 
        If neither the or db_id are specified, the method will attempt to query
        the Spirent TestCenter API (if loaded) for the current database.

        Parameters
        ----------
        name: str
            The name of the database.

        db_id: str
            The database ID to be used.

        Returns
        -------
        class
            The database object being used.

        """

        self.current_db = None

        if db_id is None and name is None:
            db_id = self.get_session_db_id()
            self.current_db = self.find_db_by_id(id=db_id)
        elif db_id:
            self.current_db = self.find_db_by_id(id=db_id)
        elif name:
            self.current_db = self.find_db_by_name(name)
        
        return self.current_db

    def find_db_by_id(self, id=None):
        """Returns the database object that matches the specified database ID.

        Parameters
        ----------
        id: str
            The database ID of the desired database.

        name: str
            The name of the desired database.

        Returns
        -------
        class
            Database object that matches the name. None otherwise.

        """
        for db in self.db_list:
            if id and id == db.id:
                return db

        return None

    def find_db_by_name(self, name=None):
        """Returns the latest database object that matches the specified name.

        WARNING: The current implemenation is probably incorrect. The last_updated
                 information needs to be updated each time if this method is 
                 going be accurate.

        Parameters
        ----------
        id: str
            The database ID of the desired database.

        name: str
            The name of the desired database.

        Returns
        -------
        class
            Database that matches the name. None otherwise.

        """
        current_db = None
        db_timestamp = None

        for db in self.db_list:
            if db.name == name:

                new_db_timestamp = dateutil.parser.parse(db.last_updated)

                if not db_timestamp:
                    db_timestamp = new_db_timestamp
                    current_db = db
                elif db_timestamp < new_db_timestamp:
                    db_timestamp = new_db_timestamp
                    current_db = db

        return current_db

    def get_all_db_info(self, summary=False):
        """Returns information about the Spirent IQ results databases.
        
        Parameters
        ----------
        summary: bool
            If True, returns only a summary. Otherwise, all of the database information is returned.
            Also, the information cached this class is updated when set to False.

        name: str
            Return only the DB's that match this name (overridden by db_id).

        Returns
        -------
        list
            A list of dicts containing the information on the database(s).

        """    

        if summary:
            result_db_list = self.__execute("get", "databases?detail=summary")
        else:
            result_db_list = self.__execute("get", "databases")

        return(result_db_list) 

    def get_db_info(self, db_id=None, summary=True):
        """Returns information about the specified Spirent IQ results databases.
        
        Parameters
        ----------
        db_id: str
            The database ID to be used. If None, the current DB ID will be used.

        summary: bool
            If True, returns only a summary. Otherwise, all of the database information is returned.

        Returns
        -------
        dict
            A dict containing the information on the specified database.
        

        Each entry contains the following when using summary=True:

        "id": "l5ixqul3p5axfgzq",
        "datastore": {
            "id": "default",
            "provider": "postgres",
            "version": "PostgreSQL 10.10 (Debian 10.10-1.pgdg80+1) on x86_64-pc-linux-gnu, compiled by gcc (Debian 4.9.2-10+deb8u2) 4.9.2, 64-bit",
            "capabilities": [
                "has_single_result_query_type",
                "has_storage_information",
                "has_delete_result_query_type",
                "has_raw_query_type",
                "has_cost_query_mode",
                "has_single_dimension_query_type",
                "has_inet_field_data_type",
                "has_multi_result_query_type",
                "has_last_materialized_view"
            ]
        },
        "name": "api testing",
        "description": "",
        "metadata": {
            "application.id": "e8c43606b3924efbaa86f82bc47dd279",
            "application.name": "TestCenter",
            "application.version": "5.03.8466.0000",
            "test.configuration.name": "\\\\vmware-host\\Shared Folders\\Projects\\SpirentTestCenterIQ\\test",
            "test.duration_sec": "366",
            "test.dut.details": "[]",
            "test.iterative": "false",
            "test.owner": "MJefferson",
            "test.running": "false",
            "test.started": "2019-12-11T01:58:34Z",
            "test.type.tags": "traffic",
            "test.user.tags": ""
        },
        "first_created": "2019-12-11T01:58:34.870653Z",
        "last_updated": "2019-12-11T08:09:16.662384Z",
        "dimension_sets": [],
        "result_sets": [],
        "profile": {
            "id": "abec5249e4a4405c812f785d10fdec14",
            "serial": 0,
            "name": "",
            "description": "",
            "metadata": null,
            "details": null,
            "views": []
        },
        "summary": {
            "count": 5454,
            "value_storage_kb": 3544,
            "index_storage_kb": 6200
        }                    

        """    

        if not db_id:
            db_id = self.get_session_db_id()
    
        if summary:
            db_info = self.__execute("get", "databases/" + db_id + "?detail=summary")
        else:
            db_info = self.__execute("get", "databases/" + db_id)

        return(db_info) 

    #==============================================================================
    def convert_result_to_dict(self, raw_data, key_names=None):
        """Convert the raw result, returned from the API, into a proper dictionary.
        If the key_name is not specified, then the key will be the row index (starting
        at 1).

        Parameters
        ----------    
        raw_data: dict
            The result dict returned by the Spirent IQ ReST API.

        key_names: list
            A list of column names to use as the keys for the returned dictionary.
            A simple integer is used if not specified.

        Returns
        -------
        dict
            The results, stored with the specified key values.

        """        

        if key_names:
            for key in key_names:
                if key not in raw_data["result"]["columns"]:
                    raise KeyError("The key '" + key + "' is not a valid value.")

        row_index = 0
        result_dict = {}
        if "rows" in raw_data["result"] and raw_data["result"]["rows"]:
            for row in raw_data["result"]["rows"]:
                entry = {}
                column_index = 0
                for column in raw_data["result"]["columns"]:
                    entry[column] = row[column_index]
                    column_index += 1                    
                
                if key_names:
                    # The user has specified which keys they want to use for the resulting dictionary.
                    # Construct the dictionary with the specified keys, and add the data for this row.
                    new_dict = current = {}
                    for key in key_names:
                        new_dict = current = {}
                        for name in key_names:
                            key_value = entry[name]
                            current[key_value] = {}
                            if name == key_names[-1]:
                                current[key_value] = entry
                            current = current[key_value]

                    # Merge the new_dict into result_dict.
                    deepupdate(result_dict, new_dict)
                else:
                    row_index += 1
                    result_dict[row_index] = entry

        return result_dict

    #==============================================================================
    def convert_result_to_csv(self, raw_data, filename="results.csv"):
        """Convert the raw result, returned from the API, into a CSV file.

        Parameters
        ----------    
        raw_data: dict
            The result dict returned by the Spirent IQ ReST API.

        filename: str
            The name of the file to store the results CSV.

        """  

        with open(filename, mode='w') as result_file:
            result_writer = csv.writer(result_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

            result_writer.writerow(raw_data["result"]["columns"])

            if "rows" in raw_data["result"] and raw_data["result"]["rows"]:
                for row in raw_data["result"]["rows"]:
                    result_writer.writerow(row)        

        return

    #==============================================================================
    def from_iso_format(self, timestamp):
        # Return a date corresponding to a date_string given in the format YYYY-MM-DDTHH:MM:SS.UUUUUUZ.
        # NOTE: This method is natively available in Python 3.7 and later.
        return datetime.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%fZ")

    #==============================================================================
    def iso_format(self, timestamp):
        # Return a string representing the date in ISO 8601 format YYYY-MM-DDTHH:MM:SS.UUUUUUZ.
        # NOTE: This method is natively available in Python 3.7 and later.
        return timestamp.strftime("%Y-%m-%dT%H:%M:%S.%fZ")        

    #==============================================================================
    def __execute(self, cmdtype, url, payload=None):
        """Construct the URL...
        Be sure to escape all invalid characters first.        
        """

        #url = requests.utils.quote(url)
        url = "".join(self.get_result_url() + "/" + url)

        # Send the command to the REST server.
        if cmdtype.lower() == "get":
            #response = requests.get(url, headers={"X-STC-API-Session": self.sessionid})
            #response = requests.get(get_result_url(), headers=get_header(), json=query_data)
            response = requests.get(url)
        elif cmdtype.lower() == "put":
            response = requests.put(url)
        elif cmdtype.lower() == "post":
            response = requests.post(url, json=payload)
        elif cmdtype.lower() == "delete":
            response = requests.delete(url)
        elif cmdtype.lower() == "head":
            response = requests.head(url)    

        # Check for exceptions.
        # We want to only raise the BLL-related exceptions, not the HTTP exception that 
        # is generated by the "requests" module.
        try:
            response.raise_for_status()
        except:
            try:    
                responsedata = self.__extract_json(response)

                #raise RuntimeError(responsedata['message']) from None
                raise RuntimeError(responsedata['message'])
            except:
                pass

        return(self.__extract_json(response))                

        # Some valid responses do not have a JSON response (like the HEAD command).
        try:
            # Try to return the JSON response.
            return(self.__extract_json(response))
        except:
            # The response was not JSON. Just return the HTTP status code.
            return(response.status_code)    

    def __extract_json(self, response):
        # Apparently there is a difference between the json commands for Python 2.6 and 2.7+.
        # Use this function to take care of the difference.

        version = pkg_resources.get_distribution("requests").version

        if LooseVersion(version) < LooseVersion("1.0"):
            result = response.json
        else:
            result = response.json()

        return(result)                
    
    def __load_json_from_file(self, input_filename):        

        # Open and read the JSON input file.        

        if input_filename:
            try:
                with open(input_filename) as json_file:
                    self.query_definitions = json.load(json_file)
            except:
                errmsg = "Unexpected error while parsing the JSON definition file:" + sys.exc_info()[1]
                print("ERROR: " + errmsg)
                raise Exception(errmsg)

        return 

#========================================================================================================
class IqDatabase:
    def __init__(self, iq, db_id):
        self.iq = iq
        self.db_id = db_id

        # This refers to the profile used by the UI when opening the database.
        self.profile_id = None

        self.refresh()

        return

    def refresh(self):
        # Populate all of the database information for the IQ server.
        db_info = self.iq.get_db_info(db_id=self.db_id, summary=False)
        
        self.info = db_info
        
        self.id = db_info["id"]
        self.name = db_info["name"]
        self.first_create = db_info["first_created"]
        self.last_updated = db_info["last_updated"]
        self.running = db_info["metadata"].get("test.running", False)

        self.set_list = []
        self.result_set_list = []
        self.dimension_set_list = []
        self.refresh_set_list()

        return

    def refresh_set_list(self):
        for iq_set in self.result_set_list + self.dimension_set_list:
            del iq_set

        for result_set_info in self.info["result_sets"]:
            result_set = IqResultSet(self, self.iq, result_set_info)
            self.result_set_list.append(result_set)

        for dimension_set_info in self.info["dimension_sets"]:
            dimension_set = IqDimensionSet(self, self.iq, dimension_set_info)            
            self.dimension_set_list.append(dimension_set)

        self.set_list = self.result_set_list + self.dimension_set_list

        for iq_set in self.set_list:
            iq_set.refresh_related_set_info()

        return

    def get_snapshot_list(self, order="ASC"):
        """Returns the names of all saved snapshots for the specified results DB.        

        Parameters
        ----------    
        order: str
            ASC for ascending, and DESC for descending.

        Returns
        -------
        list
            A list of all snapshot names for the specified database.

        """

        query = {}
        
        query["filters"] = []
        query["groups"] = []
        query["orders"] = ["view.test_event_timestamp " + order]        
        query["projections"] = [
            "view.test_snapshot_name as snapshot_name",
            "view.test_snapshot_number as snapshot_number"
        ]

        query["subqueries"] = [
             {
               "alias": "view",
               "filters": [
                 "test_events.name = 'snapshot_completed'"
               ],
               "groups": [],
               "orders": [],
               "projections": [
                  "test.snapshot_name as test_snapshot_name",
                  "test.snapshot_number as test_snapshot_number",
                  "test_events.name as test_event_name",
                  "test_events.timestamp as test_event_timestamp",
               ],
             }
          ]

        mrquery = {"multi_result": query}
        result = self.iq.execute_query(mrquery, db_id=self.id)

        snapshots = []
        for snapshot in result["result"]["rows"]:
            snapshots.append(snapshot[0])

        return snapshots

    def find_set_by_name(self, name):        
        for iq_set in self.set_list:
            if iq_set.name == name:
                return iq_set
        return None

    def get_db_url(self):
        url = "".join(self.iq.get_result_url() + "/results/" + self.db_id)
        if self.profile_id:
            url += "?profileId=" + self.profile_id

        return url

    def set_profile_id(self, profile_id):
        """Sets the profile that is used by the get_db_url() method.
        """
        self.profile_id = profile_id

        return

#========================================================================================================
class IqSet:
    def __init__(self, db, iq, set_info):
        self.set_info = set_info

        self.name = set_info["name"]
        self.iq = iq
        self.db = db

        self.column_list = []
        self.column_info = []

        return

    def refresh_related_set_info(self):
        return

    def populate_columns(self, columns):
        self.column_info = {}
        for column in columns:
            column_name = column["name"]
            self.column_info[column_name] = column
            self.column_list.append(column_name)
        return

    # def get_column_alias(self, column):
    #     full_column = self.name + "." + column
    #     alias = self.name + "_" + column
    #     #alias = re.sub("\.", "_", column)        
    #     return full_column + " AS " + alias

    def get_full_column_name(self, column):
        full_column = self.name + "." + column

        return full_column

    def get_column_alias(self, column):
        full_column = self.name + "." + column
        alias = self.name + "_" + column      
        return alias    

    def get_columns_info(self):
        # Return a dictionary with the projection query, as well as a list
        # of aliases used.

        column_info = {}
        column_info["projections"] = []
        column_info["column_alias_list"] = []
        for column in self.column_list:
            full_column = self.get_full_column_name(column)
            alias = self.get_column_alias(column)            

            column_info["projections"].append(full_column + " AS " + alias)
            column_info["column_alias_list"].append(alias)

        return column_info

    def get_column_type(self, column_name):
        if column_name not in self.column_info.keys():
            raise Exception("The column '" + column_name + "' was not found.")        
        return self.column_info[column_name]["type"]

    def get_column_unit(self, column_name):
        if column_name not in self.column_info.keys():
            raise Exception("The column '" + column_name + "' was not found.")        
        return self.column_info[column_name]["unit"]

    def get_column_display_name(self, column_name):
        if column_name not in self.column_info.keys():
            raise Exception("The column '" + column_name + "' was not found.")        
        return self.column_info[column_name]["display_name"]

    def get_column_description(self, column_name):
        if column_name not in self.column_info.keys():
            raise Exception("The column '" + column_name + "' was not found.")        
        return self.column_info[column_name]["description"]             

#========================================================================================================
class IqResultSet(IqSet):
    def __init__(self, db, iq, set_info):
        super().__init__(db, iq, set_info)
        
        self.column_info = self.set_info.get("facts", [])
        self.dimension_sets = []
        self.primary_dimension_set = None

        self.populate_columns(self.column_info)

        return

    def refresh_related_set_info(self):
        # We can't put this in the class __init__ due to a race condition.
        
        for dimension_set_name in self.set_info.get("dimension_sets", []):            
            dimension_set = self.db.find_set_by_name(dimension_set_name)
            self.dimension_sets.append(dimension_set)

        primary_dimension_set_name = self.set_info.get("primary_dimension_set", None)
        self.primary_dimension_set = self.db.find_set_by_name(primary_dimension_set_name)

        return

    def get_full_column_name(self, column, latest=False):
        if latest:
            full_column = "(" + self.name + "$last." + column + ")"
        else:
            full_column = self.name + "." + column

        return full_column        

    def get_columns_info(self, latest=False):        

        column_info = {}
        column_info["projections"] = []
        column_info["column_alias_list"] = []
        for column in self.column_list:
            full_column = self.get_full_column_name(column, latest)
            alias = self.get_column_alias(column)            

            column_info["projections"].append(full_column + " AS " + alias)
            column_info["column_alias_list"].append(alias)

        for dimension_set in self.dimension_sets:
            for column in dimension_set.column_list:
                full_column = dimension_set.get_full_column_name(column)
                alias = dimension_set.get_column_alias(column)
                column_info["projections"].append(full_column + " AS " + alias)
                column_info["column_alias_list"].append(alias)        

        return column_info

#========================================================================================================
class IqDimensionSet(IqSet):
    def __init__(self, db, iq, set_info):
        super().__init__(db, iq, set_info)

        # Attributes are the columns for a dimension_set object.
        self.column_info = self.set_info.get("attributes", [])

        self.populate_columns(self.column_info)
        return     

#========================================================================================================
class IqQuery:
    def __init__(self, db, name=None):

        self.name = name
        self.db = db
        
        self.iq_set = None        

        self.filters = []
        self.groups = []
        self.orders = []
        self.timestamp_range = {}
        self.limit = None
        self.pagination = None
       
        return    

    def execute(self):
        query = self.get_query()
        result = self.db.iq.execute_query(query, db_id=self.db.id)
        return result

    def get_query(self):

        query = {}
        query["alias"] = self.name        
        query["filters"] = self.filters
        query["groups"] = self.groups
        query["orders"] = self.orders
        query["timestamp_range"] = self.timestamp_range
        query["limit"] = self.limit
        query["pagination"] = self.pagination

        return query

    def add_filter(self, filter):        
        self.filters.append(filter)
        return

    def delete_filters(self):
        self.filters = []
        return

    def add_group(self, group):
        self.groups.append(group)
        return

    def delete_groups(self):
        self.groups = []
        return

    def add_order(self, order):
        self.orders.append(group)
        return

    def delete_orders(self):
        self.orders = []

    def add_timestamp_range(self, timestamp=None):

        self.timestamp_range = {}
        if timestamp:
            self.timestamp_range = timestamp

        return

    def add_timestamp_range_absolute(self, start=None, end=None):

        self.timestamp_range = {}        

        if start or end:
            self.timestamp_range["absolute"] = {}

            if start:
                if not isinstance(start, str):
                    # This is probably a datetime object.
                    startstr = self.db.iq.iso_format(start)
                else:
                    startstr = start

                self.timestamp_range["absolute"]["start"] = startstr

            if end:
                if not isinstance(end, str):
                    # This is probably a datetime object.
                    endstr = self.db.iq.iso_format(end)
                else:
                    endstr = end

                self.timestamp_range["absolute"]["end"] = endstr

        return                

    def add_timestamp_range_relative(self, interval=None):
        # Example intervals are "PT1M" and "PT1H".
        self.timestamp_range = {}
        
        if interval:
            self.timestamp_range["relative"] = {}
            self.timestamp_range["relative"]["interval"] = interval

        return                        

    def add_limit(self):
        return

    def add_pagination(self):
        return

#========================================================================================================
class IqSingleQuery(IqQuery):
    def __init__(self, db, iq_set_name=None, name=None):
        super().__init__(db, name=name)

        if not name:
            self.name = iq_set_name

        self.iq_set = db.find_set_by_name(iq_set_name)

        self.columns_info = None
        self.columns = []

        self.refresh_columns_info()
        return       

    def get_columns(self):        
        return self.columns

    def refresh_columns_info(self, latest=False):
        self.columns_info = self.iq_set.get_columns_info(latest)
        self.columns = self.columns_info["column_alias_list"]        
        return

    def get_query(self, latest=False):
        query = super().get_query()

        self.refresh_columns_info(latest)

        query["projections"] = self.columns_info["projections"]

        return query

    def execute(self, latest=False):        
        query = {}
        query["single_result"] = self.get_query(latest)
        result = self.db.iq.execute_query(query, db_id=self.db.id)
        return result        

#========================================================================================================
class IqMultiQuery(IqQuery):
    def __init__(self, db, iq_set_names=None, subqueries=None, name=None, keys=None):
        super().__init__(db, name=name)      

        # A multiquery is made up of two, or more, subqueries, which could be either 
        # SINGLE_RESULT or MULTI_RESULT queries (or any combination thereof).
        self.subqueries = []

        # If the user has specified a set name, create a single_result query object.
        for set_name in iq_set_names:
            iq_set = IqSingleQuery(db, iq_set_name=set_name)

            self.subqueries.append(iq_set)

        # The keys are required to correlate the subqueries.
        self.keys = []
        if keys:
            self.keys = keys
         
        return

    def get_columns(self):
        columns = []
        for query in self.subqueries:
            columns += query.get_columns()
        return columns

    def add_subqueries(self, queries):
        for query in queries:
            self.subqueries.append(query)
        return

    def get_query(self, latest=False):

        query = {}
        query["alias"] = self.name
        query["filters"] = self.filters
        query["groups"] = self.groups
        query["orders"] = self.orders
        query["limit"] = self.limit
        query["pagination"] = self.pagination

        query["subqueries"] = []
        query["projections"] = []

        columns = []
        key_dict = {}

        for subquery in self.subqueries:
            query["subqueries"].append(subquery.get_query(latest))

            for column in subquery.get_columns():
                full_column = subquery.name + "." + column
                alias = column

                if column not in columns:
                    columns.append(column)                                
                    query["projections"].append(full_column + " AS " + alias)

                if column in self.keys:
                    # This is a key that is used to join the two queries.
                    if column not in key_dict.keys():
                        key_dict[column] = []

                    key_dict[column].append(full_column)

        if not query["filters"]:
            query["filters"] = []

        for column in key_dict.keys():
            if len(key_dict[column]) == 1:
                raise Exception("The key '" + column + "' was only found in one sub-query. It must exist in all sub-queries.")
            elif len(key_dict[column]) > 2:
                raise Exception("The key '" + column + "' was only found in more than two sub-queries.")
            else:                
                query["filters"].append(key_dict[column][0] + "=" + key_dict[column][1])
        
        return query     

    def execute(self, latest=False, custom_query=None):        
        query = {}
        
        if not custom_query:
            query["multi_result"] = self.get_query(latest)
        else:
            query["multi_result"] = custom_query

        result = self.db.iq.execute_query(query, db_id=self.db.id)
        return result                 

