# Bovespa Crawler

Information about the Bovespa crawler

## Context

There are different approaches to investment analysis. One of these approaches 
is the Value Investing method.

This method tries to discover important gaps between the market price of the 
shares of the companies (official price on the stock exchange), and the real 
price of the company, known as the 
[Intrinsic Value] (https: / /www.investopedia.com/terms/i/intrinsicvalue.asp).

In Value Investing, the ultimate goal is to invest in those companies with a 
considerable low or high intrinsic value compared with the public 
value (stock exchange).

In order to be able to calculate the intrinsic value of Brazilian companies, 
we need to have access to the quarterly financial reports that companies 
deliver to Bovespa.

This crawler will extract the financial reports presented by the Brazilian 
companies on the stock market of São Paulo, and will persist all the 
information in a data backend that could be used later by ETLs to load the 
data to another service. 

## What's Bovespa?

The B3 (in full, B3 - Brasil Bolsa Balcão S.A. or B3 - Brazil, Stock Exchange 
and Over-the-Counter Market), formerly BM&FBOVESPA, is a Stock Exchange 
located at São Paulo, Brazil and the second oldest of the country

## Acknowledgments

We used the following resources to implement the crawler:

- Post [Automatização de balanços](http://clubinvest.boards.net/thread/367/automatiza-de-balan-os) 
explaining the documents available from Bovespa, and how to access to them.
- [Denet](http://www.potuz.net/denet/). An implementation in C++ of a system to do 
fundamental analysis using the information from Bovespa.

Technical resources:

- Subirats, L., Calvo, M. (2018). Web Scraping. Editorial UOC.
- Lawson, R. (2015). Web Scraping with Python. Packt Publishing Ltd. 
Chapter 2. Scraping the Data

Other resources:

- Service to query the documentation delivered by the companies. 
[Link](http://sistemas.cvm.gov.br/port/ciasabertas/)
- Utility to download multiple files from Bovespa (Not used, we do pure web 
scrapping instead). [Link](http://www.cvm.gov.br/menu/regulados/companhias/download_multiplo/index.html)

## License

[MIT License](LICENSE)

Copyright (c) 2019 BuildGroup Data Services Inc.


## Code

The `crawlers.py` file contains the declaration of the BovespaCrawler. 

The crawler is divided into two parts:

- The `crawl_params` method. That will navigate through the web locating all 
the companies that have ever been in Bovespa (`BovespaCompany`), and will 
search for all the files delivered by the companies (`BovespaCompanyFile`), 
returning the list of all the files to be processed (not downloaded and 
processed yet). 

- The `crawl` method. That will receive one file at a time that will be 
downloaded, put it into the permanent cache (GS), and into the volatile 
cache (Local FS), it will be uncompressed, we will extract all the financial 
data and create entries in the database for each 
Account-Value (`BovespaAccount`).


The crawling code is mainly divided in the following parts:

- `crawling_parts/listed_companies.py`: crawl all the listed companies 
in Bovespa (ancient and new)

- `crawling_parts/company_files.py`: crawl the list of delivered files 
by the companies to Bovespa.

- `crawling_parts/download_file.py`: download the delivered files, extract 
the financial information from them, and generate the data/dataset.csv 
and data/dictionary.csv files


### Throttling

The following functions have been throttled to avoid a bad use of the access 
to the source, controlling the quantity of request we would do simultaneously 
to the source to extract all the required data:

- `update_listed_companies` located 
at `crawling_parts/crawl_listed_companies.py`: 50 requests by minute.

- `obtain_company_files` located 
at `crawling_parts/crawl_companies_files.py`: 50 requests by minute.

- `download_file` located 
at `crawling_parts/download_file.py`: 50 requests by minute.


## Installation

First, we need to have the environment correctly setup (Caravaggio). You will found 
instruction on how to prepare your local environment:
 
 - [Setup your local environment](https://github.com/buildgroupai/django-caravaggio-rest-api/blob/master/docs/local_environment.md). 

After that, we will need to install other software that DaVinci, or more specifically our crawler, will need to do its job.

To run the crawler we will need to install the 
[Chromimum](https://www.chromium.org/Home) and 
[Chromedriver](https://chromedriver.chromium.org/) tools 
for scraping dynamic web pages like Bovespa.

```shell script
$ brew cask install chromium
$ brew cask install chromedriver
```

We will need to remember the installation folder because a reference to 
the `/Applications/Chromium.app/Contents/MacOS/Chromium` folder will be needed.

The crawler is implemented using Python 3.6. Then we will need a 3.6 environment
ready to install the dependencies.

We can use [Anaconda](https://conda.io/docs/installation.html) to manage 
the environment. Once Anaconda is present in our system, we can do the 
following steps:

```shell script
$ conda create -n bovespa_crawler python=3.6 pip
$ conda activate bovespa_crawler

$ pip install -r requirements.txt
 
or

$ python setup.py install
```

Now the crawler should be ready to run.

## Run the Crawler

To run the crawler we only need to use the Django Command `crawl`.

To see all the available options run:

```shell script
$ python manage.py crawl bovespa --help
```

It will display usage information and a list of the arguments provided by 
the bovespa crawler application:

```shell script
INFO Calling crawler: bovespa
usage: bovespa [-h] [--cache-dir CACHE_DIR] [--local-dir LOCAL_DIR]
               [--workers-num WORKERS_NUM] [--phantomjs-path PHANTOMJS_PATH]
               [--chromium-bin-file CHROMIUM_BIN_FILE]
               [--io-gs-project IO_GS_PROJECT]
               [--current-execution-date CURRENT_EXECUTION_DATE]
               [--last-execution-date LAST_EXECUTION_DATE]
               [--from-the-beginning] [--from-date FROM_DATE]
               [--to-date TO_DATE]
               [--crawling-initials [CRAWLING_INITIALS [CRAWLING_INITIALS ...]]]
               [--no-update-companies-listing]
               [--companies-listing-update-elapsetime COMPANIES_LISTING_UPDATE_ELAPSETIME]
               [--no-update-companies-files]
               [--companies-files-update-elapsetime COMPANIES_FILES_UPDATE_ELAPSETIME]
               [--force-download]
               [--include-companies [INCLUDE_COMPANIES [INCLUDE_COMPANIES ...]]]
               [--version] [-v {0,1,2,3}] [--settings SETTINGS]
               [--pythonpath PYTHONPATH] [--traceback] [--no-color]
               [--force-color]

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
  --chromium-bin-file CHROMIUM_BIN_FILE
                        Absolute path to the Chromium bin file.Ex.
                        '/Applications/Chromium.app/Contents/MacOS/Chromium'
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
  --from-the-beginning  Crawl all the company files.It is a way to short-
                        circuit the global last/current dates. Ex.
                        '2007-09-03T20:56:35.450686Z
  --from-date FROM_DATE
                        The date from which we want to crawl all the company
                        files.It is a way to short-circuit the global
                        last/current dates. Ex. '2007-09-03T20:56:35.450686Z
  --to-date TO_DATE     The date to which we want to crawl all the company
                        files.
  --crawling-initials [CRAWLING_INITIALS [CRAWLING_INITIALS ...]]
                        If we want to specify the initial letter of the
                        companiesto crawl (ex A B C)
  --no-update-companies-listing
                        If we do not want to update the listed companies
                        crawling the listing from Bovespa. We should update
                        the list once a month Ex. --no-update-companies-
                        listing
  --companies-listing-update-elapsetime COMPANIES_LISTING_UPDATE_ELAPSETIME
                        The elapse time in days between updates of the
                        companies listing Ex. 30
  --no-update-companies-files
                        If we want to update the file contents in the database
                        although the file was already downloaded in the past.
                        Ex. --no-update-companies-files
  --companies-files-update-elapsetime COMPANIES_FILES_UPDATE_ELAPSETIME
                        The elapse time in days between updates of the
                        companies files. Ex. 30
  --force-download      If we want to force the download of the file from
                        bovespa and update the permanent and local caches. Ex.
                        --force-download
  --include-companies [INCLUDE_COMPANIES [INCLUDE_COMPANIES ...]]
                        If we want to focus only on a specific companies.(ex:
                        35 94 1384
  --version             show program\'s version number and exit
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output,
                        2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g.
                        "myproject.settings.main". If this isn\'t provided, the
                        DJANGO_SETTINGS_MODULE environment variable will be
                        used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g.
                        "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions
  --no-color            Don\'t colorize the command output.
  --force-color         Force colorization of the command output.
```

Instruction to start the crawler and crawl __all the data__ 
available at Bovespa:

```shell script
$ python manage.py crawl bovespa \
    -v 0 --workers-num 10 \
    --chromium-bin-file '/Applications/Chromium.app/Contents/MacOS/Chromium' \
    --io-gs-project centering-badge-212119 \
    --cache-dir "gs://bgds_harvester_cache" \
    --local-dir "fs:///data/harvest/local"
```

Crawl information about specific companies only:

```shell script
# Crawling data from PBG S.A and VALE S.A.
$ python manage.py crawl bovespa \
    -v 0 --workers-num 10 \
    --chromium-bin-file '/Applications/Chromium.app/Contents/MacOS/Chromium' \
    --io-gs-project centering-badge-212119 \
    --cache-dir "gs://bgds_harvester_cache" \
    --local-dir "fs:///data/harvest/local" \
    --include-companies 13773 4170 \
    --crawling-initials P V
```

## Command for generate a Financial Analysis report

There is a command that we can use to generate an Excel with a basic analysis 
of the financial statements of a company for a given fiscal period.  

```shell script
$ python manage.py gen_finstat --company-ccvm 13773 --fiscal-date "2013-06-30"
```

This command will generate the Excel file `13773_20130630.xlsx` with the analysis.

## Command for run the API to query the crawled data

You will need to run the Django application as follows:

```shell script 
$ conda activate bovespa_crawler

$ python manage.py runserver 8001
```

After [obtain our user Token](https://github.com/buildgroupai/django-caravaggio-rest-api/blob/master/docs/local_environment.md#run-application-with-development-server), 
we will have everything we need to access the application.

## Advanced queries (using the API or Solr service)

Queries we can do using the Bovespa endpoints for each of the following entities:

- BovespaCompany
- BovespaCompanyFile
- BovespaAccount

Queries:

- [Obtain all the Current Assets for an specific company and period](#Obtain-all-the-Current-Assets-for-an-specific-company-and-period)
- [Obtain all the accounts that follows a pattern (RegEx search)](QueryRegEx)
- [Obtain all the new accounts keyed into the system after a specific date](QueryDate)
- [Get the latest version of a delivered file closest a given fiscal date](Get-the-latest-version-of-a-delivered-file-closest-a-given-fiscal-date)
- [Obtain the list of the latest versions of all documents delivered by the company 15300 that have been already processed](QueryGroupLast)

### Obtain all the Current Assets for an specific company and period

We will use the `/bovespa/company-account/search` endpoint to solve this request.

Arguments:

- Query: `ccvm=15300`
- Restrictions: 
    - `period=2018-06-30T00:00:00Z`, 
    - `balance_type=ASSETS`,
    - `financial_info_type=INSTANT`, 
    - and `number__startswith=1.01`
- Sort results: `order_by=number`

```shell script
$ curl -H 'Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b' \
    -X GET "http://localhost:8001/bovespa/company-account/search/?period=2018-06-30T00:00:00Z&ccvm=15300&balance_type=ASSETS&financial_info_type=INSTANT&number__startswith=1.01&order_by=number"
```

or in python after executing `python manage.py shell` in the base 
dir of the project

```python
from datetime import datetime
from caravaggio_rest_api.haystack.backends.utils import CaravaggioSearchPaginator
from davinci_crawling.example import BovespaAccount
from solrq import Q, Value

ccvm = "15300"
period = datetime.strptime("2018-06-30", "%Y-%m-%d")

filter = Q(period=period) & Q(ccvm=ccvm) & \
    Q(balance_type="ASSETS") & Q(financial_info_type="INSTANT") & \
    Q(number= Value("1.01*", safe=True))

# In Caravaggio, fields marked as facets are indexed twice. One first time a 
# field with the same name will be indexed without being marked as docValues 
# that will allow us do free text searches on its content. And other field 
# renamed to <field_name>_exact being marked as docValues that will optimize 
# the process process of sorting and faceting using the field. The field 
# marked as docValues (_exact) will be the field we use when sorting. If 
# not, we are going to get the following exception
#
# Exception: Field cache is disabled, set the field=number to be 
#   docValues=true and reindex.  Or if the field cache will not exceed 
#   the heap usage, then place useFieldCache=true in the request parameters.
#
paginator = CaravaggioSearchPaginator(
    query_string=str(filter),
    sort='number_exact asc',
    limit=5000, max_limit=5000). \
    models(BovespaAccount). \
    select("version", "number", "name",
           "financial_info_type", "balance_type", "comments",
           "amount")

# Iterate through the results
while paginator.has_next():
    paginator.next()
    for account in paginator.get_results():
        print(account.version, account.number, 
              account.name, account.comments,
              account.financial_info_type, account.balance_type,
              account.amount)
```

And the result will be something like: (it shows 10 of the 36 accounts available for the period)

```json5
{
  "total": 36,
  "page": 10,
  "next": "http://localhost:8001/bovespa/company-account/search/?balance_type=ASSETS&ccvm=15300&number__startswith=1.01&order_by=number&page=2&period=2018-06-30T00%3A00%3A00Z",
  "previous": null,
  "results": [
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Ativo Circulante",
      "value": 2053083.0,
      "created_at": "2018-11-26T22:57:30.742000",
      "updated_at": "2018-11-26T22:57:30.743000",
      "score": 10.552604
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Caixa e Equivalentes de Caixa",
      "value": 42100.0,
      "created_at": "2018-11-26T22:57:30.747000",
      "updated_at": "2018-11-26T22:57:30.747000",
      "score": 10.552604
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Aplicações Financeiras",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.750000",
      "updated_at": "2018-11-26T22:57:30.750000",
      "score": 10.552604
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Aplicações Financeiras Avaliadas a Valor Justo através do Resultado",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.754000",
      "updated_at": "2018-11-26T22:57:30.754000",
      "score": 10.552604
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.01.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Títulos para Negociação",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.758000",
      "updated_at": "2018-11-26T22:57:30.758000",
      "score": 10.552604
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.01.02",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Títulos Designados a Valor Justo",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.762000",
      "updated_at": "2018-11-26T22:57:30.762000",
      "score": 10.552604
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.01.03",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Caixa restrito",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.778000",
      "updated_at": "2018-11-26T22:57:30.779000",
      "score": 10.552604
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.02",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Aplicações Financeiras Avaliadas a Valor Justo através de Outros Resultados Abrangentes",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.790000",
      "updated_at": "2018-11-26T22:57:30.790000",
      "score": 10.552604
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.02.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Títulos Mantidos até o Vencimento",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.797000",
      "updated_at": "2018-11-26T22:57:30.797000",
      "score": 10.552604
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.03",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Aplicações Financeiras Avaliadas ao Custo Amortizado",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:35.844000",
      "updated_at": "2018-11-26T22:57:35.844000",
      "score": 10.552604
    }
  ]
}
```

### Obtain all the accounts that follows a pattern (RegEx search) [QueryRegEx] ###

We will use the `/bovespa/company-account/search` endpoint to solve this request.

To do these kind of queries we will need the `regex` operator. The case sensitive or insensitive will depends on the field definition in the index, if we are applying a `<filter class="solr.LowercaseFilterFactory" />`.

Arguments:

- Query: `ccvm=15300`
- Restrictions: 
    - `period=2018-06-30T00:00:00Z`, 
    - `financial_info_type=INSTANT`, 
    - and `number__iregex=1.01.(.*).01(.*)`
- Sort results: `order_by=number`

After [obtain our user Token](https://github.com/buildgroupai/django-caravaggio-rest-api/blob/master/docs/local_environment.md#run-application-with-development-server), we can execute the following instruction:

```
$ curl -H 'Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b' \
    -X GET "http://localhost:8001/bovespa/company-account/search/?period=2018-06-30T00:00:00Z&ccvm=15300&balance_type=ASSETS&financial_info_type=INSTANT&number__iregex=1.01.(.*).01(.*)&order_by=number"
```

or in python after executing `python manage.py shell` in the base 
dir of the project

```python
from datetime import datetime
from caravaggio_rest_api.haystack.backends.utils import CaravaggioSearchPaginator
from davinci_crawling.example import BovespaAccount
from solrq import Q, Value

ccvm = "15300"
period = datetime.strptime("2018-06-30", "%Y-%m-%d")

filter = Q(period=period) & Q(ccvm=ccvm) & \
    Q(balance_type="ASSETS") & Q(financial_info_type="INSTANT") & \
    Q(number= Value("/1.01.(.*).01(.*)/", safe=True))

# In Caravaggio, fields marked as facets are indexed twice. One first time a 
# field with the same name will be indexed without being marked as docValues 
# that will allow us do free text searches on its content. And other field 
# renamed to <field_name>_exact being marked as docValues that will optimize 
# the process process of sorting and faceting using the field. The field 
# marked as docValues (_exact) will be the field we use when sorting. If 
# not, we are going to get the following exception
#
# Exception: Field cache is disabled, set the field=number to be 
#   docValues=true and reindex.  Or if the field cache will not exceed 
#   the heap usage, then place useFieldCache=true in the request parameters.
#
paginator = CaravaggioSearchPaginator(
    query_string=str(filter),
    sort='number_exact asc',
    limit=5000, max_limit=5000). \
    models(BovespaAccount). \
    select("version", "number", "name",
           "financial_info_type", "balance_type", "comments",
           "amount")

# Iterate through the results
while paginator.has_next():
    paginator.next()
    for account in paginator.get_results():
        print(account.version, account.number, 
              account.name, account.comments,
              account.financial_info_type, account.balance_type,
              account.amount)
```


And the result will be something like: (it shows 10 of the 36 accounts available for the period)

```json5
{
  "total": 12,
  "page": 10,
  "next": "http://localhost:8001/bovespa/company-account/search/?balance_type=ASSETS&ccvm=15300&financial_info_type=INSTANT&number__iregex=1.01.%28.%2A%29.01%28.%2A%29&order_by=number&page=2&period=2018-06-30T00%3A00%3A00Z",
  "previous": null,
  "results": [
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Aplicações Financeiras Avaliadas a Valor Justo através do Resultado",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.754000",
      "updated_at": "2018-11-26T22:57:30.754000",
      "score": 12.044513
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.01.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Títulos para Negociação",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.758000",
      "updated_at": "2018-11-26T22:57:30.758000",
      "score": 12.044513
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.01.02",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Títulos Designados a Valor Justo",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.762000",
      "updated_at": "2018-11-26T22:57:30.762000",
      "score": 12.044513
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.01.03",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Caixa restrito",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.778000",
      "updated_at": "2018-11-26T22:57:30.779000",
      "score": 12.044513
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.02.02.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Títulos Mantidos até o Vencimento",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.797000",
      "updated_at": "2018-11-26T22:57:30.797000",
      "score": 12.044513
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.03.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Clientes",
      "value": 194127.0,
      "created_at": "2018-11-26T22:57:30.811000",
      "updated_at": "2018-11-26T22:57:30.812000",
      "score": 12.044513
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.03.02.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Adiantamentos a fornecedores",
      "value": 0.0,
      "created_at": "2018-11-26T22:57:30.822000",
      "updated_at": "2018-11-26T22:57:30.822000",
      "score": 12.044513
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.06.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Tributos Correntes a Recuperar",
      "value": 101872.0,
      "created_at": "2018-11-26T22:57:30.847000",
      "updated_at": "2018-11-26T22:57:30.848000",
      "score": 12.044513
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.06.01.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Imposto de renda e contribuição social a recuperar",
      "value": 21123.0,
      "created_at": "2018-11-26T22:57:30.853000",
      "updated_at": "2018-11-26T22:57:30.853000",
      "score": 12.044513
    },
    {
      "ccvm": "15300",
      "period": "2018-06-30",
      "number": "1.01.06.01.02",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Outros tributos a recuperar",
      "value": 80749.0,
      "created_at": "2018-11-26T22:57:30.858000",
      "updated_at": "2018-11-26T22:57:30.858000",
      "score": 12.044513
    }
  ]
}
```
 
### Obtain all the new accounts keyed into the system after a specific date [QueryDate]

To solve this query we use the API endpoint `/bovespa/company-acccount/search`

Arguments:

- Query: `updated_at__gte=2018-11-20T00:00:00Z`
- Sort results: `updated_at`

After [obtain our user Token](https://github.com/buildgroupai/django-caravaggio-rest-api/blob/master/docs/local_environment.md#run-application-with-development-server), we can execute the following instruction:

```
$ curl -H 'Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b' \
    -X GET "http://localhost:8001/bovespa/company-account/search/?updated_at__gte=2018-11-20T00:00:00Z&order_by=updated_at"
```

or in python after executing `python manage.py shell` in the base 
dir of the project


```python
from datetime import datetime
from caravaggio_rest_api.haystack.backends.utils import CaravaggioSearchPaginator
from davinci_crawling.example import BovespaAccount
from solrq import Q, Value, Range

ccvm = "15300"
period = datetime.strptime("2019-09-20 07:07:00", "%Y-%m-%d %H:%M:%S")

filter = Q(updated_at=Range(Value(period), '*', safe=True, boundaries="[]")) 

# In Caravaggio, fields marked as facets are indexed twice. One first time a 
# field with the same name will be indexed without being marked as docValues 
# that will allow us do free text searches on its content. And other field 
# renamed to <field_name>_exact being marked as docValues that will optimize 
# the process process of sorting and faceting using the field. The field 
# marked as docValues (_exact) will be the field we use when sorting. If 
# not, we are going to get the following exception
#
# Exception: Field cache is disabled, set the field=number to be 
#   docValues=true and reindex.  Or if the field cache will not exceed 
#   the heap usage, then place useFieldCache=true in the request parameters.
#
paginator = CaravaggioSearchPaginator(
    query_string=str(filter),
    sort='updated_at desc',
    limit=5000, max_limit=5000). \
    models(BovespaAccount). \
    select("version", "number", "name",
           "financial_info_type", "balance_type", "comments",
           "amount")

# Iterate through the results
while paginator.has_next():
    paginator.next()
    for account in paginator.get_results():
        print(account.version, account.number, 
              account.name, account.comments,
              account.financial_info_type, account.balance_type,
              account.amount)
```


And the result will be something like: (it shows 10 of the 2249174 of new accounts entered into the system)

```json5
{
  "total": 2249174,
  "page": 10,
  "next": "http://localhost:8001/bovespa/company-account/search/?order_by=updated_at&page=2&updated_at__gte=2018-11-20T00%3A00%3A00Z",
  "previous": null,
  "results": [
    {
      "ccvm": "16225",
      "period": "2015-09-30",
      "number": "1.89.01",
      "financial_info_type": "DURATION",
      "balance_type": "IF",
      "name": "QuantidadeAcaoOrdinariaCapitalIntegralizado",
      "value": 1.0,
      "created_at": "2018-11-21T01:07:55.252000",
      "updated_at": "2018-11-21T01:07:55.253000",
      "score": 10.552604
    },
    {
      "ccvm": "16225",
      "period": "2015-09-30",
      "number": "1.89.02",
      "financial_info_type": "DURATION",
      "balance_type": "IF",
      "name": "QuantidadeAcaoPreferencialCapitalIntegralizado",
      "value": 0.0,
      "created_at": "2018-11-21T01:07:55.266000",
      "updated_at": "2018-11-21T01:07:55.266000",
      "score": 10.552604
    },
    {
      "ccvm": "16225",
      "period": "2015-09-30",
      "number": "1.89.03",
      "financial_info_type": "DURATION",
      "balance_type": "IF",
      "name": "QuantidadeTotalAcaoCapitalIntegralizado",
      "value": 1.0,
      "created_at": "2018-11-21T01:07:55.274000",
      "updated_at": "2018-11-21T01:07:55.274000",
      "score": 10.552604
    },
    {
      "ccvm": "16225",
      "period": "2015-09-30",
      "number": "1.89.04",
      "financial_info_type": "DURATION",
      "balance_type": "IF",
      "name": "QuantidadeAcaoOrdinariaTesouraria",
      "value": 0.0,
      "created_at": "2018-11-21T01:07:55.283000",
      "updated_at": "2018-11-21T01:07:55.283000",
      "score": 10.552604
    },
    {
      "ccvm": "16225",
      "period": "2015-09-30",
      "number": "1.89.05",
      "financial_info_type": "DURATION",
      "balance_type": "IF",
      "name": "QuantidadeAcaoPreferencialTesouraria",
      "value": 0.0,
      "created_at": "2018-11-21T01:07:55.291000",
      "updated_at": "2018-11-21T01:07:55.291000",
      "score": 10.552604
    },
    {
      "ccvm": "16225",
      "period": "2015-09-30",
      "number": "1.89.06",
      "financial_info_type": "DURATION",
      "balance_type": "IF",
      "name": "QuantidadeTotalAcaoTesouraria",
      "value": 0.0,
      "created_at": "2018-11-21T01:07:55.299000",
      "updated_at": "2018-11-21T01:07:55.300000",
      "score": 10.552604
    },
    {
      "ccvm": "16225",
      "period": "2015-09-30",
      "number": "1",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Ativo Total",
      "value": 1644.0,
      "created_at": "2018-11-21T01:08:03.881000",
      "updated_at": "2018-11-21T01:08:03.881000",
      "score": 10.552604
    },
    {
      "ccvm": "16225",
      "period": "2015-09-30",
      "number": "1.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Ativo Circulante",
      "value": 118.0,
      "created_at": "2018-11-21T01:08:04.387000",
      "updated_at": "2018-11-21T01:08:04.387000",
      "score": 10.552604
    },
    {
      "ccvm": "16225",
      "period": "2015-09-30",
      "number": "1.01.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Caixa e Equivalentes de Caixa",
      "value": 1.0,
      "created_at": "2018-11-21T01:08:04.395000",
      "updated_at": "2018-11-21T01:08:04.395000",
      "score": 10.552604
    },
    {
      "ccvm": "16225",
      "period": "2015-09-30",
      "number": "1.01.01.01",
      "financial_info_type": "INSTANT",
      "balance_type": "ASSETS",
      "name": "Depósitos Bancários",
      "value": 1.0,
      "created_at": "2018-11-21T01:08:04.403000",
      "updated_at": "2018-11-21T01:08:04.403000",
      "score": 10.552604
    }
  ]
}
```


### Get the latest version of a delivered file closest (not included) a given fiscal date [QueryLastVersion]

To solve this query we can use the API endpoint `/bovespa/company-file/search`.

Arguments:

- Query: `status=processed`
- Restrictions: `ccvm=15300` and `fiscal_date__lte=2018-08-30T00:00:00Z`
- Sort results: `-fiscal_date,-version`
- Return the first result: `limit=1`

After [obtain our user Token](https://github.com/buildgroupai/django-caravaggio-rest-api/blob/master/docs/local_environment.md#run-application-with-development-server), we can execute the following instruction:

```
$ curl -H 'Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b' \
    -X GET "http://localhost:8001/bovespa/company-file/search/?status=processed&ccvm=15300&order_by=-fiscal_date,-version&&fiscal_date__lt=2018-08-30T00:00:00Z&limit=1" 
```

or in python after executing `python manage.py shell` in the base 
dir of the project


```python
from datetime import datetime
from caravaggio_rest_api.haystack.backends.utils import CaravaggioSearchPaginator
from davinci_crawling.example import BovespaCompanyFile
from solrq import Q, Range

ccvm = "15300"
fiscal_date = datetime.strptime("2018-08-30", "%Y-%m-%d")

filter = Q(ccvm=ccvm) & \
         Q(status='processed') & \
         Q(fiscal_date=Range('*', fiscal_date, safe=True, boundaries='[}')) 

# In Caravaggio, fields marked as facets are indexed twice. One first time a 
# field with the same name will be indexed without being marked as docValues 
# that will allow us do free text searches on its content. And other field 
# renamed to <field_name>_exact being marked as docValues that will optimize 
# the process process of sorting and faceting using the field. The field 
# marked as docValues (_exact) will be the field we use when sorting. If 
# not, we are going to get the following exception
#
# Exception: Field cache is disabled, set the field=number to be 
#   docValues=true and reindex.  Or if the field cache will not exceed 
#   the heap usage, then place useFieldCache=true in the request parameters.
#
paginator = CaravaggioSearchPaginator(
    query_string=str(filter),
    sort='fiscal_date desc, version_exact desc',
    limit=1). \
    models(BovespaCompanyFile). \
    select("doc_type", "fiscal_date", "created_at",
           "company_name", "company_cnpj",
           "file_url")

# Iterate through the results
while paginator.has_next():
    paginator.next()
    for file in paginator.get_results():
        print(file.doc_type, file.fiscal_date, 
              file.created_at, file.company_name,
              file.company_cnpj, file.file_url)
```


The results will be something like:

```json5
{
  "total": 27,
  "page": 1,
  "next": "http://localhost:8001/bovespa/company-file/search/?ccvm=15300&fiscal_date__lte=2018-08-30T00%3A00%3A00Z&limit=1&order_by=-fiscal_date%2C-version&page=2&status=processed",
  "previous": null,
  "results": [
    {
      "ccvm": "15300",
      "doc_type": "ITR",
      "fiscal_date": "2018-06-30",
      "version": "2.0",
      "status": "processed",
      "created_at": "2018-11-14T16:11:33.775000",
      "updated_at": "2018-11-26T22:57:35.932000",
      "protocol": "76980",
      "delivery_date": "2018-08-13T00:00:00",
      "delivery_type": "Reapresentação Espontânea",
      "company_name": "ALL - AMÉRICA LATINA LOGÍSTICA MALHA NORTE S.A.",
      "company_cnpj": "não informado",
      "fiscal_date_y": 2018,
      "fiscal_date_yd": 181,
      "fiscal_date_q": 2,
      "fiscal_date_m": 6,
      "fiscal_date_md": 30,
      "fiscal_date_w": 26,
      "fiscal_date_wd": 5,
      "fiscal_date_yq": "2018-Q2",
      "fiscal_date_ym": "2018-06",
      "source_url": "http://www.rad.cvm.gov.br/enetconsulta/frmDownloadDocumento.aspx?CodigoInstituicao=1&NumeroSequencialDocumento=76980",
      "file_url": "gs://vanggogh2_harvest/bovespa/ccvm_15300/ITR/date_20180630_2_0/01530020180630302.zip",
      "file_name": "01530020180630302.zip",
      "file_extension": "zip",
      "score": 5.373686
    }
  ]
}
``` 

### Obtain the list of the latest versions of all documents delivered by the company 15300 that have been already processed [QueryGroupLast]

To solve this query we need to make use of the Solr `groups` feature, something not supported yet by the RESTful API.

We can use the Solr service directly (Ex. `http://127.0.0.1:8983/solr/davinci.bovespa_company_file/select`)

Arguments:

- Query: `q=status:processed`
- Restrictions: `fq=ccvm:15300`
- Sort results: `sort=fiscal_date asc,version desc`
- Return 0-50 resultats: `start:0&rows:50`
- Fields of interest: `fl=doc_type,fiscal_date,version`
- Group the results per fiscal date: `group=true&group.field=fiscal_date`
- We are only interested in the first result of each group: `group.limit=1`

Final url:

```
curl -X GET "http://127.0.0.1:8983/solr/davinci.bovespa_company_file/select?q=status:processed&fq=ccvm:15300&sort=version_exact+desc&start=0&rows=50&fl=doc_type,fiscal_date,version&group=true&group.field=fiscal_date&group.limit=1&wt=json&indent=true"
``` 

or in python after executing `python manage.py shell` in the base 
dir of the project


```python
from datetime import datetime
from caravaggio_rest_api.haystack.backends.utils import CaravaggioSearchPaginator
from davinci_crawling.example import BovespaCompanyFile
from solrq import Q, Value, Range

ccvm = "15300"
fiscal_date = datetime.strptime("2018-08-30", "%Y-%m-%d")

filter = Q(ccvm=ccvm) & \
         Q(status='processed') & \
         Q(fiscal_date=
            Range('*', Value(fiscal_date), safe=True, boundaries='[}')) 

# In Caravaggio, fields marked as facets are indexed twice. One first time a 
# field with the same name will be indexed without being marked as docValues 
# that will allow us do free text searches on its content. And other field 
# renamed to <field_name>_exact being marked as docValues that will optimize 
# the process process of sorting and faceting using the field. The field 
# marked as docValues (_exact) will be the field we use when sorting. If 
# not, we are going to get the following exception
#
# Exception: Field cache is disabled, set the field=number to be 
#   docValues=true and reindex.  Or if the field cache will not exceed 
#   the heap usage, then place useFieldCache=true in the request parameters.
#
paginator = CaravaggioSearchPaginator(
    query_string=str(filter),
    sort='version_exact desc',
    rows=50,
    group='true',
    **{ 'group.field': 'fiscal_date',
        'group.limit': 1}). \
    models(BovespaCompanyFile). \
    select("doc_type", "fiscal_date", "version")

# Iterate through the results
num_files = 0
while paginator.has_next():
    paginator.next()    
    for group, files in paginator.get_results().items():
        print("Group: {}".format(group))
        for file in files:
            num_files += 1
            print("\t", file.doc_type, file.fiscal_date, file.version)

print("Total groups processed: {}".format(paginator.get_loaded_docs()))
print("Total files processed: {}".format(num_files))
```

The result of the query should something like this:

```json5
{
  "responseHeader":{
    "status":0,
    "QTime":149},
  "grouped":{
    "fiscal_date":{
      "matches":21,
      "groups":[{
          "groupValue":"2011-03-31T00:00:00Z",
          "doclist":{"numFound":3,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2011-03-31T00:00:00Z",
                "version":"3.0"}]
          }},
        {
          "groupValue":"2010-12-31T00:00:00Z",
          "doclist":{"numFound":2,"start":0,"docs":[
              {
                "doc_type":"DFP",
                "fiscal_date":"2010-12-31T00:00:00Z",
                "version":"2.0"}]
          }},
        {
          "groupValue":"2012-12-31T00:00:00Z",
          "doclist":{"numFound":2,"start":0,"docs":[
              {
                "doc_type":"DFP",
                "fiscal_date":"2012-12-31T00:00:00Z",
                "version":"2.0"}]
          }},
        {
          "groupValue":"2018-06-30T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2018-06-30T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2011-12-31T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"DFP",
                "fiscal_date":"2011-12-31T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2013-12-31T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"DFP",
                "fiscal_date":"2013-12-31T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2017-12-31T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"DFP",
                "fiscal_date":"2017-12-31T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2011-06-30T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2011-06-30T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2011-09-30T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2011-09-30T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2012-03-31T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2012-03-31T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2012-06-30T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2012-06-30T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2012-09-30T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2012-09-30T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2013-03-31T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2013-03-31T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2013-06-30T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2013-06-30T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2013-09-30T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2013-09-30T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2014-03-31T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2014-03-31T00:00:00Z",
                "version":"1.0"}]
          }},
        {
          "groupValue":"2014-06-30T00:00:00Z",
          "doclist":{"numFound":1,"start":0,"docs":[
              {
                "doc_type":"ITR",
                "fiscal_date":"2014-06-30T00:00:00Z",
                "version":"1.0"}]
          }}]}}}
```

## TODO

- Download the "Formulàrio Cadastral" from the B3 to obtain the Sector of Activity of the companies.

- Obtain/Crawl the Tickers/Symbols of each company.

- Obtain the historical stock prices. We can use "Yahoo Finance" and this [library](https://pypi.org/project/yahoo-finance/). 
