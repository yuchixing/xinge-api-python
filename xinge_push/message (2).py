#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from schedule import TimeInterval
from style import Style, ClickAction
from constant import *

class Message(object):
    """
    待推送的消息, Android系统专用
    """
    PUSH_SINGLE_PKG = 0
    PUSH_ACCESS_ID = 1

    def __init__(self):
        self.title = ""
        self.content = ""
        self.expireTime = 0
        self.sendTime = ""
        self.acceptTime = ()
        self.type = 0
        self.style = None
        self.action = None
        self.custom = {}
        self.multiPkg = self.PUSH_SINGLE_PKG
        self.raw = None
        self.loopTimes = 0
        self.loopInterval = 0

    def GetMessageObject(self):
        if self.raw is not None:
            if isinstance(self.raw, basestring):
                return json.loads(self.raw)
            else:
                return self.raw

        message = {}
        message['title'] = self.title
        message['content'] = self.content

        # TODO: check custom
        message['custom_content'] = self.custom

        acceptTimeObj = self.GetAcceptTimeObject()
        if None == acceptTimeObj:
            return None
        elif acceptTimeObj != []:
            message['accept_time'] = acceptTimeObj

        if self.type == MESSAGE_TYPE_ANDROID_NOTIFICATION:
            if None == self.style:
                style = Style()
            else:
                style = self.style

            if isinstance(style, Style):
                message['builder_id'] = style.builderId
                message['ring'] = style.ring
                message['vibrate'] = style.vibrate
                message['clearable'] = style.clearable
                message['n_id'] = style.nId
                message['ring_raw'] = style.ringRaw
                message['lights'] = style.lights
                message['icon_type'] = style.iconType
                message['icon_res'] = style.iconRes
                message['style_id'] = style.styleId
                message['small_icon'] = style.smallIcon
            else:
                # style error
                return None

            if None == self.action:
                action = ClickAction()
            else:
                action = self.action

            if isinstance(action, ClickAction):
                message['action'] = action.GetObject()
            else:
                # action error
                return None
        elif self.type == MESSAGE_TYPE_ANDROID_MESSAGE:
            pass
        else:
            return None

        return message

    def GetAcceptTimeObject(self):
        ret = []
        for ti in self.acceptTime:
            if isinstance(ti, TimeInterval):
                o = ti.GetObject()
                if o is None:
                    return None
                else:
                    ret.append(ti.GetObject())
            else:
                return None
        return ret

class MessageIOS(Message):
    """
    待推送的消息, iOS系统专用
    """
    def __init__(self):
        Message.__init__(self)
        self.alert = None
        self.badge = None
        self.sound = None
        self.category = None
        self.raw = None
        self.type = MESSAGE_TYPE_IOS_APNS_NOTIFICATION

    def GetMessageObject(self):
        if self.raw is not None:
            if isinstance(self.raw, basestring):
                try:
                    return json.loads(self.raw)
                except Exception:
                    return None
            elif isinstance(self.raw, dict):
                return self.raw
            else:
                return None

        message = self.custom

        acceptTimeObj = self.GetAcceptTimeObject()
        if None == acceptTimeObj:
            return None
        elif acceptTimeObj != []:
            message['accept_time'] = acceptTimeObj

        aps = {}
        if self.type == MESSAGE_TYPE_IOS_APNS_NOTIFICATION:
            if isinstance(self.alert, basestring) or isinstance(self.alert, dict):
                aps['alert'] = self.alert
            else:
                # alert type error
                return None
            if self.badge is not None:
                aps['badge'] = self.badge
            if self.sound is not None:
                aps['sound'] = self.sound
            if self.category is not None:
                aps['category'] = self.category
        elif self.type == MESSAGE_TYPE_IOS_REMOTE_NOTIFICATION:
            aps['content-available'] = 1
        else: # type error
            return None
        message['aps'] = aps
        return message


class MessageStatus(object):
    """
    推送任务的状态
    """
    def __init__(self, status, startTime):
        self.status = status
        self.startTime = startTime

    def __str__(self):
        return str(vars(self))

    def __repr__(self):
        return self.__str__()
