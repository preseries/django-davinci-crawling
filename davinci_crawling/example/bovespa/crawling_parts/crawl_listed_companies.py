# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL

import logging
import re
import itertools
import traceback

from dateutil.parser import parse as date_parse

from bs4 import BeautifulSoup

from multiprocessing.pool import Pool

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from davinci_crawling.example.bovespa import BOVESPA_CRAWLER
from davinci_crawling.example.bovespa.models import \
    BovespaCompany, SITUATION_CANCELLED, SITUATION_GRANTED
from davinci_crawling.crawling_throttle import Throttle
from davinci_crawling.utils import setup_cassandra_object_mapper

ALPHABET_LIST = list(map(chr, range(65, 91)))
NUMBERS_LIST = list(range(0, 10))

COMPANIES_LISTING_SEARCHER_LETTERS = ALPHABET_LIST + NUMBERS_LIST

COMPANIES_LISTING_URL = "http://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/CPublica/" \
                        "CiaAb/FormBuscaCiaAbOrdAlf.aspx?LetraInicial={}"

COMPANY_LETTERS_CTL = "ctl/listed_companies_letters.ctl"
COMPANIES_CTL = "ctl/listed_companies_companies.ctl"

_logger = logging.getLogger(
    "davinci_crawler_{}.crawling_part.listed_companies".
    format(BOVESPA_CRAWLER))


@Throttle(minutes=1, rate=50, max_tokens=50)
def update_listed_companies(letter, phantomjs_path):

    # We need to setup the Cassandra Object Mapper to work on multiprocessing
    # If we do not do that, the processes will be blocked when interacting
    # with the object mapper module
    setup_cassandra_object_mapper()

    driver = None
    try:
        _logger.debug("Crawling companies listing for letter: {}".
                      format(letter))

        companies = []
        driver = webdriver.PhantomJS(
            executable_path=phantomjs_path)

        url = COMPANIES_LISTING_URL.format(letter)
        _logger.debug("Crawling url: {}".format(url))

        # Let's navigate to the url and wait until the page is completely
        # loaded. We control that the page is loaded looking for the
        #  presence of the table with id = "dlCiasCdCVM"
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, 'dlCiasCdCVM')))
        except Exception as ex:
            WebDriverWait(driver, 10).until(
                EC.text_to_be_present_in_element(
                    (By.ID, 'lblMsg'),
                    "Nenhuma companhia foi encontrada com o critério de"
                    " busca especificado."))

            return companies

        bs = BeautifulSoup(driver.page_source, "html.parser")

        companies_table = bs.find("table", attrs={"id": "dlCiasCdCVM"})
        companies_rows = companies_table.findChildren(["tr"])

        # The first row is the header
        _logger.debug("Processing companies for letter [{0}]."
                      " Companies: {1}".
                      format(letter, len(companies_rows) - 1))

        for row in companies_rows[1:]:
            cells = row.findChildren('td')

            ccvm_code = cells[3].find("a").getText().strip()

            _logger.debug(
                "Check existance bovespa company: {}".format(ccvm_code))
            if not BovespaCompany.objects.filter(ccvm=ccvm_code).exists():
                _logger.debug(
                    "Bovespa company not found!: {}".format(ccvm_code))

                values = {
                    "ccvm": ccvm_code,
                    "company_name": cells[1].find("a").getText().strip(),
                    "cnpj": cells[0].find("a").getText().strip(),
                    "company_type": cells[2].find("a").getText(),
                }

                situation_text = cells[4].find("a").getText().strip()
                situation_date = re.search(
                    r".*(\d{2}/\d{2}/\d{4})", situation_text)[1]
                situation_date = date_parse(situation_date)

                if "cancelado" in situation_text.lower():
                    values.update({
                        "situation": SITUATION_CANCELLED,
                        "canceled_date": situation_date
                    })
                elif "concedido" in situation_text.lower():
                    values.update({
                        "situation": SITUATION_GRANTED,
                        "granted_date": situation_date
                    })

                _logger.debug("Create bovespa company: {}".format(values))
                companies.append(BovespaCompany.create(**values))
            else:
                _logger.debug(
                    "Get bovespa company from DB: {}".format(ccvm_code))
                companies.append(BovespaCompany.objects.get(ccvm=ccvm_code))

        return companies
    except Exception as ex:
        _logger.exception(
            "Unable to get, or crawl if it doesn't exists,"
            " the list of listed companies")
        raise ex
    finally:
        _logger.debug(
            "Finishing to crawl listed companies for letter {}".format(letter))
        if driver:
            _logger.debug(
                "Closing the PhantomJS driver for letter {}".format(letter))
            driver.quit()


def crawl_listed_companies(phantomjs_path, workers_num=10):

    companies = []

    pool = Pool(processes=workers_num)

    try:
        func_params = []
        for letter in COMPANIES_LISTING_SEARCHER_LETTERS:
            func_params.append([letter, phantomjs_path])

        call_results = pool.starmap(
                update_listed_companies, func_params)

        # Merge all the responses into one only list
        companies += list(
            itertools.chain.from_iterable(call_results))

        return companies
    except TimeoutError:
        print("Timeout error")
        traceback.print_exc()
        raise
    finally:
        pool.close()
        pool.join()
        pool.terminate()
