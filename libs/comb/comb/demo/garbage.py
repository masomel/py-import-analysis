# -*- coding: utf-8 -*-


import comb.demo.mongo as mongo
import comb.mq.mongo as MongoHelper
from pymongo import MongoClient




class Slot(mongo.Slot):
    def __enter__(self):
        MongoHelper.garbage(self.db['mq1'])
        return False


    def __exit__(self, exc_type, exc_val, exc_tb):
        print("exit(),nothing to do")


    def slot(self, result):
        print("this code is used to clean old-queue-data from demo/mongo.py")
        pass









