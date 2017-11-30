# -*- coding: utf-8 -*-



def token(collection, token='token'):
    return collection.find_and_modify({token: {'$exists': False}}, {'$set': {'token': True}})


def release(collection, token='token'):
    return collection.update({token: True}, {'$set': {token: False}}, multi=True)


def garbage(collection, token='token'):
    """
    garbage for mongo message queue
    :param collection:
    :param token:
    :return:
    """
    collection.remove({token: False}, multi=True)