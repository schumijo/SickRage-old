# coding=utf-8
# Author: djoole <bobby.djoole@gmail.com>
#
# URL: https://sickrage.github.io
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage. If not, see <http://www.gnu.org/licenses/>.

import time
import traceback
import re

from sickbeard import logger, tvcache
from sickbeard.common import USER_AGENT
from sickchill.helper.common import try_int
from sickchill.helper.common import convert_size
from sickchill.providers.ddl.DDLProvider import DDLProvider
from sickbeard.bs4_parser import BS4Parser

class GrabTheBeastProvider(DDLProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        DDLProvider.__init__(self, "GrabTheBeast")

        self.cache = tvcache.TVCache(self, min_time=0)  # Only poll ZoneTelechargement every 10 minutes max

        self.urls = {'base_url': 'https://grabthebeast.com/stream/',
                     'search': 'https://grabthebeast.com/search/',
                     'rss': 'https://grabthebeast.com/'}

        self.url = self.urls['base_url']

        self.headers.update({'User-Agent': USER_AGENT})

        self.storageProviderAllow = {}


        self.titleVersion = {
            'vostfr': {
                'keywords': ["vostfr", "hdtv"],
                'suffix': 'VOSTFR.HDTV'
            },
            'vf': {
                'keywords': ["french", "hdtv"],
                'suffix': 'FRENCH.HDTV'
            },
            'vostfr-hd': {
                'keywords': ["720p","vostfr"],
                'suffix': 'VOSTFR.720P.HDTV.x264'
            },
            'vf-hd': {
                'keywords': ["french", "720p"],
                'suffix': 'FRENCH.720P.HDTV.x264'
            },
            'vostfr-1080p': {
                'keywords': ["vostfr", "hd1080p"],
                'suffix': 'VOSTFR.1080P.HDTV.x264'
            },
            'vf-1080p': {
                'keywords': ["french", "hd1080p"],
                'suffix': 'FRENCH.1080P.HDTV.x264'
            }
        }

    def canUseProvider(self, data):
        for key,value in self.storageProviderAllow.items():
            if key == data and value:
                return True
        return False


    def search(self, search_params, age=0, ep_obj=None):  # pylint: disable=too-many-branches, too-many-locals, too-many-statements
        results = []

        for mode in search_params:
            # Don't support RSS
            if mode == 'RSS':
                continue

            items = []

            logger.log(u"Search Mode: {0}".format(mode), logger.DEBUG)

            for search_string in search_params[mode]:

                detectSeasonEpisode = re.search('(\d{1,2})[^\d]{1,2}(\d{1,2})(?:[^\d]{1,2}(\d{1,2}))?.*', search_string)
                seasonVersion = detectSeasonEpisode.group(1)
                episodeVersion = detectSeasonEpisode.group(2)

                search_string_for_url = search_string.replace(search_string.split(" ")[-1],"")

                logger.log(u"Search string: {0}".format
                           (search_string.decode("utf-8")), logger.DEBUG)

                logger.log(u"search_string_for_url: {0}".format
                           (search_string_for_url.decode("utf-8")), logger.DEBUG)

                search_urlS = [self.urls['search']]
                base_url = [self.urls['base_url']][0]

                for search_url in search_urlS:

                    data = {}

                    dataSearch = self.get_url(search_url+search_string_for_url)
                    if not dataSearch:
                        continue

                    with BS4Parser(dataSearch, 'html5lib') as html:
                        serie_rows = html(class_=re.compile('search_about'))

                        for result_rows in serie_rows:
                            try:
                                link_page = result_rows.find_all('a')[0].get('href')
                                show_id = link_page.split("/")[-1]
                                logger.log("Show ID : "+show_id, logger.DEBUG)

                                link_dl = base_url+show_id+'/season/'+seasonVersion+'/episode/'+episodeVersion
                                dataPage = self.get_url(link_dl, verify=False)
                                with BS4Parser(dataPage, 'html5lib') as htmlPage:
                                    corps_page = htmlPage(class_=re.compile('grid'))
                                    if len(corps_page)<1:
                                        continue
                                    ddlLinks = corps_page[0].find_all('source')

                                    providerDDLName = ""
                                    for ddlLink in ddlLinks:
                                        providerDDLLink = ddlLink.get('src')
                                        title = providerDDLLink.split("/")[-1]
                                        #provider = providerDDLLink.split("/")[2]
                                        provider = "Agxz"

                                        if self.canUseProvider(provider):
                                            providerDDLName = provider
                                            logger.log("Provider : "+providerDDLName, logger.DEBUG)
                                            logger.log("Title : "+title, logger.DEBUG)
                                            logger.log("Link : "+providerDDLLink, logger.DEBUG)

                                            item = {'title': title, 'link': providerDDLLink}
                                            items.append(item)
                                            providerDDLName = ""

                            except Exception:
                                logger.log(u'Failed doing webui callback: {0}'.format((traceback.format_exc())), logger.ERROR)
            results += items

        return results

provider = GrabTheBeastProvider()
