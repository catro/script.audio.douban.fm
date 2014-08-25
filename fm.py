# -*- coding: utf-8 -*-

import sys
import re
import urllib
import urllib2
import gzip
import StringIO
import os
import threading
import socket
import time
import json
from Queue import Queue

try:
    import xbmc
    XBMC=True
except:
    XBMC=False

reload(sys)
sys.setdefaultencoding('utf8')


class BaseFM:

    def log(self, msg):
        if XBMC:
            xbmc.log('[%s]: %s' % (self.__class__.__name__, msg))
        else:
            print('[%s]: %s' % (self.__class__.__name__, msg))

    def __init__(self, **argv):
        if argv is None:
            self._channel_index = 0
            self._song_min = 1
            self._timeout = 10
        else:
            self._channel_index = argv.get('channel_index', 0)
            self._song_min = argv.get('song_min', 1)
            self._timeout = argv.get('timeout', 10)
        socket.setdefaulttimeout(self._timeout)
        self._song_queue = Queue()
        self._running = False
        self._channels = []

    def _get_channels(self):
        raise NotImplementedError

    def get_channels(self):
        if len(self._channels) == 0:
            self._get_channels()
        return self._channels

    def _set_channel(self, channel_index):
        raise NotImplementedError

    def set_channel(self, channel_index):
        self._set_channel(channel_index)
        while self._song_queue.empty() == False:
            self._song_queue.get(False)

    def _get_song(self):
        raise NotImplementedError

    def get_channel_title(self, channel):
        raise NotImplementedError

    def get_song_info(self, song):
        raise NotImplementedError

    def get_song(self):
        self.log('Get song')
        if self._song_queue.qsize() <= self._song_min and not self._running:
            self._running = True
            t = threading.Timer(0.001, self.run)
            t.start()
        try:
            song = self._song_queue.get(self._timeout)
            return song
        except:
            return {}

    def run(self):
        songs = self._get_song()
        for song in songs:
            self._song_queue.put(song)
        self._running = False

    def _open_url(self, url):
        try:
            req = urllib2.Request(url)
            req.add_header('Cookie', 'bid=\"kkuoIz8va00\"; viewed=\"4227116\"; __utma=30149280.1671652081.1408968993.1408968993.1408968993.1; __utmb=30149280.1.10.1408968993; __utmc=30149280; __utmz=30149280.1408968993.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none)')
            req.add_header('User-Agent', r'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.110 Safari/537.36 CoolNovo/2.0.9.20')
            req.add_header('Accept-encoding', 'gzip')
            response = urllib2.urlopen(req)
            httpdata = response.read()
            if response.headers.get('content-encoding', None) == 'gzip':
                httpdata = gzip.GzipFile(fileobj=StringIO.StringIO(httpdata)).read()
            response.close()
            match = re.compile('encodingt=(.+?)"').findall(httpdata)
            if len(match)<=0:
                match = re.compile('charset="(.+?)"').findall(httpdata)
            if len(match)<=0:
                match = re.compile('charset=(.+?)"').findall(httpdata)
            if len(match)>0:
                charset = match[0].lower()
                if charset == 'gb2312':
                    charset = 'gbk'
                if (charset != 'utf-8') and (charset != 'utf8'):
                    httpdata = httpdata.decode(charset)
                else:
                    httpdata = httpdata.decode('utf8')
        except:
            httpdata = ''

        return httpdata


class DoubanFM(BaseFM):
    _base_url = 'http://www.douban.com/j/app/radio/people?app_name=radio_desktop_win&version=100'

    def _get_channels(self):
        self.log('Get channels')
        page = self._open_url('http://www.douban.com/j/app/radio/channels')
        try:
            data = json.loads(page)
            self._channels = data['channels']
        except:
            self.log('No channel')
            pass

    def _set_channel(self, channel_index):
        if channel_index < len(self._channels):
            self._channel_index = channel_index
            return True
        else:
            return False

    def _get_song(self):
        if len(self._channels) == 0:
            return None
        url = self._base_url + '&channel=%s&type=n' % self._channels[self._channel_index]['channel_id']
        self.log('Get song list from ' + url)
        page = self._open_url(url)
        try:
            data = json.loads(page)
            for song in data['song']:
                print u'Get song: ' + song['title']
            return data['song']
        except:
            self.log('No song')
            pass

    def get_channel_title(self, channel):
        return channel['name']

    def get_song_info(self, song):
        return {'title': song['title'], 'url': song['url'], 'image': song['picture']}


if __name__ == '__main__':
    fm = DoubanFM()

    c = 's'
    while not c == 'x':
        if len(c) > 0:
            if c[0] == 's':
                channels = fm.get_channels()
                i = 0
                for channel in channels:
                    i += 1
                    print ('%d. %s' % (i, fm.get_channel_title(channel)))
            elif c[0] == 'n':
                song = fm.get_song()
                print 'Playing song ' + fm.get_song_info(song)['title']
            elif c[0] in '0123456789':
                i = int(c)
                fm.set_channel(i - 1)
                print 'Set channel to %s' % fm.get_channel_title(fm.get_channels()[i - 1])
                song = fm.get_song()
                print 'Playing song ' + fm.get_song_info(song)['title']
        
        c=raw_input()
        
        
