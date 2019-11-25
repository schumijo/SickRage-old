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

class ZoneTelechargementProvider(DDLProvider):  # pylint: disable=too-many-instance-attributes

    def __init__(self):

        DDLProvider.__init__(self, "ZoneTelechargement")

        self.cache = tvcache.TVCache(self, min_time=0)  # Only poll ZoneTelechargement every 10 minutes max

        self.urls = {'base_url': 'https://www.zone-telechargement.net/',
                     'search': 'https://www.zone-telechargement.net/index.php?do=search&old=1&subaction=search&full_search=1&story=',
                     'rss': 'https://www.zone-telechargement.net/rss.xml'}

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
            'vf-webrip': {
                'keywords': ["french", "webrip"],
                'suffix': 'FRENCH.WEBRIP'
            },
            'vostfr-webdl': {
                'keywords': ["vostfr", "web-dl"],
                'suffix': 'VOSTFR.WEB-DL'
            },
            'vf-webdl': {
                'keywords': ["french", "web-dl"],
                'suffix': 'FRENCH.WEB-DL'
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
            },
            'multi-1080p': {
                'keywords': ["multi", "1080p"],
                'suffix': 'FRENCH.1080P.HDTV.x264'
            },
            'multi-webdl': {
                'keywords': ["multi", "720p"],
                'suffix': 'MULTI.720P.WEB-DL'
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
                    data["do"] = "search"
                    data["subaction"] = "search"
                    data["story"] = search_string_for_url
                    data["catlist[]"] = "15,16,17,18,19,20,21"

                    #dataSearch = self.get_url(search_url, post_data=data)
                    dataSearch = self.get_url(search_url+search_string_for_url)
                    if not dataSearch:
                        continue

                    with BS4Parser(dataSearch, 'html5lib') as html:
                        serie_rows = html(class_=re.compile('cover_infos_title'))

                        for result_rows in serie_rows:
                            try:
                                links_page = result_rows.find_all('a')
                                logger.log("Result found : "+links_page[0].get('href'), logger.DEBUG)

                                #seasonNameDetect = links_page[0].get_text()
                                seasonNameDetect = links_page[0].get('href')
                                seasonNameDetect = " ".join(seasonNameDetect.split())
                                #if not seasonNameDetect.find("Saison "+str(int(seasonVersion))) >= 0:
                                if not seasonNameDetect.find("saison-"+str(int(seasonVersion))) >= 0:
                                    continue

                                dataPage = self.get_url(links_page[0].get('href'), verify=False)
                                with BS4Parser(dataPage, 'html5lib') as htmlPage:
                                    url = links_page[0].get('href')
                                    title = ""

                                    corps_page = htmlPage(class_=re.compile('postinfo'))
                                    quality = corps_page[0].find_all('font')
                                    quality = quality[0].text.replace(' ','-').lower()

                                    for key, tv in self.titleVersion.items():
                                        if all(keyword in quality for keyword in tv["keywords"]):
                                            title = search_string.replace(" ",".") +"."+ tv["suffix"]
                                            break;

                                    logger.log("Quality detected : "+title,logger.DEBUG)

                                    providerDDLName = ""
                                    bTags = corps_page[0].find_all('b')

                                    for bTag in bTags:
                                        bForms = bTag.find_all('form')

                                        if len(bForms) == 0:
                                            providerDDLName = ""
                                            if self.canUseProvider(bTag.text):
                                                providerDDLName = bTag.text
                                        else:
                                            if self.canUseProvider(providerDDLName) and \
                                               bTag.find_all('button')[0].text.startswith("Episode "+str(int(episodeVersion))):
                                                   DlProtectLink = bForms[0].get('action')
                                                   logger.log("Protected link : "+DlProtectLink,logger.DEBUG)
                                                   encryptUrl = bTag.find_all('input')[0].get('value')
                                                   logger.log("Protected URL : "+encryptUrl,logger.DEBUG)

                                                   data = {}
                                                   data["url"] = encryptUrl
                                                   dataProtect = self.get_url(DlProtectLink, post_data=data)
                                                   with BS4Parser(dataProtect, 'html5lib') as htmlProtect:
                                                       protect_page = htmlProtect(class_=re.compile('card-body'))
                                                       providerDDLLink = protect_page[0].find_all('a')[0].get('href')

                                                   logger.log("Provider : "+providerDDLName, logger.INFO)
                                                   logger.log("Title : "+title, logger.INFO)
                                                   logger.log("Link : "+providerDDLLink, logger.INFO)

                                                   item = {'title': title, 'link': providerDDLLink}
                                                   items.append(item)

                            except Exception:
                                logger.log(u'Failed doing webui callback: {0}'.format((traceback.format_exc())), logger.ERROR)
            results += items

        return results

provider = ZoneTelechargementProvider()
