# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL

import logging
import re
import traceback

from multiprocessing.pool import Pool

from urllib.parse import urlencode

from caravaggio_rest_api.query import CaravaggioSearchQuerySet
from dateutil.parser import parse as date_parse

from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from davinci_crawling.example.bovespa import BOVESPA_CRAWLER
from davinci_crawling.example.bovespa.models import \
    BovespaCompany, BovespaCompanyFile, DOC_TYPES
from davinci_crawling.crawling_throttle import Throttle
from davinci_crawling.utils import setup_cassandra_object_mapper

try:
    from dse.cqlengine.query import LWTException
except ImportError:
    from cassandra.cqlengine.query import LWTException


RE_DOWNLOAD_FILE = r"javascript:fVisualizaArquivo_ENET\('([\d]+)','DOWNLOAD'\)"
RE_FISCAL_DATE = r'Data Encerramento.*[\s].*(\d{2}/\d{2}/\d{4})'
RE_DELIVERY_DATE = r'Data Entrega.*[\s].*(\d{2}/\d{2}/\d{4}) \d{2}:\d{2}'
RE_VERSION = r'Versão.*[\s].*(\d+.\d+)'
RE_DELIVERY_TYPE = r'Tipo Apresentação.*[\s].*<td.*>([\w\s]*)</td>'
RE_COMPANY_NAME = r'Razão Social.*:(.*)<br/>'
RE_CNPJ = r'CNPJ.*:(.*)\s'
RE_TOTAL_FILES = r'(\d*) documento\(s\) encontrado\(s\)'
RE_LAST_FILE_IN_PAGE = r'Exibindo (\d*) a (\d*)'

NEXT_PAGE_LINK_TEXT = "Próximos >>"

COMPANY_DOCUMENTS_URL = "http://siteempresas.bovespa.com.br/" \
                        "consbov/ExibeTodosDocumentosCVM.asp?{}"


DOWNLOAD_URL = "http://www.rad.cvm.gov.br/enetconsulta/" \
               "frmDownloadDocumento.aspx?CodigoInstituicao=1&" \
               "NumeroSequencialDocumento={protocol}"

_logger = logging.getLogger("davinci_crawler_{}.crawling_part.company_files".
                            format(BOVESPA_CRAWLER))


def extract_ENET_files_from_page(
        ccvm, driver, bs, doc_type, from_date=None):
    """
    Extract all the files to download from the listing HTML page

    :param driver: the panthomjs driver with the current page loaded. We use
                    the driver to navigate through the listing if needed
    :param bs: a BeautifulSoup object with the content of the listing page
    :return: a list of tuples with two components: the fiscal_period (date)
                and the protocol code for each file in the list
    """
    files = []

    # Extract the company name from the content
    company_name = re.search(RE_COMPANY_NAME, str(bs))[1].strip()

    # Extract the CNPJ from the content
    company_cnpj = re.search(RE_CNPJ, str(bs))[1].strip().lower()

    _logger.debug("Extracting files from {0} - {1}".
                  format(company_name, company_cnpj))

    # Get the number of files we should expect to find for the company
    try:
        num_of_docs = int(re.search(RE_TOTAL_FILES, str(bs))[1])
        _logger.debug("Total files {0}".format(num_of_docs))
    except:
        _logger.warning("There is no files information in the companies "
                        "files page for [{ccvm} - {doc_type}] ".
                        format(ccvm=ccvm, doc_type=doc_type))
        return files

    while True:
        # Get the number of files we can really get from the current page
        last_file_in_page = int(
            re.search(RE_LAST_FILE_IN_PAGE, str(bs))[2])
        _logger.debug("Last file in page: {0}".format(last_file_in_page))


        # Obtain the table elements that contains information about the
        # financial statements of the company we are interested in
        # ITR or DFP
        all_tables = [tag.findParent("table") for tag in
                      bs.find_all(
                          text=re.compile("{} - ENET".format(doc_type)))
                      if tag.findParent("table")]

        # For each table we extract the files information of all the files
        # that belongs to a fiscal period after the from_date argument.
        for table in all_tables:
            link_tag = table.find('a', href=re.compile(RE_DOWNLOAD_FILE))
            if link_tag:
                fiscal_date = re.search(RE_FISCAL_DATE,str(table))[1]
                fiscal_date = date_parse(fiscal_date)

                delivery_date = re.search(RE_DELIVERY_DATE, str(table))[1]
                delivery_date = date_parse(delivery_date)

                # We only continue processing files from the HTML page
                # if are newer (deliver after) than the from_date argument.
                # We look for newer delivery files
                if from_date is not None and delivery_date <= from_date:
                    break

                version = re.search(RE_VERSION, str(table))[1]

                delivery_type = re.search(RE_DELIVERY_TYPE, str(table))[1]

                protocol = re.match(
                    RE_DOWNLOAD_FILE, link_tag.attrs['href'])[1]

                source_url = DOWNLOAD_URL.format(protocol=protocol)

                company_file_data = {
                    "ccvm": ccvm,
                    "doc_type": doc_type,
                    "fiscal_date": fiscal_date,
                    "version": version,
                    "company_name": company_name,
                    "company_cnpj": company_cnpj,
                    "delivery_date": delivery_date,
                    "delivery_type": delivery_type,
                    "protocol": protocol,
                    "source_url": source_url
                }

                # We only create the company files if the file is not
                # already present in the system
                try:
                    BovespaCompanyFile. \
                        if_not_exists().\
                        create(**company_file_data)
                except LWTException as e:
                    _logger.warning(
                        "The company file [{ccvm} - '{name}' - {doc_type} - "
                        "{fiscal_date:%Y-%m-%d} - {version}]"
                        " cannot be created. The file already exists.".
                            format(ccvm=ccvm,
                                   name=company_name,
                                   doc_type=doc_type,
                                   fiscal_date=fiscal_date,
                                   version=version))
                    pass

                files.append(company_file_data)
            else:
                _logger.debug("The file is not available in ENET format")

        if last_file_in_page == num_of_docs:
            # We loaded all the files
            break
        else:
            # Navigate to the next page
            element = driver.find_element_by_link_text(NEXT_PAGE_LINK_TEXT)
            element.click()

            # Wait until the page is loaded
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//form[@name='AIR']/table/*")))

            bs = BeautifulSoup(driver.page_source, "html.parser")

    return files


