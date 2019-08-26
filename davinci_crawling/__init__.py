
r"""

   ___      _   ___         _   _____                ___
  / _ \___ | | / (____ ____(_) / __________ __    __/ (____ ___ _
 / // / _ `| |/ / / _ / __/ / / /__/ __/ _ `| |/|/ / / / _ / _ `/
/____/\_,_/|___/_/_//_\__/_/  \___/_/  \_,_/|__,__/_/_/_//_\_, /
                                                          /___/
"""

__title__ = 'Django DaVinci Crawling Framework'
__version__ = '0.1.3'
__author__ = 'Javier Alperte'
__license__ = 'MIT'
__copyright__ = 'Copyright (c) 2019 BuildGroup Data Services Inc.'

# Version synonym
VERSION = __version__

# Header encoding (see RFC5987)
HTTP_HEADER_ENCODING = 'iso-8859-1'

# Default datetime input and output formats
ISO_8601 = 'iso-8601'

default_app_config = 'davinci_crawling.apps.DaVinciCrawlingConfig'
