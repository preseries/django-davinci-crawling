# -*- coding: utf-8 -*-
# Copyright (c) 2018-2019 PreSeries Tech, SL

from davinci_crawling.time import mk_datetime

ERRORS = {
    "22014": "Invalid date",
    "22015": "Invalid hour",
    "22016": "No record found",
    "22017": "Invalid document type",

    "22013": "Internal error generating the XML",

    "1": "Incorrect login"
}


class BovespaError(Exception):
    """
    <?xml version="1.0" encoding="ISO-8859-1" ?>
    <ERROS DataSolicitada="19/02/2016 00:01" TipoDocumento="ITR" 
            DataConsulta="23/07/2018 15:30">
        <NUMERO_DO_ERRO>22016</NUMERO_DO_ERRO>
        <DESCRICAO_DO_ERRO>Nenhum registro localizado.</DESCRICAO_DO_ERRO>
        <FONTE_DO_ERRO>RetornaXMLDonwloadMultiplo</FONTE_DO_ERRO>
    </ERROS>
    """
    requested_date = None
    doc_type = None
    request_date = None

    error_code = None
    error_source = None

    def __init__(self, obj):
        self.doc_type = obj.ERROS["TipoDocumento"]
        self.requested_date = mk_datetime(obj.ERROS["DataSolicitada"])
        self.request_date = mk_datetime(obj.ERROS["DataConsulta"])

        self.error_code = obj.ERROS.NUMERO_DO_ERRO.cdata
        self.error_source = obj.ERROS.FONTE_DO_ERRO.cdata

        self.message = ERRORS.get(self.error_code, "Unknown")

    def __str__(self):
        return "{error: %s, message: %s, source: %s, " \
               "doc: %s, request_date: %s, " \
               "requested_date: %s" % \
               (self.error_code, self.message,
                self.error_source, self.doc_type,
                self.request_date, self.requested_date)


class DownloadError(Exception):
    """
    This exception signals when a download wasn't successful
    
    It contains the reference to the related Doc
    """

    doc = None

    def __init__(self, doc):
        self.doc = doc
