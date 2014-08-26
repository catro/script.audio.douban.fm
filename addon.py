# -*- coding: utf-8 -*-
import os
import sys

import xbmc
import xbmcaddon
import xbmcgui

from fm import DoubanFM

addon = xbmcaddon.Addon(id='script.audio.douban.fm')
addon_path = addon.getAddonInfo('path')
addon_name = addon.getAddonInfo('name')
reload(sys)
sys.setdefaultencoding('utf8')

class FMPlayer(xbmc.Player):
    def __init__(self, *args, **kwargs):
        self._continue = True
        self._onNewSong = kwargs.get('onNewSong')
        self._fm = DoubanFM()
        xbmc.Player.__init__(self)

    def getFM(self):
        return self._fm

    def play(self):
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        song = self._fm.get_song()
        if len(song.keys()) > 0:
            self._onNewSong(song)
            listitem = xbmcgui.ListItem(song.get('title', ''))
            listitem.setInfo('music', {'title': song.get('title', '')})
            xbmc.Player().play(song.get('url', ''))
        else:
            xbmcgui.notification('豆瓣FM', '获取歌曲超时')
        xbmc.executebuiltin( "Dialog.Close(busydialog)")

    def onPlayBackEnded(self):
        if self._continue == True:
            self.play()

    def quit(self):
        self._continue = False
        self.stop()

class GUI(xbmcgui.WindowXML):
    CONTROL_CHANNEL_LIST = 500
    CONTROL_FAV = 521
    CONTROL_BAN = 522
    CONTROL_NEXT = 523
    ACTION_PREVIOUS_MENU = [9, 92, 10]
    ACTION_EXIT_SCRIPT = [13]
    ACTION_PLAY = [79]

    def __init__(self, *args, **kwargs):
        self._player = FMPlayer(onNewSong=self.onNewSong)
        self._player.stop()
        self._fm = self._player.getFM()
        self._channel_index = 1
        self._channels = []
        xbmcgui.WindowXML.__init__(self)

    def onInit(self):
        xbmc.executebuiltin("ActivateWindow(busydialog)")
        if len(self._channels) == 0:
            self._window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
            self._channel_list = self.getControl(self.CONTROL_CHANNEL_LIST)
            xbmc.executebuiltin("ActivateWindow(busydialog)")
            self._channels = self._fm.get_channels()
            xbmc.executebuiltin( "Dialog.Close(busydialog)")

            if len(self._channels) > 0:
                self._channel_list.reset()
                for channel in self._channels:
                    li = xbmcgui.ListItem(self._fm.get_channel_title(channel))
                    self._channel_list.addItem(li)
                self._channel_list.getListItem(self._channel_index).select(True)
                self._fm.set_channel(self._channel_index)
                self._player.play()
            else:
                xbmcgui.notification(u'豆瓣FM', u'获取列表超时')

    def onNewSong(self, song):
        title = song.get('title', '')
        picture = song.get('picture', '')
        artist = song.get('artist', '')
        albumtitle = song.get('albumtitle', '')
        public_time = song.get('public_time', '')
        self._window.setProperty('title', title)
        self._window.setProperty('picture', picture)
        self._window.setProperty('artist', artist)
        self._window.setProperty('albumtitle', albumtitle)
        self._window.setProperty('public_time', public_time)

    def onAction(self, action):
        action_id = action.getId()
        if action_id in self.ACTION_PREVIOUS_MENU:
            if self._player.isPlaying():
                self._player.stop()
            self.close()

    def onClick(self, controlId):
        if controlId == self.CONTROL_CHANNEL_LIST:
            self.updateSelection()
        elif controlId == self.CONTROL_NEXT:
            self._player.play()

    def updateSelection(self):
        pos = self._channel_list.getSelectedPosition()
        if pos != self._channel_index:
            self._channel_list.getListItem(self._channel_index).select(False)
            self._channel_list.getListItem(pos).select(True)
            self._channel_index = pos
            self._fm.set_channel(pos)
            self._player.play()

    def log(self, msg):
        xbmc.log('[DoubanFMGUI]: %s' % msg)

if __name__ == '__main__':
    gui = GUI(u'douban_skin.xml', addon_path, "Default")
    gui.doModal()
    del gui
