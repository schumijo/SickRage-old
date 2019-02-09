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
import cfscrape

from sickbeard import helpers, logger, tvcache
from sickbeard.common import USER_AGENT
from sickrage.helper.common import try_int
from sickrage.helper.common import convert_size
from sickrage.providers.ddl.DDLProvider import DDLProvider
from sickbeard.bs4_parser import BS4Parser

class SeriesCRProvider(DDLProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        DDLProvider.__init__(self, "SeriesCR")

        self.cache = tvcache.TVCache(self, min_time=0)  # Only poll SeriesCR every 10 minutes max

        self.urls = {'base_url': 'https://www.seriescr.com',
                     'search': 'https://www.seriescr.com/?s=',
                     'rss': 'https://www.seriescr.com'}

        self.url = self.urls['base_url']

        self.headers.update({'User-Agent': USER_AGENT})

        self.storageProviderAllow = {}
        
        self.titleVersion = {
            'vo': {
                'keywords': ["hdtv"],
                'suffix': 'SDTV'
            },
            'vostfr-hd': {
                'keywords': ["720p","hdtv","x264"],
                'suffix': '720P.HDTV.x264'
            },
            'vostfr-hd-x265': {
                'keywords': ["720p","hdtv","x265"],
                'suffix': '720P.HDTV.x265'
            },
            'vostfr-1080p': {
                'keywords': ["1080p","x265"],
                'suffix': '1080P.HDTV.x265'
            }
        }


    def getTitleVersion(self, x):
        return titleVersion.get(x, '')

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
                for search_url in search_urlS:

                    data = {}
                    sessionSearch = cfscrape.create_scraper()
                    dataSearch = sessionSearch.get(search_url+search_string).content

                    if not dataSearch:
                        continue

                    with BS4Parser(dataSearch, 'html5lib') as html:
                        serie_rows = html(class_=re.compile('entry-title'))

                        for result_rows in serie_rows:
                            try:
                                links_page = result_rows.find_all('a')
                                logger.log(links_page[0].get('href'), logger.DEBUG)
                                
                                sessionPage = cfscrape.create_scraper()
                                dataPage = sessionPage.get(links_page[0].get('href')).content
                                with BS4Parser(dataPage, 'html5lib') as htmlPage:
                                    url = links_page[0].get('href')
                                    title = ""
                                    
                                    content_page = htmlPage(class_=re.compile('description'))
                                    bDesc = content_page[1].find_all('div')
                                    content_page = htmlPage(class_=re.compile('more'))
                                    bMore = content_page[0].find_all('div')
                                    bTags = bDesc + bMore
                                    bTags = bTags[:-2]
                                    i=1
                                    for bTag in bTags:
                                        if i%4 == 1:
                                            quality = bTag.find_all('strong')
                                            quality = quality[0].text.lower()

                                            for key, tv in self.titleVersion.items():
                                                if all(keyword in quality for keyword in tv["keywords"]):
                                                    title = search_string.replace(" ",".") +"."+ tv["suffix"]
                                                    break;

                                        if i%4 == 3:
                                            bLinks = bTag.find_all('a')
                                            providerDDLName = ""
                                            for bLink in bLinks:
                                                providerDDLName = bLink.get_text().capitalize()
                                                if self.canUseProvider(providerDDLName):
                                                    providerDDLLink = bLink.get('href')
                                                    logger.log("Provider : "+providerDDLName, logger.DEBUG)
                                                    logger.log("Title : "+title, logger.DEBUG)
                                                    logger.log("Link : "+providerDDLLink, logger.DEBUG)

                                                    item = {'title': title, 'link': providerDDLLink}
                                                    items.append(item)
                                                    providerDDLName = ""
                                        i += 1

                            except Exception:
                                logger.log(u'Failed doing webui callback: {0}'.format((traceback.format_exc())), logger.ERROR)
            results += items

        return results

provider = SeriesCRProvider()
