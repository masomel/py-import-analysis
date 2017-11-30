# -*- coding: utf-8 -*-





def push(redis,key,value):
    return redis.rpush(key,value)
    pass


def pop(redis,key):
    # @todo
    return redis.lpop(key)
    pass

