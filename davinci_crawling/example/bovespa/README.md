# Bovespa Crawler


## Introduction

The B3 (in full, B3 - Brasil Bolsa Balcão S.A. or B3 - Brazil, Stock Exchange and Over-the-Counter Market), formerly BM&FBOVESPA, is a Stock Exchange located at São Paulo, Brazil and the second oldest of the country

This crawler will allow us to download the 

http://siteempresas.bovespa.com.br/consbov/ExibeTodosDocumentosCVM.asp?CNPJ=&CCVM=9512&TipoDoc=C&QtLinks=1000
http://www.cvm.gov.br/menu/regulados/companhias/download_multiplo/manual_tecnico.html
http://sistemas.cvm.gov.br/port/ciasabertas/dado_110.asp


Pending:

- Obtain the tickers of each company

    http://www.b3.com.br/en_us/market-data-and-indices/indices/stocks-per-index/

        ON: açoes ordinárias nominativas. Sempre 3
        PN: açoes preferenciais nominativas. Pode ser 4->A, 5->B ou 6->C, e mais. Cada nivel pode ter seus própios direitos e restriçoes (% de dividendos, etc)

        Ex. Lojas Americanas. LAME3 -> ON, LAME4 -> PN

- Industry classification for the companies (Yahoo)
- Historical stock prices (Yahoo)

    https://www.investopedia.com/markets/api/partial/historical/?Symbol=LAME4.SA&Type=%20Historical+Prices&Timeframe=Daily&StartDate=Nov+28%2C+2017&EndDate=Dec+05%2C+2017

- Compute basic indicators
- Compute Market Cap. (shares outstanding * share price)

## Advanced Solr queries

### Obtain the list of the latest versions of all documents delivered by the company 15300 that have been already processed

Arguments:

- Query: `q=status:processed`
- Restrictions: `fq=ccvm:15300`
- Sort results: `sort=fiscal_date asc,version desc`
- Return 0-50 resultats: `start:&rows:50`
- Fields of interest: `fl=doc_type,fiscal_date,version`
- Group the results per fiscal date: `group=true&group.field=fiscal_date`
- We are only interested in the first result of each group: `group.limit=1`

Final url:

```
curl -X GET "http://127.0.0.1:8983/solr/davinci.bovespa_company_file/select?q=status:processed&fq=ccvm:15300&sort=version_exact+desc&start=0&rows=50&fl=doc_type,fiscal_date,version&group=true&group.field=fiscal_date&group.limit=1&wt=json&indent=true"
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