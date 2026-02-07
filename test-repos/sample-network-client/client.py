#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Network Client - Python 2 Legacy Code
A network communication client with Python 2 patterns.
"""

import urllib
import urllib2
import httplib
import socket
import SocketServer
import BaseHTTPServer
import SimpleHTTPServer
import xmlrpclib
import thread
import time


class NetworkClient:
    """A simple network client for HTTP operations."""
    
    def __init__(self, base_url, timeout=30):
        self.base_url = base_url
        self.timeout = timeout
        self.cookies = {}
        self.headers = {
            'User-Agent': 'Python-NetworkClient/1.0',
            'Accept': 'application/json, text/plain, */*',
        }
    
    def get(self, endpoint, params=None):
        """Perform a GET request."""
        url = self.base_url + endpoint
        
        if params:
            query_string = urllib.urlencode(params)
            url = url + '?' + query_string
        
        print "GET %s" % url
        
        try:
            request = urllib2.Request(url)
            for key, value in self.headers.iteritems():
                request.add_header(key, value)
            
            response = urllib2.urlopen(request, timeout=self.timeout)
            data = response.read()
            code = response.getcode()
            
            print "Response: %d (%d bytes)" % (code, len(data))
            return {'status': code, 'data': data}
            
        except urllib2.HTTPError, e:
            print "HTTP Error: %d %s" % (e.code, e.reason)
            return {'status': e.code, 'error': str(e)}
        except urllib2.URLError, e:
            print "URL Error: %s" % e.reason
            return {'status': 0, 'error': str(e)}
        except socket.timeout:
            print "Request timed out!"
            return {'status': 0, 'error': 'timeout'}
    
    def post(self, endpoint, data=None, json_data=None):
        """Perform a POST request."""
        url = self.base_url + endpoint
        
        if json_data:
            import json
            body = json.dumps(json_data)
            self.headers['Content-Type'] = 'application/json'
        elif data:
            body = urllib.urlencode(data)
            self.headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            body = ''
        
        print "POST %s" % url
        print "Body: %s" % body[:100]
        
        try:
            request = urllib2.Request(url, body)
            for key, value in self.headers.iteritems():
                request.add_header(key, value)
            
            response = urllib2.urlopen(request, timeout=self.timeout)
            data = response.read()
            code = response.getcode()
            
            print "Response: %d (%d bytes)" % (code, len(data))
            return {'status': code, 'data': data}
            
        except urllib2.HTTPError, e:
            print "HTTP Error: %d %s" % (e.code, e.reason)
            return {'status': e.code, 'error': str(e)}
        except urllib2.URLError, e:
            print "URL Error: %s" % e.reason
            return {'status': 0, 'error': str(e)}
    
    def download_file(self, url, filepath):
        """Download a file from URL."""
        print "Downloading %s to %s..." % (url, filepath)
        
        try:
            urllib.urlretrieve(url, filepath)
            print "Download complete!"
            return True
        except IOError, e:
            print "Download failed: %s" % e
            return False
    
    def check_connectivity(self, host, port):
        """Check if a host:port is reachable."""
        print "Checking connectivity to %s:%d..." % (host, port)
        
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        try:
            result = sock.connect_ex((host, port))
            if result == 0:
                print "Connection successful!"
                return True
            else:
                print "Connection failed (error code: %d)" % result
                return False
        finally:
            sock.close()


class SimpleAPIClient:
    """A simple XML-RPC client."""
    
    def __init__(self, url):
        self.url = url
        self.server = xmlrpclib.ServerProxy(url)
    
    def call(self, method, *args):
        """Call a remote method."""
        print "Calling %s(%s)..." % (method, ', '.join(map(repr, args)))
        
        try:
            func = getattr(self.server, method)
            result = func(*args)
            print "Result: %s" % repr(result)
            return result
        except xmlrpclib.Fault, e:
            print "XML-RPC Fault: %s" % e
            return None
        except xmlrpclib.ProtocolError, e:
            print "Protocol Error: %s" % e
            return None


def main():
    print "Network Client v1.0"
    print "=" * 40
    
    base_url = raw_input("Enter base URL: ")
    client = NetworkClient(base_url)
    
    print "\nCommands: get, post, download, ping, quit"
    
    while True:
        cmd = raw_input("\nnet> ").strip().lower()
        
        if cmd == 'quit':
            break
        elif cmd == 'get':
            endpoint = raw_input("Endpoint: ")
            result = client.get(endpoint)
            print "Status: %d" % result.get('status', 0)
        elif cmd == 'post':
            endpoint = raw_input("Endpoint: ")
            data_str = raw_input("Data (key=value,key2=value2): ")
            data = dict(item.split('=') for item in data_str.split(',') if '=' in item)
            result = client.post(endpoint, data=data)
            print "Status: %d" % result.get('status', 0)
        elif cmd == 'download':
            url = raw_input("URL: ")
            filepath = raw_input("Save as: ")
            client.download_file(url, filepath)
        elif cmd == 'ping':
            host = raw_input("Host: ")
            port = int(raw_input("Port: "))
            client.check_connectivity(host, port)
        else:
            print "Unknown command: %s" % cmd
    
    print "Goodbye!"


if __name__ == '__main__':
    main()
