# -*- coding: utf-8 -*-
# Copyright (c) 2019 BuildGroup Data Services Inc.

import logging
import json

import xmljson
from xml.etree.ElementTree import fromstring

from caravaggio_rest_api.utils import quarter

from davinci_crawling.example.bovespa import BOVESPA_CRAWLER
from davinci_crawling.example.bovespa.models import \
    DFP_BALANCE_IF, DFP_FINANCIAL_INFO_DURATION, \
    BALANCE_TYPES, FINANCIAL_INFO_TYPES, DFP_BALANCE_DMPL, DOC_TYPE_ITR, \
    DOC_TYPE_DFP, DFP_BALANCE_BPA, DFP_BALANCE_BPP, DFP_BALANCE_DFC_MD, \
    DFP_BALANCE_DFC_MI, DFP_BALANCE_DVA, BovespaAccount

RE_FILE_BY_ITR = r"^.*\.ITR"
RE_FILE_BY_XML = r"^.*\.XML"

FILE_DOCUMENT = "{doc_type}/Documento.xml"
FILE_CAPITAL_COMPOSITION = \
    "{doc_type}/ComposicaoCapitalSocialDemonstracaoFinanceiraNegocios.xml"
FILE_FINANCIAL_INFO = "{doc_type}/InfoFinaDFin.xml"

SHARES_NUMBER_ACCOUNTS = [
    ("1.89.01", "QuantidadeAcaoOrdinariaCapitalIntegralizado"),
    ("1.89.02", "QuantidadeAcaoPreferencialCapitalIntegralizado"),
    ("1.89.03", "QuantidadeTotalAcaoCapitalIntegralizado"),
    ("1.89.04", "QuantidadeAcaoOrdinariaTesouraria"),
    ("1.89.05", "QuantidadeAcaoPreferencialTesouraria"),
    ("1.89.06", "QuantidadeTotalAcaoTesouraria")
]

_logger = logging.getLogger("davinci_crawler_{}.document".
                            format(BOVESPA_CRAWLER))


def convert_xml_into_json(file):
    with open(file) as f:
        xml_content = f.read().replace("\n", "")
        return xmljson.badgerfish.data(fromstring(xml_content))


def get_scales(available_files, company_file):
    """
    Obtain the Metric Scale and Quantity of Shares from the Document.xml file

    Where to find the values:
        xmldoc.child("Documento").child_value("CodigoEscalaMoeda")
        xmldoc.child("Documento").child_value("CodigoEscalaQuantidade")

    :param available_files: list of available files per name
    :return: the money scale and quantity of shares
    """
    data = convert_xml_into_json(
        available_files[FILE_DOCUMENT.format(
            doc_type=company_file.doc_type.lower())])

    money_scale = int(data["Documento"]["CodigoEscalaMoeda"]["$"])
    quant_scale = int(data["Documento"]["CodigoEscalaQuantidade"]["$"])
    money_scale = 1999 - money_scale * 999
    quant_scale = 1999 - quant_scale * 999

    return money_scale, quant_scale


def get_sector(available_files, company_file):
    """
    Obtain the Sector Code from the Document.xml file

    Where to find the values:
        xmldoc.child("Documento").child_value(
            "CompanhiaAberta/CodigoSetorAtividadeEmpresa")

    :param available_files: list of available files per name
    :return: the code of the sector of the company
    """
    data = convert_xml_into_json(
        available_files[FILE_DOCUMENT.format(
            doc_type=company_file.doc_type.lower())])

    sector = int(
        data["Documento"][
            "CompanhiaAberta"][
            "CodigoSetorAtividadeEmpresa"]["$"])

    return sector


def get_cap_composition_accounts(sector, available_files, company_file):
    money_scale, quant_scale = get_scales(available_files, company_file)

    data = convert_xml_into_json(
        available_files[
            FILE_CAPITAL_COMPOSITION.
            format(doc_type=company_file.doc_type.lower())])

    accounts = []
    for acc_number, acc_name in SHARES_NUMBER_ACCOUNTS:
        account = {
            "ccvm": company_file.ccvm,
            "period": company_file.fiscal_date,
            "version": company_file.version,
            "balance_type": DFP_BALANCE_IF,
            "financial_info_type": DFP_FINANCIAL_INFO_DURATION,
            "number": acc_number,
            "name": acc_name,
            "sector": sector
        }

        equity = data["ArrayOfComposicaoCapitalSocialDemonstracaoFinanceira"][
            "ComposicaoCapitalSocialDemonstracaoFinanceira"]

        if isinstance(equity, (list, tuple)):
            value = int(equity[len(equity) - 1][
                acc_name]["$"])
        else:
            value = int(equity[acc_name]["$"])

        account["amount"] = int(value / quant_scale)
        account = BovespaAccount.create(**account)
        accounts.append(account)

    return accounts


