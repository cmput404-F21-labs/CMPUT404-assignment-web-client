#!/usr/bin/env python3
# coding: utf-8
# Copyright 2016 Abram Hindle, Uladzimir Bondarau, https://github.com/tywtyw2002, and https://github.com/treedust
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
# you may use urllib to encode data appropriately
from urllib.parse import urlparse

CARRIAGE_RETURN = "\r\n"

def help():
    print("httpclient.py [GET/POST] [URL]\n")

class HTTPResponse(object):
    def __init__(self, code=200, body=""):
        self.code = code
        self.body = body

class HTTPClient(object):
    # Parses url
    # ex: https://www.youtube.com/watch?v=dQw4w9WgXcQ#t=98s
    # {'host': 'www.youtube.com', 'path': '/watch', 'query': 'v=dQw4w9WgXcQ', 'fragmentation': 't=98s', 'port': 80}
    def parse_url(self, url):
        parsed_url = urlparse(url)
        url_params = (url + "?").split('?')[1].split('#')
        url_query = url_params[0]
        url_fragmentation = ""
        if (len(url_params) > 1):
            url_fragmentation = url_params[1]

        url_details = {
            "host": parsed_url.hostname,
            "path": parsed_url.path,
            "query": url_query,
            "fragmentation": url_fragmentation,
            "port": parsed_url.port
        }

        if (url_details["path"] == ''):
            url_details.update({"path":'/'})

        if (not url_details["port"]):
            url_details.update({"port":80})

        return url_details

    # Decompose response from the destination on status code and body
    def parse_response(self, response):
        parsed_response = response.split(CARRIAGE_RETURN+CARRIAGE_RETURN)
        response_line = parsed_response[0].split(CARRIAGE_RETURN)[0]
        response = {
            'code': int(response_line.split()[1]),
            'body': parsed_response[1]
        }
        return response

    # Construct payload based on method and required headers and params
    def construct_payload(self, url_details, command, args):
        url = url_details["path"]
        request_host = "HOST: %s\r\n" % (url_details["host"]) 
        request_close = "Connection: close\r\n"
        if (command == "GET"):
            if (url_details["query"] != ""):
                url = url + "?" + url_details["query"]
            if (url_details["fragmentation"] != ""):
                url = url + "#" + url_details["fragmentation"]

            request_line = "%s %s HTTP/1.1\r\n" % (command, url)

            return  "".join([request_line, request_host, request_close, CARRIAGE_RETURN])
        elif (command == "POST"):
            if (url_details["fragmentation"] != ""):
                url = url + "#" + url_details["fragmentation"]
            request_line = "%s %s HTTP/1.1\r\n" % (command, url)

            body = ""
            if (args):
                for (key, value) in args.items():
                    body += "%s=%s&" % (key, value)
            if (url_details["query"] != ""):
                queries = url_details.split('&')
                for query_option in queries:
                    key = query_option.split('=')[0]
                    value = query_option.split('=')[1]
                    body += "%s=%s&" % (key, value)

            body = body[:-1]

            request_content = "Content-Type: application/x-www-form-urlencoded\r\n"
            request_content_length = "Content-Length: %s\r\n" % (len(body))
            request_body = "%s\r\n" % (body)
            
            return  "".join([request_line, request_host, request_content, request_content_length, request_close, CARRIAGE_RETURN, request_body, CARRIAGE_RETURN])

    def handle_request(self, command, url, args):
        # decompose user url
        url_details = self.parse_url(url)
        # connect to host
        self.connect(url_details.get("host"), url_details.get("port"))

        # send user request to dst
        payload = self.construct_payload(url_details, command, args)
        self.sendall(payload)

        # receive data from dst
        data = self.recvall(self.socket)
        # termine the connection
        self.close()

        # parse response and complete the request
        response = self.parse_response(data)

        self.std_out(response)

        return HTTPResponse(response['code'], response['body'])

    def GET(self, url, args=None):
        return self.handle_request("GET", url, args)

    def POST(self, url, args=None):
        return self.handle_request("POST", url, args)

    # Handle implemented methods
    def command(self, url, command="GET", args=None):
        if (command == "POST"):
            return self.POST( url, args )
        elif (command == "GET"):
            return self.GET( url, args )
        else:
            return "\n\r*** Method not supported. ***\n\r"

    def std_out(self, response):
        print(response['code'])
        print(response['body'])

    def sendall(self, data):
        self.socket.sendall(data.encode('utf-8'))
    def recvall(self, sock):
        # read everything from the socket
        buffer = bytearray()
        done = False
        while not done:
            part = sock.recv(1024)
            if (part):
                buffer.extend(part)
            else:
                done = not part
        return buffer.decode('utf-8')
        
    def connect(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        return None
    def close(self):
        self.socket.close()
    
if __name__ == "__main__":
    client = HTTPClient()
    command = "GET"
    if (len(sys.argv) <= 1):
        help()
        sys.exit(1)
    elif (len(sys.argv) == 3):
        print(client.command( sys.argv[2], sys.argv[1] ))
    else:
        print(client.command( sys.argv[1] ))
