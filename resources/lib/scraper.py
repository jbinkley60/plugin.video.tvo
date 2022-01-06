# -*- coding: utf-8 -*-
# TV Ontario Kodi Video Addon
#
from t1mlib import t1mAddon
import json
import re
import os
import xbmc
import xbmcplugin
import xbmcgui
import html.parser
import sys
import requests

URL_BRIGHTCOVE_POLICY_KEY = 'http://players.brightcove.net/%s/%s_default/index.min.js'
# AccountId, PlayerId
URL_BRIGHTCOVE_VIDEO_JSON = 'https://edge.api.brightcove.com/'\
                              'playback/v1/accounts/%s/videos/%s'
# data_account, video_id
UNESCAPE = html.parser.HTMLParser().unescape
TVOBASE = 'https://tvo.org'


class myAddon(t1mAddon):

  def getAddonMenu(self,url,ilist):
      azurl = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ1'
      for name in azurl:
          url = name
          infoList = {'mediatype':'tvshow',
                      'Title': name,
                      'Plot': name}
          ilist = self.addMenuItem(name,'GS', ilist, url, self.addonIcon, self.addonFanart, infoList, isFolder=True)
      return(ilist)


  def getAddonShows(self,url,ilist):
      html = requests.get(''.join([TVOBASE,'/documentaries/browse/filters/ajax/',url]), headers=self.defaultHeaders).text
      html = html[11:-12]
      a = json.loads(html)
      a = a["data"]
      a = re.compile('<div class="views\-row">.+?href="(.+?)".+?<div class="bc-thumb-(.+?)".+?src="(.+?)".+?results">(.+?)<.+?field\-\-item">(.+?)<',re.DOTALL).findall(a)
      for url,playable,thumb,name,plot in a:
          name = name.strip()
          name = UNESCAPE(name)
          url = ''.join([TVOBASE,url])
          infoList= {'mediatype':'tvshow',
                     'Title': name,
                     'Plot': UNESCAPE(plot)}
          if playable == 'wrapper':
              ilist = self.addMenuItem(name,'GV', ilist, url, thumb, thumb, infoList, isFolder=False)
          else:
              ilist = self.addMenuItem(''.join([name,' (Series)']),'GE', ilist, url, thumb, thumb, infoList, isFolder=True)
      return(ilist)


  def getAddonEpisodes(self,url,ilist):
      self.defaultVidStream['width']  = 640
      self.defaultVidStream['height'] = 480
      html = requests.get(url, headers=self.defaultHeaders).text
      vids = re.compile('<div class="content-list__first.+?href="(.+?)".+?src="(.+?)".+?href=.+?>(.+?)<.+?field-summary"><div class="field-content">(.+?)<',re.DOTALL).findall(html)
      if vids == []:
          vids = re.compile('"og:url" content="(.+?)".+?content="(.+?)".+?content="(.+?)".+?".+?content="(.+?)"',re.DOTALL).search(html).groups()
          vids = [(vids[0],vids[2],vids[1],vids[3])]
      TVShowTitle = re.compile('property="og:title" content="(.+?)"', re.DOTALL).search(html).group(1)
      for (url, thumb, name, plot) in vids:
          if not url.startswith('http'):
              url = ''.join([TVOBASE,url])
          if not thumb.startswith('http'):
              thumb = ''.join([TVOBASE,thumb[1:]])
          fanart = thumb
          name = UNESCAPE(name)
          infoList = {'mediatype':'episode',
                      'Title': name,
                      'TVShowTitle': UNESCAPE(TVShowTitle),
                      'Studio':'TV Ontario',
                      'Plot': UNESCAPE(plot)}
          ilist = self.addMenuItem(name,'GV', ilist, url, thumb, fanart, infoList, isFolder=False)
      return(ilist)


  def getAddonVideo(self,url):
      html = requests.get(url, headers=self.defaultHeaders).text
      data_player = re.compile('data-player="(.+?)"',re.DOTALL).search(html).group(1)
      data_video_id = re.compile('data-video-id="(.+?)"',re.DOTALL).search(html).group(1)
      data_account = re.compile('data-account="(.*?)"',re.DOTALL).search(html).group(1)
      file_js = requests.get(URL_BRIGHTCOVE_POLICY_KEY %
                                (data_account, data_player)).text
      policy_key = re.compile('policyKey:"(.+?)"').search(file_js).group(1)
      bcurl = URL_BRIGHTCOVE_VIDEO_JSON % (data_account, data_video_id)
      bcpolicykey = 'application/json;pk=%s' % policy_key
      uheaders = self.defaultHeaders.copy()
      uheaders['Accept'] = bcpolicykey
      resp = requests.get(bcurl, headers=uheaders).text
      json_parser = json.loads(resp)
      vidurl = ''
      if 'sources' in json_parser:
        for url in json_parser["sources"]:
            if 'src' in url:
                if 'm3u8' in url["src"]:
                    vidurl = url["src"]
      if vidurl == '':
        return False
      suburl = ''
      if 'text_tracks' in json_parser:
        for url in json_parser["text_tracks"]:
            if 'src' in url:
                if 'text/vtt' in url["src"]:
                    suburl = url["src"]
      liz = xbmcgui.ListItem(path=vidurl)
      if suburl != '':
        liz.setSubtitles([suburl])
      xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, liz)
