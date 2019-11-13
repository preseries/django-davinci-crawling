.. _davinci_kafka_monitoring:

.. highlight:: rst

.. role:: python(code)
    :language: python

.. role:: latex(code)
    :language: latex

Kafka Monitoring
================

This guide will help you around all the integrations that have been done for the Kafka monitoring.

1. Architecture
---------------
The architecture has three main components, KSQL, Prometheus and Grafana.

- KSQL will provide the data;
- Prometheus will collect the data from KSQL and turn into metrics;
- Grafana will collect the metrics and plot graphs with them.

1.1. KSQL
********
KSQL is one of the most important components of the Kafka infrastructure, all the tasks requests will
be streamed on KSQL to be split into separated topics on Kafka, on KSQL we can create real-time tables
that will change the data dynamically when new data arrives, we created a bunch of tables on KSQL to
supply our monitoring needs.

We created tables for almost all scenarios and situations, below you can find an example of a table
creation.

.. code-block:: sql

    CREATE TABLE DAVINCI_TASKS_CREATED_ALL_ON_DEMAND_5_MINUTE AS SELECT STATUS, TYPE, count(*)
    WINDOW TUMBLING (SIZE 5 MINUTE) WHERE STATUS = 0 AND TYPE = 1 GROUP BY STATUS, TYPE;

We have tables for CREATED, FINISHED and ERROR statuses, in each of them for HIGH and NORMAL priorities
and for each of these combinations, 4 times windows. Like this:

- Quantity of CREATED crawling tasks
   - All Crawlers (HIGH AND NORMAL)
       - 5min
       - 30min
       - 1 hour
       - 1 day
   - Specific Crawlers (HIGH AND NORMAL)
       - 5min
       - 30min
       - 1 hour
       - 1 day
- Quantity of FINISHED crawling tasks
   - All Crawlers (HIGH AND NORMAL)
       - 5min
       - 30min
       - 1 hour
       - 1 day
   - Specific Crawlers (HIGH AND NORMAL)
       - 5min
       - 30min
       - 1 hour
       - 1 day
- Quantity of ERROR crawling tasks
   - All Crawlers (HIGH AND NORMAL)
       - 5min
       - 30min
       - 1 hour
       - 1 day
   - Specific Crawlers (HIGH AND NORMAL)
       - 5min
       - 30min
       - 1 hour
       - 1 day

1.2. Prometheus
**************
Prometheus is used to collect the data from KSQL and create metrics with this data,
to work with Prometheus we need to add exporters to it in order to create the metrics.

The exporters will expose metrics to Prometheus that will retrieve the metrics from time
to time.

We created a new exporter to extract KSQL data, this exporter is based on the `JDBC exporter <https://github.com/sysco-middleware/prometheus-jdbc-exporter>`_,
we started to use the JDBC exporter but we found out that as KSQL use real-time
queries we need to improve how the exporter works, that's why we created a `KSQL Exporter <https://github.com/buildgroupai/prometheus-ksql-exporter>`_,
our KSQL Exporter uses the `KSQL JDBC Driver <https://github.com/mmolimar/ksql-jdbc-driver>`_ to make the queries and expose the results to Prometheus.

To add new queries to Prometheus we need to modify the config.yml file inside the `davinci-kafka-processing <https://github.com/buildgroupai/davinci-kafka-processing>`_ project (environment/local/prometheus/config.yml) and include the new queries to be exported.
The file looks like this example below:

.. code-block:: yaml

    ---
    connections:
      - url: 'jdbc:ksql://address-of-ksql:8088'
        prepare_statement_support: false
    queries:
      - name: "all_batch_5_minute"
        help: "All Batches (5 minutes window)"
        values:
          - "KSQL_COL_2"
        query:  |
          SELECT KSQL_COL_2 FROM DAVINCI_TASKS_CREATED_ALL_BATCH_5_MINUTE
      - name: "all_on_demand_5_minute"
        help: "All On Demand (5 minutes window)"
        values:
          - "KSQL_COL_2"
        query:  |
          SELECT KSQL_COL_2 FROM DAVINCI_TASKS_CREATED_ALL_ON_DEMAND_5_MINUTE

To add new queries you just need to add new objects to the queries section. The metrics that will be
exported will have the same name as the name you specified to the query.

With all this configured we now have all the metrics on Prometheus.

1.3. Grafana
***********
The last piece of the infrastructure is the Grafana or any visualization tool,
Grafana has direct integration with Prometheus, to use Grafana is very simple,
just need to add Prometheus as a data source and start using it to create new
graphs and statistics.

1.4. Any other visualization tool
********************************
As we used Prometheus as the centralized tool to serve metrics we can use any
other visualization tools to mount our graphs and statistics we just need to
integrate with our Prometheus server.

2. How to run
------------
For these services, we have a docker-compose file that will start and configure
all the pieces needed on the monitoring. The docker-compose file is on the
`davinci-kafka-processing <https://github.com/buildgroupai/davinci-kafka-processing>`_
project on the infrastructure/local/prometheus folder.

Just need to run a `docker-compose up` command to start all the monitoring.

