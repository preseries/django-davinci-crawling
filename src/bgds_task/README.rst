{{ app_name | capfirst }} Crawler
===================================

**Title**:

**Subtitle**:

Context
-------

Motivation.

Acknowledges
------------

Resources:

-  Subirats, L., Calvo, M. (2018). Web Scraping. Editorial UOC.

-  Lawson, R. (2015). Web Scraping with Python. Packt Publishing Ltd.
   Chapter 2. Scraping the Data.

-  ....

License
-------

This software has been licensed under CC BY-SA 4.0.

With this license you are free to:

-  **Share** — copy and redistribute the material in any medium or
   format
-  **Adapt** — remix, transform, and build upon the material for any
   purpose, even commercially.

With the following conditions:

-  **Attribution**: you must give appropriate credit, provide a link to
   the license, and indicate if changes were made. You may do so in any
   reasonable manner, but not in any way that suggests the licensor
   endorses you or your use.

-  **ShareAlike**: if you remix, transform, or build upon the material,
   you must distribute your contributions under the same license as the
   original.

Code
----

The crawler code is inside the implementation of the ``Crawler class``
at ``{{ app_name | lower }}.crawlers.{{ app_name | capfirst }}Crawler``.

**crawl.py**: is the main function of the crawler.

The **utils.py** contains some utility methods to manage the control
files and date time objects.

...

Installation
~~~~~~~~~~~~

To run the crawler we will need to install the Chromium and Chromedriver
tools.

We can install the libraries using Homebrew:

1. Chromium browser

.. code:: bash

    $ brew cask install chromium

2. Chromedriver

.. code:: bash

    $ brew cask install chromedriver

We can test the installation running the following instruction:

.. code:: bash

    $ chromedriver --version
    ChromeDriver 77.0.3865.40 (f484704e052e0b556f8030b65b953dce96503217-refs/branch-heads/3865@{#442})

We will need to remember the Chromium binary file location because a
reference to the ``/Applications/Chromium.app/Contents/MacOS/Chromium``
file will be needed.

The crawler is implemented for Python 3.6. Then we will need a 3.6
environment ready to install the dependencies.

We can use `Anaconda <https://conda.io/docs/installation.html>`__ to
manage the environment. Once Anaconda is present in our system, we can
do the following steps:

::

    $ conda create -n bovespa_crawler python=3.6
    $ conda activate bovespa_crawler
    $ python setup install

We need to install ``GDAL library`` for Spatial queries (in Sierra MAC
OSX or above):

::

    $ sudo chown -R $(whoami) $(brew --prefix)/*
    $ sudo install -d -o $(whoami) -g admin /usr/local/Frameworks
    $ brew install gdal

Now the crawler should be ready to run.

Run the crawler
~~~~~~~~~~~~~~~

To run the crawler we only need to run the ``crawl.py`` script. The
crawler can be invoked using the following config parameters:

Arguments:

-  ``--chromium-bin-file``: The path where we can found the Chromium
   binary installed. Default: ``None``. Ex:
   "/Applications/Chromium.app/Contents/MacOS/Chromium".

-  ``--from-date``: Extract only the data after an specific date.
   Default: ``None``. Ex: "2018-01-01".

-  ``--cache-folder``: The folder we want to use to save the downloaded
   files. Default: ``./crawler_cache``. Ex: /data/crawlers/bovespa.

-  ``--workers-num``: The number of parallel threads crawling. Default:
   ``10``. Ex: 20.

Examples:

-  Crawl all the resources using 5 parallel processes

::

    python crawl.py {{ app_name | lower }} \
        --chromium-bin-file '/Applications/Chromium.app/Contents/MacOS/Chromium' \
        --workers-num 5 \
        --io-gs-project centering-badge-212119 \
        --cache-dir "gs://davinci_crawling" \
        --local-dir "fs:///data/davinci_crawling/local"

Run the tests
~~~~~~~~~~~~~

To run the tests we only need to run the following instruction:

::

    $ python manage.py test --testrunner=caravaggio_rest_api.testrunner.TestRunner {{ app_name | lower }}/tests

The output will be something like:

::

    Creating test database for alias 'default'...
    Creating test database for alias 'cassandra'...
    Creating keyspace test_apian [CONNECTION cassandra] ..
    Syncing {{ app_name | lower }}.models.{{ app_name | capfirst }}Resource
    System check identified no issues (0 silenced).
    ...
    ...

Avoid the destruction of the database after the tests have finished and
the indexes synchronization:

::

    $ python manage.py test --testrunner=caravaggio_rest_api.testrunner.TestRunner --keepdb --keep-indexes {{ app_name | lower }}/tests

**NOTE**: you should create the index once at least.
