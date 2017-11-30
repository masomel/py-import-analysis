from __init__ import *

try:
	url = save_file()
	print url
except GistError as e:
	print e.value
