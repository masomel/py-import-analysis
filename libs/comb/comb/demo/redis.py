# -*- coding: utf-8 -*-


import comb.slot
import comb.mq.redis as RedisHelper

import redis


class Slot(comb.slot.Slot):
    def initialize(self):
        """

        This block is execute before thread initial

       Example::

           class UserSlot(Slot):
               def initialize(self,*args,**kwargs):
                   self.attr = kwargs.get('attr',None)

               def slot(self, result):
                   ...

       """

        if self.extra_loader.options.get('--force1'):
            self.threads_num = 1
            print("Force thread nums to 1")


        self.db = redis.Redis()




    def __enter__(self):
        data = RedisHelper.push(self.db,'mq1','aaaa')
        if not data:
            return False
        return data['_id']

    def __exit__(self, exc_type, exc_val, exc_tb):
        data = RedisHelper.pop(self.db,'mq1')


    def slot(self, result):
        print("call slot,current data is:", result)
        pass


    @staticmethod
    def options():
        return (
            "Extra options:",
            ('--force1','force 1 thread'),
        )






