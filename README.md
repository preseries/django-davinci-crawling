# Da Vinci

Dango library to manage crawling services. It's built on top of `caravaggio_api` to allow 

API project template based on `Django 2.1 (and higher)`, and `DRF 3.8 (and higher)`.

Technologies:

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
- Google App Engine Flexible (Custom) support
- PGBouncer Connection Pool supported in the Docker image
    

## How create a new Crawler project

```
$ conda create -n myproject pip python=3.7
$ conda activate myproject

$ pip install django>=2

$ django-admin.py startproject \
  --template=https://github.com/preseries/davinci-crawling-template-project/archive/master.zip \
  --name=Dockerfile \
  --extension=py,md,env,sh,template,yamltemplate \
  myproject
```

We can now follow the instructions explained in the README.md file inside the new created project in order to install and execute the new crawler code.
    
    
## Testing


### Requirements

When Django runs the test suite, it creates a new database for each entry
 in `settings.DATABASES`, in our case one for postgres and other for cassandra. 

We will get an error message if the postgres user with username django does
 not have permission to create a database. To run the tests we will need first
  to be sure that the `apian` user has rights to do so.
 
 ```
 $ docker run -it --rm --link davinci_crawling-db:postgres postgres:9.6 psql -h postgres -U postgresPassword for user postgres: 
psql (9.6.1)
Type "help" for help.

postgres=# ALTER USER davinci_crawling CREATEDB;
ALTER ROLE
 ```
   
### Run the tests

To run the tests we only need to run the following instruction:

```
$ python manage.py test --testrunner=davinci_crawling.testrunner.TestRunner
```

The output will be something like:

```
Creating test database for alias 'default'...
Creating test database for alias 'cassandra'...
Creating keyspace test_apian [CONNECTION cassandra] ..
Syncing davinci_crawling.example.models.BovespaCompany
Syncing davinci_crawling.example.models.BovespaCompanyFile
Syncing davinci_crawling.example.models.BovespaAccount
System check identified no issues (0 silenced).
E
======================================================================
ERROR: test_create_companies (company.tests.tests.GetAllCompanyTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/accounts/xalperte/documents/MasterUOC/Classes/Project/code/apian/company/tests/tests.py", line 24, in setUp
    self.companies = slurp("./companies.json")
  File "/Users/xalperte/anaconda/envs/apian/lib/python3.7/site-packages/spitslurp/__init__.py", line 51, in slurp
    with io.open(path, 'r', encoding=encoding) as f:
FileNotFoundError: [Errno 2] No such file or directory: './companies.json'

----------------------------------------------------------------------
Ran 1 test in 0.007s

FAILED (errors=1)
Destroying test database for alias 'default'...
Destroying test database for alias 'cassandra'...
```

Avoid the destruction of the database after the tests have finished and the indexes synchronization:

```
$ python manage.py test --testrunner=caravaggio_rest_api.testrunner.TestRunner --keepdb --keep-indexes
```


## Run the Crawler

To run the crawler we only need to use the Django Command `crawl`.

To see all the available options in the Crawler run:

```
$ python manage.py crawl <MY_CRAWLER_NAME> --help
```

It will give you the following output:

```
INFO Calling crawler: <MY_CRAWLER_NAME>
usage: <MY_CRAWLER_NAME> [-h] [--cache-dir CACHE_DIR] [--local-dir LOCAL_DIR]
               [--workers-num WORKERS_NUM] --phantomjs-path PHANTOMJS_PATH
               [--io-gs-project IO_GS_PROJECT]
               [--current-execution-date CURRENT_EXECUTION_DATE]
               [--last-execution-date LAST_EXECUTION_DATE]
               [....]
               [CUSTOM CRAWLER PARAMS]
               [....]
               [--version] [-v {0,1,2,3}] [--settings SETTINGS]
               [--pythonpath PYTHONPATH] [--traceback] [--no-color]

Crawler settings

optional arguments:
  -h, --help            show this help message and exit
  --cache-dir CACHE_DIR
                        The path where we will leave the files. Ex.
                        fs:///data/harvest/permanent gs://davinci_harvest
  --local-dir LOCAL_DIR
                        The path where we will leave the files. Ex.
                        fs///data/harvest/volatile
  --workers-num WORKERS_NUM
                        The number of workers (threads) to launch in parallel
  --phantomjs-path PHANTOMJS_PATH
                        Absolute path to the bin directory of the PhantomJS
                        library.Ex. '/phantomjs-2.1.1-macosx/bin/phantomjs'
  --io-gs-project IO_GS_PROJECT
                        If we are using Google Storage to persist the files,
                        we could need to inform about the project of the
                        bucket.Ex. centering-badge-212119
  --current-execution-date CURRENT_EXECUTION_DATE
                        The current time we are starting the crawler (UTC) Ex.
                        '2008-09-03T20:56:35.450686Z
  --last-execution-date LAST_EXECUTION_DATE
                        The last time we executed the crawler (UTC) Ex.
                        '2007-09-03T20:56:35.450686Z
  .....
  CUSTOM CRAWLER PARAMS HELP MESSAGE
  .....
  --version             show program's version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn't provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don't colorize the command output.
```

For example, if we want to start the crawler to crawl using __MY_CRAWLER_NAME__, we run:

```
$ python manage.py crawl <MY_CRAWLER_NAME> \
    -v 0 --workers-num 10 \
    --phantomjs-path /phantomjs-2.1.1-macosx/bin/phantomjs \
    --io-gs-project centering-badge-212119 \
    --cache-dir "gs://vanggogh2_harvest" \
    --local-dir "fs:///data/harvest/local"
```

## TODO

### Start Docker Instances for crawl

- Example to start a VM from python

https://medium.com/google-cloud/using-app-engine-to-start-a-compute-engine-vm-be713c98d6a
https://github.com/fivunlm/app-engine-start-vm/blob/master/main.py

- Container Optimized OS instances

https://cloud.google.com/container-optimized-os/docs/how-to/run-container-instance
https://cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance 


Init instances:

- Cloud-init to start the docker container instance)

    https://cloud.google.com/container-optimized-os/docs/how-to/create-configure-instance#viewing_available_images

- or, Startup script

    https://cloud.google.com/compute/docs/startupscript
    
    
### Proxies Support

- Rotating proxies utilities:
    - For Scrappy (we can extract ideas) https://github.com/TeamHG-Memex/scrapy-rotating-proxies
    - The S1mbi0se proxy for conclas project: https://github.com/s1mbi0se/conclas/blob/master/conclas/miner/proxy.py 
    
- Obtain lists of proxies (free)

    - FREE: list-proxies node module made exactly for that: https://github.com/chill117/proxy-lists it generates a proxy file that can be used by the previous rotation proxy code.
    - https://proxymesh.com

