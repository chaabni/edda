# Copyright 2009-2012 10gen, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#!/usr/bin/env python

import os
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

import socket
import webbrowser

try:
    import json
except ImportError:
    import simplejson as json
import threading

from time import sleep

data = None
server_list = None
admin = None

class ThreadClass(threading.Thread):

    def run(self):
        """Open page and send GET request to server"""
        # open the JS page
        url = "http://localhost:28000"
        try:
            webbrowser.open(url, 1, True)
        except webbrowser.Error:
            print "Error: Unable to launch webpage"
            print "Please try again with a different default browser"
    # end of ThreadClass


def send_to_js(frames, servers, info):
    """Sends information to the JavaScript
    client"""

    global data
    global server_list
    global admin

    admin = info
    data = frames
    server_list = servers

    # fork here!
    t = ThreadClass()
    t.start()
    # parent starts a server listening on localhost:27080
    # child opens page to send GET request to server
    # open socket, bind and listen
    print "==========================================================="
    print "Opening server, kill with Ctrl+C once logl.html has opened"
    print "==========================================================="
    try:
        server = HTTPServer(('', 28000), LoglHTTPRequest)
    except socket.error, (value, message):
        if value == 98:
            print "Error: could not bind to localhost:28018"
        else:
            print message
            return
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.socket.close()
        # return upon completion
        print "Done serving, exiting"
        return


class LoglHTTPRequest(BaseHTTPRequestHandler):

    mimetypes = mimetypes = {"html": "text/html",
                  "htm": "text/html",
                  "gif": "image/gif",
                  "jpg": "image/jpeg",
                  "png": "image/png",
                  "json": "application/json",
                  "css": "text/css",
                  "js": "text/javascript",
                  "ico": "image/vnd.microsoft.icon"}

    docroot = str(os.path.dirname(os.path.abspath(__file__)))
    docroot += "/display/"

    def process_uri(self, method):
        """Process the uri"""
        if method == "GET":
            (uri, q, args) = self.path.partition('?')
        else:
            return

        uri = uri.strip('/')

        # default "/" to "logl.html"
        if len(uri) == 0:
            uri = "logl.html"

        # find type of file
        (temp, dot, type) = uri.rpartition('.')
        if len(dot) == 0:
            type = ""

        return (uri, args, type)

    def do_GET(self):
        # do nothing with message
        # return data
        (uri, args, type) = self.process_uri("GET")

        if len(type) == 0:
            return

        if type == "admin":
            admin = {}
            admin["total_frame_count"] = len(data)
            self.wfile.write(json.dumps(admin))

        elif type == "all_frames":
            self.wfile.write(json.dumps(data))

        # format of a batch request is
        # 'start-end.batch'
        elif type == "batch":
            uri = uri[:len(uri) - 6]
            parts = uri.partition("-")
            try:
                start = int(parts[0])
            except ValueError:
                start = 0
            try:
                end = int(parts[2])
            except ValueError:
                end = 0
            batch = {}

            # check for entries out of range
            if end < 0:
                return
            if start < 0:
                start = 0;
            if start >= len(data):
                return
            if end >= len(data):
                end = len(data) - 1

            for i in range(start, end):
                if not str(i) in data:
                    break
                batch[str(i)] = data[str(i)];
            self.wfile.write(json.dumps(batch))


        elif type == "servers":
            self.wfile.write(json.dumps(server_list))

        elif type in self.mimetypes and os.path.exists(self.docroot + uri):
            f = open(self.docroot + uri, 'r')

            self.send_response(200, 'OK')
            self.send_header('Content-type', self.mimetypes[type])
            self.end_headers()
            self.wfile.write(f.read())
            f.close()
            return

        else:
            self.send_error(404, 'File Not Found: ' + uri)
            return