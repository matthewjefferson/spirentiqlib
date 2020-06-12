#!/usr/bin/env python
"""Provides canned result objects that use the spirenttestcenteriq module.
    
"""

from spirenttestcenteriq import *

__author__ = "Matthew Jefferson"
__copyright__ = "Copyright 2020, Spirent Communications"
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
        
class Results:
    def __init__(self, db):

        self.db = db
        self.query = None
        self.keys = None
        self.raw_result_data = None
        self.counters = None

        return

    def refresh(self, latest=True):
        query = { 'alias': None,
                  'filters': [ 'tx_stream_live_stats.tx_stream_stream_id=rx_stream_live_stats.rx_stream_stream_id'],
                  'groups': [],
                  'limit': None,
                  'orders': [],
                  'pagination': None,
                  'projections': [ 'tx_stream_live_stats.tx_stream_live_stats_timestamp AS tx_stream_live_stats_timestamp',
                                   'tx_stream_live_stats.tx_stream_live_stats_frame_count AS tx_stream_live_stats_frame_count',
                                   'tx_stream_live_stats.tx_stream_live_stats_frame_rate AS tx_stream_live_stats_frame_rate',
                                   'tx_stream_live_stats.tx_stream_stream_id AS tx_stream_stream_id',
                                   'tx_stream_live_stats.port_name AS port_name',
                                   'tx_stream_live_stats.port_handle AS port_handle',
                                   'tx_stream_live_stats.tx_port_handle AS tx_port_handle',
                                   'tx_stream_live_stats.tx_port_name AS tx_port_name',
                                   'tx_stream_live_stats.tx_port_scheduling_mode AS tx_port_scheduling_mode',
                                   'tx_stream_live_stats.tx_port_speed AS tx_port_speed',
                                   'tx_stream_live_stats.stream_block_name AS stream_block_name',
                                   'tx_stream_live_stats.tx_stream_config_ipv4_1_dest_addr AS tx_stream_config_ipv4_1_dest_addr',
                                   'tx_stream_live_stats.tx_stream_config_ipv4_1_source_addr AS tx_stream_config_ipv4_1_source_addr',
                                   'rx_stream_live_stats.rx_stream_live_stats_timestamp AS rx_stream_live_stats_timestamp',
                                   'rx_stream_live_stats.rx_stream_live_stats_sig_frame_count AS rx_stream_live_stats_sig_frame_count',
                                   'rx_stream_live_stats.rx_stream_stream_id AS rx_stream_stream_id',
                                   'rx_stream_live_stats.rx_stream_live_stats_sig_frame_rate AS rx_stream_live_stats_sig_frame_rate',
                                   'rx_stream_live_stats.rx_stream_live_stats_avg_latency AS rx_stream_live_stats_avg_latency',
                                   'rx_stream_live_stats.rx_port_handle AS rx_port_handle',
                                   'rx_stream_live_stats.rx_port_name AS rx_port_name'],
                  'subqueries': [ { 'alias': 'tx_stream_live_stats',
                                    'filters': [],
                                    'groups': [],
                                    'limit': None,
                                    'orders': [],
                                    'pagination': None,
                                    'projections': [ '(tx_stream_live_stats$last.timestamp) AS tx_stream_live_stats_timestamp',
                                                     '(tx_stream_live_stats$last.frame_count) AS tx_stream_live_stats_frame_count',
                                                     '(tx_stream_live_stats$last.frame_rate) AS tx_stream_live_stats_frame_rate',
                                                     'tx_stream.stream_id AS tx_stream_stream_id',
                                                     'port.name AS port_name',
                                                     'port.handle AS port_handle',
                                                     'tx_port.handle AS tx_port_handle',
                                                     'tx_port.name AS tx_port_name',
                                                     'tx_port.scheduling_mode AS tx_port_scheduling_mode',
                                                     'tx_port.speed AS tx_port_speed',
                                                     'stream_block.name AS stream_block_name',
                                                     'tx_stream_config.ipv4_1_dest_addr AS tx_stream_config_ipv4_1_dest_addr',
                                                     'tx_stream_config.ipv4_1_source_addr AS tx_stream_config_ipv4_1_source_addr'],
                                    'timestamp_range': {}},
                                  { 'alias': 'rx_stream_live_stats',
                                    'filters': [],
                                    'groups': [],
                                    'limit': None,
                                    'orders': [],
                                    'pagination': None,
                                    'projections': [ '(rx_stream_live_stats$last.timestamp) AS rx_stream_live_stats_timestamp',
                                                     '(rx_stream_live_stats$last.frame_count) AS rx_stream_live_stats_frame_count',
                                                     '(rx_stream_live_stats$last.sig_frame_count) AS rx_stream_live_stats_sig_frame_count',
                                                     'rx_stream.stream_id AS rx_stream_stream_id',
                                                     '(rx_stream_live_stats$last.sig_frame_rate) AS rx_stream_live_stats_sig_frame_rate',
                                                     '(rx_stream_live_stats$last.avg_latency) AS rx_stream_live_stats_avg_latency',
                                                     'rx_port.handle AS rx_port_handle',
                                                     'rx_port.name AS rx_port_name'],
                                    'timestamp_range': {}}]}

        # query = { 'alias': None,
        #           'filters': [ 'tx_stream_live_stats.tx_stream_stream_id=rx_stream_live_stats.rx_stream_stream_id'],
        #           'groups': [],
        #           'limit': None,
        #           'orders': [],
        #           'pagination': None,
        #           'projections': [ 'tx_stream_live_stats.tx_stream_live_stats_timestamp AS tx_stream_live_stats_timestamp',
        #                            'tx_stream_live_stats.tx_stream_live_stats_frame_count AS tx_stream_live_stats_frame_count',
        #                            'tx_stream_live_stats.tx_stream_live_stats_frame_rate AS tx_stream_live_stats_frame_rate',
        #                            'tx_stream_live_stats.tx_stream_stream_id AS tx_stream_stream_id',
        #                            'tx_stream_live_stats.port_name AS port_name',
        #                            'tx_stream_live_stats.port_handle AS port_handle',
        #                            'tx_stream_live_stats.tx_port_handle AS tx_port_handle',
        #                            'tx_stream_live_stats.tx_port_name AS tx_port_name',
        #                            'tx_stream_live_stats.tx_port_scheduling_mode AS tx_port_scheduling_mode',
        #                            'tx_stream_live_stats.tx_port_speed AS tx_port_speed',
        #                            'tx_stream_live_stats.stream_block_name AS stream_block_name',
        #                            'tx_stream_live_stats.tx_stream_config_ipv4_1_dest_addr AS tx_stream_config_ipv4_1_dest_addr',
        #                            'tx_stream_live_stats.tx_stream_config_ipv4_1_source_addr AS tx_stream_config_ipv4_1_source_addr',
        #                            'rx_stream_live_stats.rx_stream_live_stats_timestamp AS rx_stream_live_stats_timestamp',
        #                            'rx_stream_live_stats.rx_stream_live_stats_sig_frame_count AS rx_stream_live_stats_sig_frame_count',
        #                            'rx_stream_live_stats.rx_stream_stream_id AS rx_stream_stream_id',
        #                            'rx_stream_live_stats.rx_stream_live_stats_sig_frame_rate AS rx_stream_live_stats_sig_frame_rate',
        #                            'rx_stream_live_stats.rx_stream_live_stats_avg_latency AS rx_stream_live_stats_avg_latency',
        #                            'rx_stream_live_stats.rx_port_handle AS rx_port_handle',
        #                            'rx_stream_live_stats.rx_port_name AS rx_port_name'],
        #           'subqueries': [ { 'alias': 'tx_stream_live_stats',
        #                             'filters': [],
        #                             'groups': [],
        #                             'limit': None,
        #                             'orders': [],
        #                             'pagination': None,
        #                             'projections': [ '(tx_stream_live_stats.timestamp) AS tx_stream_live_stats_timestamp',
        #                                              '(tx_stream_live_stats.frame_count) AS tx_stream_live_stats_frame_count',
        #                                              '(tx_stream_live_stats.frame_rate) AS tx_stream_live_stats_frame_rate',
        #                                              'tx_stream.stream_id AS tx_stream_stream_id',
        #                                              'port.name AS port_name',
        #                                              'port.handle AS port_handle',
        #                                              'tx_port.handle AS tx_port_handle',
        #                                              'tx_port.name AS tx_port_name',
        #                                              'tx_port.scheduling_mode AS tx_port_scheduling_mode',
        #                                              'tx_port.speed AS tx_port_speed',
        #                                              'stream_block.name AS stream_block_name',
        #                                              'tx_stream_config.ipv4_1_dest_addr AS tx_stream_config_ipv4_1_dest_addr',
        #                                              'tx_stream_config.ipv4_1_source_addr AS tx_stream_config_ipv4_1_source_addr'],
        #                             'timestamp_range': {}},
        #                           { 'alias': 'rx_stream_live_stats',
        #                             'filters': [],
        #                             'groups': [],
        #                             'limit': None,
        #                             'orders': [],
        #                             'pagination': None,
        #                             'projections': [ '(rx_stream_live_stats.timestamp) AS rx_stream_live_stats_timestamp',
        #                                              '(rx_stream_live_stats.frame_count) AS rx_stream_live_stats_frame_count',
        #                                              '(rx_stream_live_stats.sig_frame_count) AS rx_stream_live_stats_sig_frame_count',
        #                                              'rx_stream.stream_id AS rx_stream_stream_id',
        #                                              '(rx_stream_live_stats.sig_frame_rate) AS rx_stream_live_stats_sig_frame_rate',
        #                                              '(rx_stream_live_stats.avg_latency) AS rx_stream_live_stats_avg_latency',
        #                                              'rx_port.handle AS rx_port_handle',
        #                                              'rx_port.name AS rx_port_name'],
        #                             'timestamp_range': {}}]}        
        
        self.raw_result_data = self.query.execute(latest=latest, custom_query=query)
        #self.raw_result_data = self.query.execute(latest=latest)         

        if "result" in self.raw_result_data.keys() and "columns" in self.raw_result_data["result"].keys():
            self.counters = self.raw_result_data["result"]["columns"]

        return self.raw_result_data

class StreamLiveResults(Results):
    def __init__(self, db):
        super().__init__(db)      

        self.result_data = None

        self.keys = ["tx_stream_stream_id"]

        self.query = IqMultiQuery(db, ["tx_stream_live_stats", "rx_stream_live_stats"], keys=self.keys)

        return

    @timeit
    def refresh(self, latest=True):
        super().refresh(latest)      

        keys = self.keys + ["tx_stream_live_stats_timestamp"]
        self.result_data = self.db.iq.convert_result_to_dict(self.raw_result_data, key_names=keys)        

        return self.result_data
