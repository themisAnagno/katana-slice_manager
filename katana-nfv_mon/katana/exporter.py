#!/usr/bin/env python3

"""
Read the collected NFV metrics and expose them to Prometheus
"""

import logging
import threading

from katana.utils.kafkaUtils.kafkaUtils import create_consumer, create_topic
from katana.utils.threadingUtis.threadingUtils import MonThread
from prometheus_client import start_http_server, Gauge

# Create the logger
logger = logging.getLogger(__name__)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_formatter = logging.Formatter("%(asctime)s %(name)s %(levelname)s %(message)s")
stream_handler.setFormatter(stream_formatter)
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)


def mon_start(ns_list, ns_thread_dict):
    """
    Starts the monitoring of new network services
    """
    logger.info("Starting Network Function Status monitoring")
    for ns_id, ns in ns_list.items():
        for key, value in ns.items():
            location = key.replace("-", "_")
            ns_name = value["ns-name"].replace("-", "_")
            metric_name = "ns_" + ns_name + "_" + location
            dict_entry = ns_thread_dict.get(metric_name, {})
            if not dict_entry:
                ns_status = Gauge(metric_name, "Network Service Status", ["slice_id"])
            else:
                ns_status = next(iter(dict_entry.values()))["metric"]
            ns_status.labels(value["slice_id"]).set(1)
            new_thread = MonThread(value, ns_status)
            new_thread.start()
            dict_entry[ns_id] = {"thread": new_thread, "metric": ns_status}
            ns_thread_dict[metric_name] = dict_entry


def mon_stop(ns_list, ns_thread_dict):
    """
    Stops the monitoring os new network services
    """
    logger.info("Stoping Network Function Status monitoring")
    for ns_id, ns in ns_list.items():
        for key, value in ns.items():
            location = key.replace("-", "_")
            ns_name = value["ns-name"].replace("-", "_")
            metric_name = "ns_" + ns_name + "_" + location
            mon_thread = ns_thread_dict[metric_name][ns_id]["thread"]
            mon_thread.stop()


def start_exporter():
    """
    Starts the NFV Monitoring. Creates the Kafka consumer
    """

    # Create the thread dictionary
    ns_thread_dict = {}

    # Create the Kafka topic
    create_topic("nfv_mon")

    # Create the Kafka consumer
    consumer = create_consumer("nfv_mon")

    for message in consumer:
        ns_list = message.value["ns_list"]
        if message.value["action"] == "create":
            mon_start(ns_list, ns_thread_dict)
        else:
            mon_stop(ns_list, ns_thread_dict)


if __name__ == "__main__":
    start_http_server(8002)
    start_exporter()
