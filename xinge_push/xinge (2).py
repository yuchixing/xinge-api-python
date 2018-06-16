#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copyright ? 1998 - 2013 Tencent. All Rights Reserved. 腾讯公司 版权所有

"""
import sys
if sys.VERSION > 3:
    PY3 = True
    import httplib
    import urllib
else:
    PY3 = False
    import http.client as httplib
    import urllib.parse as urllib

import json
import hashlib
import time

from constant import *
from message import Message, MessageIOS, MessageStatus
from collections import Iterable

class TagTokenPair(object):
    """
    tag-token串，用来批量设置tag和token的对应关系
    """
    def __init__(self, tag, token):
        self.tag = str(tag)
        self.token = str(token)

class XingeApp(object):
    """
    xinge_push的主要模块，调用信鸽restful API通信
    用来创建、查询推送任务，设置、查询account和tags等信息
    """
    PATH_PUSH_TOKEN = '/v2/push/single_device'
    PATH_PUSH_ACCOUNT = '/v2/push/single_account'
    PATH_PUSH_ACCOUNT_LIST = '/v2/push/account_list'
    PATH_PUSH_ALL = '/v2/push/all_device'
    PATH_PUSH_TAGS = '/v2/push/tags_device'
    PATH_GET_PUSH_STATUS = '/v2/push/get_msg_status'
    PATH_GET_DEV_NUM = '/v2/application/get_app_device_num'
    PATH_QUERY_TAGS = '/v2/tags/query_app_tags'
    PATH_CANCEL_TIMING_PUSH = '/v2/push/cancel_timing_task'
    PATH_BATCH_SET_TAG = '/v2/tags/batch_set'
    PATH_BATCH_DEL_TAG = '/v2/tags/batch_del'
    PATH_QUERY_TOKEN_TAGS = '/v2/tags/query_token_tags'
    PATH_QUERY_TAG_TOKEN_NUM = '/v2/tags/query_tag_token_num'
    PATH_PUSH_TOKEN_LIST_MULTIPLE = '/v2/push/device_list_multiple'
    PATH_PUSH_ACCOUNT_LIST_MULTIPLE = '/v2/push/account_list_multiple'
    PATH_CREATE_MULTIPUSH = '/v2/push/create_multipush'
    PATH_QUERY_INFO_OF_TOKEN = '/v2/application/get_app_token_info'
    PATH_QUERY_TOKENS_OF_ACCOUNT = '/v2/application/get_app_account_tokens'
    PATH_DEL_TOKEN_OF_ACCOUNT = '/v2/application/del_app_account_tokens'
    PATH_DEL_ALL_TOKENS_OF_ACCOUNT = '/v2/application/del_app_account_all_tokens'

    PATH_PUSH_APP =  '/v3/push/app'

    
    IOS_MIN_ID = 2200000000
    
    def __init__(self, accessId, secretKey):
        """

        :param accessId: int, APP的唯一标识
        :param secretKey: str, 信鸽网站分配的通信密钥
        """
        self.accessId = int(accessId)
        self.secretKey = str(secretKey)

    def ValidateToken(self, token):
        if(self.accessId >= 2200000000):
            return len(token) == 64
        else:
            return (len(token) == 40 or len(token) == 64)
        
    def InitParams(self):
        params = {}
        params['access_id'] = self.accessId
        params['timestamp'] = XingeHelper.GenTimestamp()
        return params
    
    def ValidateMessageType(self, message):
        if(self.accessId >= self.IOS_MIN_ID and isinstance(message, MessageIOS)):
            return True
        elif(self.accessId < self.IOS_MIN_ID and not isinstance(message, MessageIOS)):
            return True
        else:
            return False
        
    def SetPushParams(self, params, message, environment):
        if False == self.ValidateMessageType(message):
            return False
        if(self.accessId >= self.IOS_MIN_ID and environment != ENV_PROD and environment != ENV_DEV):
            return False
        elif(self.accessId < self.IOS_MIN_ID):
            environment = 0
        
        params['expire_time'] = message.expireTime
        params['send_time'] = message.sendTime
        params['message_type'] = message.type
        params['multi_pkg'] = message.multiPkg
        params['environment'] = environment
        msgObj = message.GetMessageObject()
        if None == msgObj or not isinstance(msgObj, dict):
            return False
        else:
            params['message'] = json.dumps(msgObj, separators=(',',':'), ensure_ascii=False)
            return True
        
    def Request(self, path, params):
        params['sign'] = XingeHelper.GenSign(path, params, self.secretKey)
        return XingeHelper.Request(path, params)
    
    def PushSingleDevice(self, deviceToken, message, environment=0):
        """
        推送到单个设备
        :param deviceToken: str, 目标设备token
        :param message: Message, 待推送的消息
        :param environment: int, 推送的目标环境(仅iOS需要, 必须是ENV_PROD或ENV_DEV的一种)
        :return: (int, str), (ret_code, error_msg)
        """
        deviceToken = str(deviceToken)
        if not (isinstance(message, Message) or isinstance(message, MessageIOS)):
            return ERR_PARAM, 'message type error'
        
        params = self.InitParams()
        if False == self.SetPushParams(params, message, environment):
            return ERR_PARAM, 'invalid message, check your input'
        params['device_token'] = deviceToken
        
        ret = self.Request(self.PATH_PUSH_TOKEN, params)
        return ret[0], ret[1]
    
    def PushSingleAccount(self, deviceType, account, message, environment=0):
        """
        推送到单个账号
        :param deviceType: int, 设备类型，请填0
        :param account: str, 目标账号
        :param message: Message, 待推送的消息
        :param environment: int, 推送的目标环境(仅iOS需要, 必须是ENV_PROD或ENV_DEV的一种)
        :return: (int, str), (ret_code, error_msg)
        """
        deviceType = int(deviceType)
        account = str(account)
        if not isinstance(message, Message):
            return ERR_PARAM, 'message type error'
        
        params = self.InitParams()
        if False == self.SetPushParams(params, message, environment):
            return ERR_PARAM, 'invalid message, check your input'
        params['device_type'] = deviceType
        params['account'] = account
        
        ret = self.Request(self.PATH_PUSH_ACCOUNT, params)
        return ret[0], ret[1]
    
    def PushAccountList(self, deviceType, accountList, message, environment=0):
        """
        推送到多个账号，如果目标账号数超过10000，建议改用XingeApp.PushDeviceListMultiple
        :param deviceType: int, 设备类型，请填0
        :param accountList: Iterable, 账号列表
        :param message: Message, 待推送的消息
        :param environment: int, 推送的目标环境(仅iOS需要, 必须是ENV_PROD或ENV_DEV的一种)
        :return: (int, str, dict), (ret_code, error_msg, ext_info)
        """
        deviceType = int(deviceType)
        if not isinstance(message, Message):
            return ERR_PARAM, 'message type error'
        if not isinstance(accountList, Iterable):
            return ERR_PARAM, 'accountList type error', None
        
        params = self.InitParams()
        if False == self.SetPushParams(params, message, environment):
            return ERR_PARAM, 'invalid message, check your input'
        params['device_type'] = deviceType
        params['account_list'] = json.dumps([str(i) for i in accountList])
        params['send_time'] = ""
        
        ret = self.Request(self.PATH_PUSH_ACCOUNT_LIST, params)
        return ret[0], ret[1], ret[2]
    
    def PushAllDevices(self, deviceType, message, environment=0):
        """
        推送给全量设备
        :param deviceType: int, 设备类型，请填0
        :param message: Message, 待推送的消息
        :param environment: int, 推送的目标环境(仅iOS需要, 必须是ENV_PROD或ENV_DEV的一种)
        :return: 若成功则返回(int, str, str), (0, '', push_id)；失败返回(int, str, None), (ret_code, error_msg, None)
        """
        deviceType = int(deviceType)
        if not isinstance(message, Message):
            return ERR_PARAM, 'message type error', None
        
        params = self.InitParams()
        if False == self.SetPushParams(params, message, environment):
            return ERR_PARAM, 'invalid message, check your input', None
        params['device_type'] = deviceType
        params['loop_times'] = message.loopTimes
        params['loop_interval'] = message.loopInterval
        
        ret = self.Request(self.PATH_PUSH_ALL, params)
        result = None
        if ERR_OK == ret[0]:
            if 'push_id' not in ret[2]:
                return ERR_RETURN_DATA, '', result
            else:
                result = ret[2]['push_id']
        return ret[0], ret[1], result
    
    def PushTags(self, deviceType, tagList, tagsOp, message, environment=0):
        """
        推送给多个tags对应的设备
        :param deviceType: int, 设备类型，请填0
        :param tagList: Iterable, 指定推送的tag列表
        :param tagsOp: str, 多个tag的运算关系，取值必须是下面之一： AND OR
        :param message: Message, 待推送的消息
        :param environment: int, 推送的目标环境(仅iOS需要, 必须是ENV_PROD或ENV_DEV的一种)
        :return: 若成功则返回(int, str, str), (0, '', push_id)；失败返回(int, str, None), (ret_code, error_msg, None)
        """
        deviceType = int(deviceType)
        if not isinstance(message, Message):
            return ERR_PARAM, 'message type error', None
        if not isinstance(tagList, Iterable):
            return ERR_PARAM, 'tagList type error', None
        if tagsOp not in ('AND','OR'):
            return ERR_PARAM, 'tagsOp error', None
        
        params = self.InitParams()
        if not self.SetPushParams(params, message, environment):
            return ERR_PARAM, 'invalid message, check your input', None
        params['device_type'] = deviceType
        params['tags_list'] = json.dumps([str(tag) for tag in tagList], separators=(',',':'))
        params['tags_op'] = tagsOp
        params['loop_times'] = message.loopTimes
        params['loop_interval'] = message.loopInterval
        
        ret = self.Request(self.PATH_PUSH_TAGS, params)
        result = None
        if ERR_OK == ret[0]:
            if 'push_id' not in ret[2]:
                return ERR_RETURN_DATA, '', result
            else:
                result = ret[2]['push_id']
        return ret[0], ret[1], result

    def CreateMultipush(self, message, environment=0):
        """
        创建大批量推送消息，后续可调用PushAccountListMultiple或PushDeviceListMultiple接口批量添加设备；此接口创建的任务不支持定时推送
        :param message: Message, 待推送的消息
        :param environment: int, 推送的目标环境(仅iOS需要, 必须是ENV_PROD或ENV_DEV的一种)
        :return: 若成功则返回(int, str, str), (0, '', push_id)；失败返回(int, str, None), (ret_code, error_msg, None)
        """
        if not isinstance(message, Message):
            return ERR_PARAM, 'message type error'
        
        params = self.InitParams()
        if not self.SetPushParams(params, message, environment):
            return ERR_PARAM, 'invalid message, check your input'
            
        ret = self.Request(self.PATH_CREATE_MULTIPUSH, params)
        result = None
        if ERR_OK == ret[0]:
            if 'push_id' not in ret[2]:
                return ERR_RETURN_DATA, '', result
            else:
                result = ret[2]['push_id']
        return ret[0], ret[1], result

    def PushDeviceListMultiple(self, pushId, deviceList):
        """
        推送消息给大批量设备，可对同一个push_id多次调用此接口
        :param pushId: CreateMultipush函数返回的push_id
        :param deviceList: Iterable, 待推送的设备列表
        :return: (int, str), (ret_code, error_msg)
        """
        pushId = int(pushId)
        if pushId == 0:
            return ERR_PARAM, 'push_id type error'
        if not isinstance(deviceList, Iterable):
            return ERR_PARAM, 'deviceList type error', None
        
        params = self.InitParams()        
        params['device_list'] = json.dumps([str(i) for i in deviceList])
        params['push_id'] = pushId
        params['send_time'] = ""
        ret = self.Request(self.PATH_PUSH_TOKEN_LIST_MULTIPLE, params)
        return ret[0], ret[1]

    def PushAccountListMultiple(self, pushId, accountList):
        """
        推送消息给大批量账号，可对同一个push_id多次调用此接口
        :param pushId: CreateMultipush函数返回的push_id
        :param accountList: Iterable, 待推送的账号列表
        :return: (int, str), (ret_code, error_msg)
        """
        push_id = int(pushId)
        if push_id == 0:
            return ERR_PARAM, 'push_id type error'
        if not isinstance(accountList, Iterable):
            return ERR_PARAM, 'accountList type error', None
        
        params = self.InitParams()        
        params['account_list'] = json.dumps([str(i) for i in accountList])
        params['push_id'] = pushId
        params['send_time'] = ""
        ret = self.Request(self.PATH_PUSH_ACCOUNT_LIST_MULTIPLE, params)
        return ret[0], ret[1]
    
    def QueryPushStatus(self, pushIdList):
        """
        查询群发消息的状态，可同时查询多个pushId状态
        :param pushIdList: Iterable, 要查询的push_id列表
        :return: 若成功则返回(int, str, dict), (0, '', {push_id: MessageStatus})；失败返回(int, str, dict), (ret_code, error_msg, {})
        """
        if not isinstance(pushIdList, Iterable):
            return ERR_PARAM, 'pushIdList type error', None
        
        params = self.InitParams()
        params['push_ids'] = json.dumps([{'push_id':str(pushId)} for pushId in pushIdList], separators=(',',':'))
        
        ret = self.Request(self.PATH_GET_PUSH_STATUS, params)
        result = {}
        if ERR_OK == ret[0]:
            if 'list' not in ret[2]:
                return ERR_RETURN_DATA, '', result
            for status in ret[2]['list']:
                result[status['push_id']] = MessageStatus(status['status'], status['start_time'])
            
        return ret[0], ret[1], result
    
    def QueryDeviceCount(self):
        """
        查询APP覆盖的设备数量
        :return: (int, str, int), (ret_code, error_msg, device_num)
        """
        params = self.InitParams()
        ret = self.Request(self.PATH_GET_DEV_NUM, params)
        result = None
        if ERR_OK == ret[0]:
            if 'device_num' not in ret[2]:
                return ERR_RETURN_DATA, '', result
            else:
                result = ret[2]['device_num']
        return ret[0], ret[1], result
    
    def QueryTags(self, start, limit):
        """
        查询应用当前所有的tags
        :param start: int, 从哪个index开始
        :param limit: int, 限制结果数量，最多取多少个tag
        :return: (int, str, int, list), (ret_code, error_msg, total_count, tag_list)
        """
        params = self.InitParams()
        params['start'] = int(start)
        params['limit'] = int(limit)
        
        ret = self.Request(self.PATH_QUERY_TAGS, params)
        retCode = ret[0]
        total = None
        tags = []
        if ERR_OK == ret[0]:
            if 'total' not in ret[2]:
                retCode = ERR_RETURN_DATA
            else:
                total = ret[2]['total']
                
            if 'tags' in ret[2]:
                tags = ret[2]['tags']
        return retCode, ret[1], total, tags
    
    def CancelTimingPush(self, pushId):
        """
        取消尚未推送的定时任务
        :param pushId: int, 各类推送任务返回的push_id
        :return: (int, str), (ret_code, error_msg)
        """
        params = self.InitParams()
        params['push_id'] = str(pushId)
        
        ret = self.Request(self.PATH_CANCEL_TIMING_PUSH, params)
        return ret[0], ret[1]
        
    def BatchSetTag(self, tagTokenPairs):
        """
        批量为token设备标签，每次调用最多输入20个pair
        :param tagTokenPairs: TagTokenPair, 需要设置的tag-token对
        :return: (int, str), (ret_code, error_msg)
        """
        for pair in tagTokenPairs:
            if not isinstance(pair, TagTokenPair):
                return ERR_PARAM, 'tag-token pair type error!'
            if False == self.ValidateToken(pair.token):
                return ERR_PARAM, ('invalid token %s' % pair.token)
        params = self.InitParams()
        params['tag_token_list'] = json.dumps([[pair.tag, pair.token] for pair in tagTokenPairs])
        
        ret = self.Request(self.PATH_BATCH_SET_TAG, params)
        return ret[0], ret[1]
        
    def BatchDelTag(self, tagTokenPairs):
        """
        批量为token删除标签，每次调用最多输入20个pair
        :param tagTokenPairs: TagTokenPair, 需要设置的tag-token对
        :return: (int, str), (ret_code, error_msg)
        """
        for pair in tagTokenPairs:
            if not isinstance(pair, TagTokenPair):
                return ERR_PARAM, 'tag-token pair type error!'
            if False == self.ValidateToken(pair.token):
                return ERR_PARAM, ('invalid token %s' % pair.token)
        params = self.InitParams()
        params['tag_token_list'] = json.dumps([[pair.tag, pair.token] for pair in tagTokenPairs])
        
        ret = self.Request(self.PATH_BATCH_DEL_TAG, params)
        return ret[0], ret[1]

    def QueryTokenTags(self, token):
        """
        查询设备下所有的tag
        :param token: str, 目标设备token
        :return: (int, str, list), (ret_code, error_msg, tag_list)
        """
        params = self.InitParams()
        params['device_token'] = str(token)

        ret = self.Request(self.PATH_QUERY_TOKEN_TAGS, params)
        result = None
        if 'tags' in ret[2]:
            result = ret[2]['tags']
        return ret[0], ret[1], result

    def QueryTagTokenNum(self, tag):
        """
        查询带有指定tag的设备数量
        :param tag: str, 指定的标签
        :return: (int, str, int), (ret_code, error_msg, device_num)
        """
        params = self.InitParams()
        params['tag'] = str(tag)

        ret = self.Request(self.PATH_QUERY_TAG_TOKEN_NUM, params)
        result = None
        if 'device_num' in ret[2]:
            result = ret[2]['device_num']
        return ret[0], ret[1], result

    def QueryInfoOfToken(self, token):
        """
        查询token相关的信息，包括最近一次活跃时间，离线消息数等
        :param token: str, 目标设备token
        :return: (int, str, dict), (ret_code, error_msg, ext_info)
        """
        params = self.InitParams()
        params['device_token'] = str(token)

        ret = self.Request(self.PATH_QUERY_INFO_OF_TOKEN, params)
        return ret[0], ret[1], ret[2]

    def QueryTokensOfAccount(self, account):
        """
        查询账号绑定的token
        :param account: str, 指定的账号
        :return: (int, str, list), (ret_code, error_msg, token_list)
        """
        params = self.InitParams()
        params['account'] = str(account)

        ret = self.Request(self.PATH_QUERY_TOKENS_OF_ACCOUNT, params)
        result = None
        if 'tokens' in ret[2]:
            result = ret[2]['tokens']
        return ret[0], ret[1], result

    def DeleteTokenOfAccount(self, account, device_token):
        """
        删除指定账号和token的绑定关系（token仍然有效）
        :param account: str, 目标账号
        :param device_token: str, 目标token
        :return: (int, str, dict), (ret_code, error_msg, ext_info)
        """
        params = self.InitParams()
        params['account'] = str(account)
        params['device_token'] = str(device_token)

        ret = self.Request(self.PATH_DEL_TOKEN_OF_ACCOUNT, params)
        return ret[0], ret[1], ret[2]

    def DeleteAllTokensOfAccount(self, account):
        """
        删除指定账号绑定的所有token（token仍然有效）
        :param account: str, 目标账号
        :return: (int, str), (ret_code, error_msg)
        """
        params = self.InitParams()
        params['account'] = str(account)

        ret = self.Request(self.PATH_DEL_ALL_TOKENS_OF_ACCOUNT, params)
        return ret[0], ret[1]

class XingeHelper(object):
    XINGE_HOST = 'openapi.xg.qq.com'
    XINGE_PORT = 80
    TIMEOUT = 10
    HTTP_METHOD = 'POST'
    HTTP_HEADERS = {'HOST' : XINGE_HOST, 'Content-Type' : 'application/x-www-form-urlencoded'}
    
    STR_RET_CODE = 'ret_code'
    STR_ERR_MSG = 'err_msg'
    STR_RESULT = 'result'
    
    @classmethod
    def SetServer(cls, host=XINGE_HOST, port=XINGE_PORT):
        cls.XINGE_HOST = host
        cls.XINGE_PORT = port
        cls.HTTP_HEADERS['HOST'] = cls.XINGE_HOST
    
    @classmethod
    def GenSign(cls, path, params, secretKey):
        ks = sorted(params.keys())
        paramStr = ''.join([('%s=%s' % (k, params[k])) for k in ks])
        signSource = '%s%s%s%s%s' % (cls.HTTP_METHOD, cls.XINGE_HOST, path, paramStr, secretKey)
        return hashlib.md5(signSource).hexdigest()
    
    @classmethod
    def GenTimestamp(cls):
        return int(time.time())
    
    @classmethod
    def Request(cls, path, params):
        httpClient = httplib.HTTPConnection(cls.XINGE_HOST, cls.XINGE_PORT, timeout=cls.TIMEOUT)
        if cls.HTTP_METHOD == 'GET':
            httpClient.request(cls.HTTP_METHOD, ('%s?%s' % (path, urllib.urlencode(params))), headers=cls.HTTP_HEADERS)
        elif cls.HTTP_METHOD == 'POST':
            httpClient.request(cls.HTTP_METHOD, path, urllib.urlencode(params), headers=cls.HTTP_HEADERS)
        else:
            # invalid method
            return ERR_PARAM, '', None
        
        response = httpClient.getresponse()
        retCode = ERR_RETURN_DATA
        errMsg = ''
        result = {}
        if 200 != response.status:
            retCode = ERR_HTTP
        else:
            data = response.read()
            retDict = json.loads(data)
            if(cls.STR_RET_CODE in retDict):
                retCode = retDict[cls.STR_RET_CODE]
            if(cls.STR_ERR_MSG in retDict):
                errMsg = retDict[cls.STR_ERR_MSG]
            if(cls.STR_RESULT in retDict):
                if isinstance(retDict[cls.STR_RESULT], dict):
                    result = retDict[cls.STR_RESULT]
                elif isinstance(retDict[cls.STR_RESULT], list):
                    result = retDict[cls.STR_RESULT]
                elif retDict[cls.STR_RESULT] == '':
                    pass
                else:
                    retCode = ERR_RETURN_DATA
        return retCode, errMsg, result
