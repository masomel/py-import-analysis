import requests
import sys
import json

GIST_API_URL = 'https://api.github.com/gists'

class GistError(Exception):
	def __init__(self, value):
		self.value = value
	def __str__(self):
		repr(self.value)

def save_file(file_name=None):
	if not file_name:
		if len(sys.argv) <= 1:
			raise GistError("No file specified.")
			return
		file_name = sys.argv[1]
	try: 
		with open(file_name, 'r') as f:
			file_contents = f.read()
	except IOError:
		raise GistError("Cannot open file: {0}. File may not exist, " \
		"or you may not have permission to access it.".format(file_name))
		return

	data = { "files": {	file_name: { "content": file_contents }	} }
	try:
		r = requests.post(GIST_API_URL, data=json.dumps(data))
		url = r.json()['html_url']
		return url
	except requests.exceptions.ConnectionError:
		raise GistError("Could not connect to Github's API. Is your internet connection working?")
		return

if __name__ == '__main__':
	try:
		url = save_file()
		print url
	except GistError as e:
		print e.value
