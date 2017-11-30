

from cmd2 import Cmd
import os, sys, urllib2
__version__ = '0.1'
     
class Myshell(Cmd):
        """
       The main class
     
       """
     
        def __init__(self):
            Cmd.__init__(self)
     
        def do_stock(self, line):
            print line
	    req = urllib2.Request('http://download.finance.yahoo.com/d/quotes?s='+line+'&f=l1')
	    res = urllib2.urlopen(req)	#open URL
	    print 'Stock value is:',res.read()
	
	def do_greet(self, line):
	    f = os.popen('whoami')	#take the username in f
	    name = f.read()
	    print "Hi ", name		#prints the user name
     
#if __name__ == '__main__':
obj1 = Myshell()
obj1.cmdloop()
     


