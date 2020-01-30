##########
Changelog
##########

Current
=======

New Features
************
- Support for parallelism on crawl command using the producer/consumer pattern
    - The `crawl_params` calls a `produce.add_crawl_params` method to add a crawl param.
    - The `crawl` now is called by a consumer that runs in background.
- Add the Sphinx documentation to the davinci crawling;
- Add the task API to the DaVinci Crawling.
- Add the crawl_params method that will create a batch task on the DaVinci Task.
- Add a delete_json method to the net.py file to support delete requests.
- Add a method to utils to get all registered crawlers.
- Add distributed throttle implementation using Redis;
- Add pylimit to the requirements;
- Add proxy mesh to chrome driver on selenium;
- Add proxy mesh to fetch_file to download files;
- Add persistent-queue to the crawl flow to avoid losing tasks if their state are QUEUED or RUNNING;
- Add jsondiff on the register_differences method to allow comparison between resource versions created by crawlers;

Improvements or Changes
***********************
- Change the `crawl_params` to receive a producer parameter
    - This producer is an implementation of CrawlParamsProducer class, for example:
.. code-block:: python
   :linenos:
    class CrawlParamsQueueProducer(CrawlParamsProducer):
        ....
        def add_crawl_params(self, param, options):
            ....
            multiprocess_queue.put([param, options])

- Add a `to_date` option to the bovespa crawler
- Add a `crawling_initials` option to the bovespa crawler
- Change all the multiprocessing implementations to be Thread instead of Process
    - We need that to better deal with cassandra in different threads, with the process we weren't able to have a process inside a process
- Add the field `thread_id` to the `BovespaCompanyFile` that stores the thread id that processes the file
- Add the possibility to change the `LOGGING_FILE` on settings using an enviroment variable with the same name
- Change the crawl command to pool tasks from the DB;
- Improve the Throttle class to be extended;
- Change the key used on throttle from `<function_name>` to `<crawler_name>_<function_name>_<throttle_suffix>`
- Add maintenance status to the task;
- Add a `more_info` field to the task;
- Remove unnecessary usage of the setup_cassandra_object_mapper inside the bovespa crawler;
- Change table name from harvest_checkpoint to davinci_checkpoint;
- Add feature that allows the user to restrict the countries where we can get the proxies from.

Bug Fixing
**********
- Fix a bug with the `include_companies` parameter that wasn't working with a list of companies;
- Truncate milliseconds on created_at on task model because as this field is used as primary key the milliseconds cause errors on comparisons;
- Change proxy quality checker threads to daemon to let the program finish

Version 0.1.5
=============

New Features
************
- Users subsystem for support for Client (External System), Organizations, and Users
- Support for Subscriptions/Allowances and libraries for check permissions/roles
- Add drf-yasg to allow OpenAPI endpoints (schema, documentation)

Improvements or Changes
***********************
- Add support for Django-debug-toolbar and Django-extensions for debug
- Improvement in Throttling configuration. The throttling are registered automatically, no need to define the views in settings.py

Bug fixing
**********
- Updated dependencies using the new url format to reference private Github projects.

Version 0.1.4
=============

New Features
************
- Added support for Chromium and Chromedriver for Selenium

Improvements or Changes
***********************
- Update the Bovespa crawler to use the new interface to get access to the "Selenium Driver" registered into the system:
.. code-block:: python
   :linenos:
    from davinci_crawling.example.bovespa import BOVESPA_CRAWLER
    from davinci_crawling.utils import CrawlersRegistry
    .....
    .....
    def my_crawling_method(..., options, ....)
          .....
          driver = None
           try:
                  ....
                  driver = CrawlersRegistry().get_crawler(
                          BOVESPA_CRAWLER).get_web_driver(**options)
                  ....
                  # use the driver
                  ....
            finally:
                  if driver:
                  driver.quit()

Bug fixing
**********
- Updated version of Caravaggio and Django Cassandra Engine to fix issues with the creation of the Test DB.

Version 0.1.3
=============

New Features
************
Still Experimental:

- Library to manage GCP instance from code
- Scheduler to allow plan the execution of crawlers
- Allow define crawling scheduling by crawler in settings.py

Improvements or Changes
***********************
- Update dependency version with Django Caravaggio REST API, now version 0.1.5.
- The code belongs to BGDS, we have updated the copyright headers to reflect it.
- Remove dependencies to preseries github repo and change it by buildgroupai.

Bug fixing
**********
- New version of Django needs a new command parameter called force-color

Version 0.1.2
=============

New Features
************
- No new features

Improvements
************
- Updated to the 0.1.3 version of Caravaggio REST API, that give us support for RegExp searches using the `regex` operator in queries. Ex. number__regex=1.01.(.).01(.)

Bug fixing
**********
- No bugs fixed

Version 0.1.1
=============

New Features
************
- A new admin commmand `gen_finstat` that generates and Excel with all the financial statements and basic indicatos for a company and period.
- Added examples of two Financial Reports generated with the admin command `gen_finstat` into `davinci_crawling.example.bovespa.management.command.data` folder.
- Bosvespa Crawler example: allow crawling the data of some specific companies (`--include-companies`)

Improvements
************
- Added a `README.md` with a complete explanation of the Bovespa Crawler. We also explain how to use the REST API to query for data, or access directly to the Solr service to do more complex queries.
- Added the `ORDERING_PARAM` field and `COERCE_DECIMAL_TO_STRING` to the `REST_FRAMEWORK` config variable. The first fixes the query param to "order_by", and the second force the serialization of the Decimal fields as decimals instead of strings.
- Adapt the Bovespa code to the refactors made into `django-caravaggio-rest-api`.

Bug Fixing
**********
- Fix bug when copying the file from the GS to the local file system

Other
*****
- Updated dependency version of `django-caravaggio-rest-api`

Version 0.1.0
=============

New Features
************
- Django REST Framework (DRF)
- DRF Cache support (for rdb and cassandra models)
- DRF Throttle support by ViewSet and request action (retrieve, list, create, update, etc.)
- DRF Token Authentication (no username needed, Bearer token)
- PostgreSQL backend for miscellaneous models (User, Token, etc.)
- DSE Cassandra backend for business models
- Configuration of Cassandra-DRF serializers
- Support for JSONField in Cassandra (Text field)
- Support for pre/post callbacks in CassandraModel (DRF cache clean actions)
- DRF-Haystack-DSE support to support fast searches (DSE-Solr) with model examples
- Command to synchronize the DSE tables with the needed search indexes
- Swagger view of the API documentation

