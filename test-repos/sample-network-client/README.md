# Sample Network Client (Python 2)

A legacy network communication client for testing migration.

## Python 2 Patterns Used:
- `print` statements
- `urllib` module functions (`urlencode`, `urlretrieve`)
- `urllib2` module
- `httplib` module (should be `http.client`)
- `SocketServer` module (should be `socketserver`)
- `BaseHTTPServer` module (should be `http.server`)
- `SimpleHTTPServer` module
- `xmlrpclib` module (should be `xmlrpc.client`)
- `thread` module
- `raw_input()` function
- `dict.iteritems()` method
- Old-style exception handling
- `%` string formatting
