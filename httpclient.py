#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, https://github.com/tywtyw2002, and https://github.com/treedust
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
#     http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Do not use urllib's HTTP GET and POST mechanisms.
# Write your own HTTP GET and POST
# The point is to understand what you have to send and get experience with it

import sys
import socket
import re
from typing import Dict, Tuple
from urllib import request
# you may use urllib to encode data appropriately
import urllib.parse

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    #def get_host_port(self,url):

    def connect(self, host, port):
        self.socket = socket.create_connection((host, port))                    
        return None    

    def get_url(self, url: str) -> Tuple[str, str, int]:
        parsedUrl = urllib.parse.urlparse(url)        
        return(
            parsedUrl.hostname, 
            parsedUrl.path if parsedUrl.path != '' else '/', 
            parsedUrl.port or 80)

    def get_request(self, operation : str, host : str, path : str, args : Dict = None) -> str:

        query = None if args is None else urllib.parse.urlencode(args)            
        content = ''

        if operation == 'GET' and query != None:
            path += '?' + query        
        elif operation == 'POST' and query != None:
            content = query + '\r\n\r\n'

        request = f"{operation} {path} HTTP/1.1\r\n{self.get_request_headers(operation, host, query)}\r\n\r\n{content}"

        print (request)
        return request

    def get_request_headers(self, operation, host, content = None) -> str:
        requestHeaders = {               
                'Host' : host,
                'Connection' : 'close',
                'User-Agent' : 'rkeele/1.0.0', 
                'Accept' : '*/*'                
            }
            
        if operation == 'POST' :
            requestHeaders['Content-Type'] = 'application/x-www-form-urlencoded'
            requestHeaders['Content-Length'] = str(0) if content is None else str(len(content))

        return '\r\n'.join(': '.join(x) for x in requestHeaders.items())    

    def get_code(self, data: bytearray) -> int:        
        return int(data[:data.index(b'\r\n')].decode('utf-8').split(' ')[1])

    def get_headers(self, data: bytearray) -> str:
        return str.strip(data[:data.index(b'\r\n\r\n')].decode('utf-8'))

    def get_header(self, headers : str, targetHeader : str) -> str :
        try:                        
            return {k.lower(): v for k, v in dict(x.split(': ') for x in headers.split('\r\n')[1:]).items()}[targetHeader.lower()]               
        except:            
            return None

    def get_charset(self, headers : str) :
        try:
            contentType = self.get_header(headers, 'content-type')
            if contentType is None: return None

            for x in str.strip(contentType.split(';')):
                if 'charset' in x:
                    return str.strip(x.split('=')[1])
            return None
        except:
            return None

    def get_body(self, data: bytearray, encoding = 'utf-8') -> str:            
        try:            
            return str.strip(data[data.index(b'\r\n\r\n'):].decode('utf-8' if encoding is None else encoding, 'ignore'))
        except:
            return str.strip(data[data.index(b'\r\n\r\n'):].decode('utf-8', 'ignore'))
    
    def sendall(self, data : bytearray):
        self.socket.sendall(data.encode('utf-8'))
        
    def close(self):
        try:
            self.socket.close()
        except: pass            
    
    # read everything from the socket
    def recvall_b(self, sock) -> bytearray:
        buffer = bytearray()        
        while True:
            part = sock.recv(1024)                   
            buffer += part
            if (not part):                
                return buffer                    

    def GET(self, url, args : Dict = None) -> HTTPResponse:
        host, path, port = self.get_url(url)          
        try:            
            self.connect(host, port)                                

            request = self.get_request('GET', host, path, args)            
            self.sendall(request)                    
            response = self.recvall_b(self.socket)                                           

            code = self.get_code(response)
            headers = self.get_headers(response)                        
            body = self.get_body(response, self.get_charset(headers))                    

            return HTTPResponse(code, body)
        except socket.gaierror:
            print('Could not resolve host:', host)
            exit()        
        finally:
            self.close()

    def POST(self, url, args : Dict = None) -> HTTPResponse:      
        try:
            host, path, port = self.get_url(url)          
            self.connect(host, port)                                

            request = self.get_request('POST', host, path, args)
            self.sendall(request)                    
            response = self.recvall_b(self.socket)                                           

            code = self.get_code(response)            
            headers = self.get_headers(response)            
            body = self.get_body(response, self.get_charset(headers))                    
            
            return HTTPResponse(code, body)
        except socket.gaierror:
            print('Could not resolve host:', host)
            exit()
        finally:
            self.close()

    def command(self, url, command="GET", args=None):
        if (command == "GET"):
            
            return self.GET(url, args).body

        elif (command == "POST"):
            
            return self.POST(url, args)        

        else:
            return "Unsupported operation."
    
if __name__ == "__main__":
    client = HTTPClient()    
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
        # client.command(sys.argv[2], sys.argv[1])
    else:
        print(client.command( sys.argv[1] ))
        # client.command(sys.argv[1])
