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
from sickrage.helper.common import try_int
from sickrage.helper.common import convert_size
from sickrage.providers.ddl.DDLProvider import DDLProvider
from sickbeard.bs4_parser import BS4Parser

class DDLIslandProvider(DDLProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        DDLProvider.__init__(self, "DDLIsland")

        self.cache = tvcache.TVCache(self, min_time=0)  # Only poll DDLIsland every 10 minutes max

        self.urls = {'base_url': 'http://www.ddl-island.su',
                     'search': 'http://www.ddl-island.su/recherche.php?categorie=98&rechercher=Rechercher&fastr_type=ddl&find=',
                     'rss': 'http://www.ddl-island.su'}

        self.url = self.urls['base_url']

        self.headers.update({'User-Agent': USER_AGENT})

        self.storageProviderAllow = {}

    def canUseProvider(self, data):
        for key,value in self.storageProviderAllow.items():
            if key.lower() == data.lower() and value:
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
                    logger.log(search_url+search_string_for_url, logger.DEBUG) #JO

                    dataSearch = self.get_url(search_url+search_string_for_url, post_data=data)
                    if not dataSearch:
                        continue

                    with BS4Parser(dataSearch, 'html5lib') as html:
                        serie_rows = html(class_=re.compile('fiche_listing'))

                        for result_rows in serie_rows:
                            try:
                                links_page = result_rows.find_all('a')
                                logger.log(links_page[1].get('href'), logger.DEBUG)
                               
                                NameDetect = links_page[1].get_text()
                                logger.log(NameDetect, logger.DEBUG) #JO
                                if not NameDetect.find(search_string_for_url) >= 0:
                                    continue

                                if not NameDetect.find("Saison "+str(int(seasonVersion))) >= 0:
                                    continue

                                dataPage = self.get_url(links_page[1].get('href').replace('.html',''), verify=False)
                                with BS4Parser(dataPage, 'html5lib') as htmlPage:
                                    url = links_page[1].get('href').replace('.html','')
                                    title = ""
                                    
                                    content_page = htmlPage.findAll('div', id=re.compile('alllinks'))
                                    bTags = content_page[0].find_all('li')
                                    for bTag in bTags:
                                        providerDDLName = ""
                                        title = bTag.text.split(' : ')[1]

                                        if self.canUseProvider(bTag.find_all('span')[0].find_all('span')[0]['title']):
                                            providerDDLName = bTag.find_all('span')[0].find_all('span')[0]['title'] 

                                        if  self.canUseProvider(providerDDLName) and \
                                                title.find(search_string.rsplit(' ',1)[1]) >= 0:
                                            providerDDLLink = bTag.find_all('a')[0]['href']
                                            logger.log(providerDDLName, logger.DEBUG)
                                            logger.log(title, logger.DEBUG)
                                            logger.log(providerDDLLink, logger.DEBUG)

                                            item = {'title': title, 'link': providerDDLLink}
                                            items.append(item)
                                            providerDDLName = ""

                            except Exception:
                                logger.log(u'Failed doing webui callback: {0}'.format((traceback.format_exc())), logger.ERROR)
            results += items

        return results

provider = DDLIslandProvider()
