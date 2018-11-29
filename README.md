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
