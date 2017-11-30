import sys

try:
	import urllib.request as request
except ImportError:
	# Python 2
	import urllib2 as request

class Request(request.Request):
	if (3, 3) < sys.version_info < (3, 4):
		method = None

	def __init__(self, *args, **kwargs):
		"""
		Construct a Request. Usage is the same as for
		`urllib.request.Request` except it also takes an optional `method`
		keyword argument. If supplied, `method` will be used instead of
		the default.

		>>> req = Request('http://example.com')
		>>> req.get_method()
		'GET'

		>>> req.method = 'POST'
		>>> req.get_method()
		'POST'

		Passing None is the same as not passing a value.

		>>> req = Request('http://example.com', method=None)
		>>> req.get_method()
		'GET'

		>>> req = Request('http://example.com', data='xxx')
		>>> req.get_method()
		'POST'

		>>> req = Request('http://example.com', method='PUT')
		>>> req.get_method()
		'PUT'

		Removing the attribute resets the behavior.
		>>> del req.method
		>>> req.get_method()
		'GET'

		>>> class SpecialRequest(Request):
		...     method = 'SPECIAL'
		>>> req = SpecialRequest('http://example.com')
		>>> req.get_method()
		'SPECIAL'

		>>> req = SpecialRequest('http://example.com', method='PATCH')
		>>> req.get_method()
		'PATCH'
		"""
		method = kwargs.pop('method', None)
		request.Request.__init__(self, *args, **kwargs)
		# On Python 3.3, remove the None attribute
		vars(self).pop('method', None)
		if method:
			self.method = method

	def get_method(self):
		return getattr(self, 'method', None) or request.Request.get_method(self)