@Throttle(minutes=1, rate=50, max_tokens=50)
def obtain_company_files(
        ccvm, phantomjs_path, doc_type, from_date=None):
    """
    This function is responsible for get the relation of files to be
    processed for the company and start its download

    This function is being throttle allowing 20 downloads per minute
    """

    # We need to setup the Cassandra Object Mapper to work on multiprocessing
    # If we do not do that, the processes will be blocked when interacting
    # with the object mapper module
    setup_cassandra_object_mapper()

    files = []
    driver = None

    try:
        driver = webdriver.PhantomJS(
            executable_path=phantomjs_path)

        encoded_args = urlencode(
            {'CCVM': ccvm, 'TipoDoc': 'C', 'QtLinks': "1000"})
        url = COMPANY_DOCUMENTS_URL.format(encoded_args)

        # Let's navigate to the url and wait until the reload is being done
        # We control that the page is loaded looking for an element with
        # id = "AIR" in the page
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'AIR')))
        except TimeoutException:
            WebDriverWait(driver, 10).until(
                EC.title_contains("CBLCNET -"))
            _logger.warning(
                "There is no documents page for company {ccvm} "
                "and {doc_type}. Showing 'Error de Aplicacao'".
                    format(ccvm=ccvm, doc_type=doc_type))
            return files

        # Once the page is ready, we can select the doc_type from the list
        # of documentation available and navigate to the results page
        # Select ITR files and Click
        element = driver.find_element_by_link_text(doc_type)
        element.click()

        # Wait until the page is loaded
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//form[@name='AIR']/table/*")))
        except TimeoutException:
            WebDriverWait(driver, 10).until(
                EC.title_contains("CBLCNET -"))
            _logger.warning(
                "There is no documents page for company {ccvm} "
                "and {doc_type}. Showing 'Error de Aplicacao'".
                    format(ccvm=ccvm, doc_type=doc_type))
            return files

        bs = BeautifulSoup(driver.page_source, "html.parser")

        # We extract the references to all the ENET files
        # The ENET files are ZIP files that contains textual document that
        # we can parse and extract information from them
        files = extract_ENET_files_from_page(
            ccvm, driver, bs, doc_type, from_date)

        return files
    except NoSuchElementException as ex:
        _logger.warning(
            "The company {ccvm} do not have {doc_type} documents".
            format(ccvm=ccvm, doc_type=doc_type))
        return []
    finally:
        _logger.debug(
            "Finishing to crawl company "
            "[{ccvm} - {doc_type}] files: [{num_files}]".
            format(ccvm=ccvm, doc_type=doc_type, num_files=len(files)))
        if driver:
            _logger.debug("Closing the phantomjs driver for company "
                          "[{ccvm} - {doc_type}]".
                          format(ccvm=ccvm, doc_type=doc_type))
            driver.quit()


def crawl_companies_files(
        phantomjs_path, workers_num=10,
        include_companies=None, from_date=None):

    companies_files = []
    pool = Pool(processes=workers_num)

    try:
        # Obtain the ccvm codes of all the listed companies
        ccvm_codes = [r.ccvm for r in
                      BovespaCompany.objects.
                          only(["ccvm"]).all()]

        ccvm_codes = sorted(ccvm_codes)

        _logger.debug(
            "Processing the files of {0} companies from {1}".
                format(len(ccvm_codes),
                       "{0:%Y-%m-%d}".format(from_date)
                       if from_date else "THE BEGINNING"))

        func_params = []
        for ccvm_code in ccvm_codes:
            if include_companies and ccvm_code not in include_companies:
                continue

            for doc_type in DOC_TYPES:
                func_params.append([
                    ccvm_code, phantomjs_path, doc_type, from_date])

        call_results = pool.starmap(obtain_company_files, func_params)

        # Merge all the responses into one only list
        # companies_files += list(
        #    itertools.chain.from_iterable(call_results))

    except TimeoutError:
        print("Timeout error")
        traceback.print_exc()
        raise
    finally:
        pool.close()
        pool.join()
        pool.terminate()
