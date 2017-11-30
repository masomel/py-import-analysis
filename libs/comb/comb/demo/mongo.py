# -*- coding: utf-8 -*-


import comb.slot
import comb.mq.mongo as MongoHelper
from pymongo import MongoClient


class Slot(comb.slot.Slot):
    def initialize(self):
        """Hook for subclass initialization.

        This block is execute before thread initial

       Example::

           class UserSlot(Slot):
               def initialize(self,*args,**kwargs):
                   self.attr = kwargs.get('attr',None)

               def slot(self, result):
                   ...

       """

        self.threads_num = 4
        self.sleep = 1
        self.sleep_max = 60
        if self.debug:
            self.db = MongoClient('localhost', 27017)['db_mq_dev']
        else:
            self.db = MongoClient('localhost', 27017)['db_mq_pro']


    def __enter__(self):
        data = MongoHelper.token(self.db['mq1'])
        if not data:
            return False
        return data['_id']

    def __exit__(self, exc_type, exc_val, exc_tb):
        data = MongoHelper.release(self.db['mq1'])


    def slot(self, result):
        print("call slot,current mongo-id is:", result)
        pass