def get_financial_info_accounts(sector, available_files, company_file):
    accounts = []

    money_scale, quant_scale = get_scales(available_files, company_file)

    data = convert_xml_into_json(
        available_files[
            FILE_FINANCIAL_INFO.
            format(doc_type=company_file.doc_type.lower())])

    for account_info in data["ArrayOfInfoFinaDFin"]["InfoFinaDFin"]:
        acc_version = account_info["PlanoConta"]["VersaoPlanoConta"]
        try:
            account = {
                "ccvm": company_file.ccvm,
                "period": company_file.fiscal_date,
                "version": company_file.version,
                "balance_type": BALANCE_TYPES[
                    int(acc_version["CodigoTipoDemonstracaoFinanceira"]["$"])],
                "financial_info_type": FINANCIAL_INFO_TYPES[
                    int(acc_version["CodigoTipoInformacaoFinanceira"][
                        "$"]) - 1],
                "number": str(account_info["PlanoConta"]["NumeroConta"]["$"]),
                "name": str(account_info["DescricaoConta1"]["$"]),
                "sector": sector
            }
        except KeyError as ex:
            _logger.exception(
                "Unable to found a field in account=[{}]".format(
                    json.dumps(account_info, sort_keys=True, indent=4)), ex)
            raise ex

        if account["balance_type"] == DFP_BALANCE_DMPL:
            period = account_info[
                "PeriodoDemonstracaoFinanceira"][
                "NumeroIdentificacaoPeriodo"]["$"]
            if (company_file.doc_type == DOC_TYPE_DFP and period != 1) or \
                    (company_file.doc_type == DOC_TYPE_ITR and period != 4):
                continue

            # Shares outstanding
            dmpl_account = dict(account)
            dmpl_account["comments"] = "Capital social integralizado"
            dmpl_account["amount"] = float(account_info["ValorConta1"]["$"])
            dmpl_account = BovespaAccount.create(**dmpl_account)
            accounts.append(dmpl_account)

            # Reserves
            dmpl_account = dict(account)
            dmpl_account["comments"] = "Reservas de capital"
            dmpl_account["amount"] = \
                float(account_info["ValorConta2"]["$"] / money_scale)
            dmpl_account = BovespaAccount.create(**dmpl_account)
            accounts.append(dmpl_account)

            # Revenue reserves
            dmpl_account = dict(account)
            dmpl_account["comments"] = "Reservas de lucro"
            dmpl_account["amount"] = \
                float(account_info["ValorConta3"]["$"] / money_scale)
            dmpl_account = BovespaAccount.create(**dmpl_account)
            accounts.append(dmpl_account)

            # Accrued Profit/Loss
            dmpl_account = dict(account)
            dmpl_account["comments"] = "Lucros/Prejuízos acumulados"
            dmpl_account["amount"] = \
                float(account_info["ValorConta4"]["$"] / money_scale)
            dmpl_account = BovespaAccount.create(**dmpl_account)
            accounts.append(dmpl_account)

            # Accumulated other comprehensive income
            dmpl_account = dict(account)
            dmpl_account["comments"] = "Outros resultados abrangentes"
            dmpl_account["amount"] = \
                float(account_info["ValorConta5"]["$"] / money_scale)
            dmpl_account = BovespaAccount.create(**dmpl_account)
            accounts.append(dmpl_account)

            # Stockholder's equity
            dmpl_account = dict(account)
            dmpl_account["comments"] = "Patrimônio Líquido"
            dmpl_account["amount"] = \
                float(account_info["ValorConta6"]["$"] / money_scale)
            dmpl_account = BovespaAccount.create(**dmpl_account)
            accounts.append(dmpl_account)
        else:
            if company_file.doc_type == DOC_TYPE_DFP:
                account["amount"] = \
                    float(account_info["ValorConta1"]["$"]) / money_scale
            elif company_file.doc_type == DOC_TYPE_ITR:
                # Profit and Los (ASSETS or LIABILITIES)
                if account["balance_type"] in [
                        DFP_BALANCE_BPA, DFP_BALANCE_BPP]:
                    account["amount"] = \
                        float(account_info["ValorConta2"]["$"]) / money_scale
                # Discounted Cash-flow (direct/indirect) and
                #   Value Added Demostration
                elif account["balance_type"] in [
                        DFP_BALANCE_DFC_MD,
                        DFP_BALANCE_DFC_MI,
                        DFP_BALANCE_DVA]:
                    account["amount"] = \
                        float(account_info["ValorConta4"]["$"]) / money_scale
                else:
                    q = quarter(account["period"].date())
                    if q == 1:
                        account["amount"] = \
                            float(account_info["ValorConta4"]["$"]) / \
                            money_scale
                    else:
                        account["amount"] = \
                            float(account_info["ValorConta2"]["$"]) / \
                            money_scale
            account = BovespaAccount.create(**account)
            accounts.append(account)

    return accounts


def load_account_details(options, available_files, company_file):

    sector = get_sector(available_files, company_file)
    accounts = get_cap_composition_accounts(
        sector, available_files, company_file)
    accounts.extend(get_financial_info_accounts(
        sector, available_files, company_file))

    return accounts
