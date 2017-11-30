# -*- coding: utf-8 -*-

class Slot(object):
    """
    To use comb, you should create a python module file. we named *slot*.

    A legal slot must be named 'Slot' in your module file and it must be at least contain four method:

    * `initialize`

    initial resource, e.g: database handle

    * `__enter__`

    get next data to do,you can fetch one or more data.

    * `slot`

    user custom code

    * `__exit__`

    when slot finished, call this method

    """

    def __init__(self, combd):
        """Don't override this method unless what you're doing.

        """

        self.threads_num = combd.threads_num
        self.sleep = combd.sleep
        self.sleep_max = combd.sleep_max
        self.debug = combd.debug
        self.combd = combd

        self.initialize()


    def initialize(self):
        """Hook for subclass initialization.
        
        This block is execute before thread initial
        
        Example::

            class UserSlot(Slot):
                def initialize(self):
                    self.threads_num = 10 

                def slot(self, result):
                    ...
        
        """
        pass

    def __enter__(self):
        """You **MUST** return False when no data to do.

        The return value will be used in `Slot.slot`
        """
        print("You should override __enter__ method by subclass")
        return False


    def __exit__(self, exc_type, exc_val, exc_tb):
        """When slot done, will call this method.
        """
        print("You should override __exit__ method by subclass")
        pass


    def slot(self, msg):
        """
        Add your custom code at here.

        For example, look at:

        * `comb.demo.list`

        * `comb.demo.mongo`

        * `comb.demo.redis`


        """

        pass


        # @staticmethod
        # def options():
        # """
        # replace this method if you want add user options
        #     :return:
        #     """
        #     return ()
        #     pass
