import functools
import contextlib


try:
	suppress_file_not_found = functools.partial(
		contextlib.suppress,
		FileNotFoundError,
	)
except Exception:
	# Python 3.3 doesn't have contextlib.suppress
	# nor FileNotFoundError.
	import contextlib2
	suppress_file_not_found = functools.partial(
		contextlib2.suppress,
		OSError,
	)
