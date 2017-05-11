# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.

import tornado.ioloop as ioloop
import tornado.ioloop
import tornado.web as web

from mycroft.configuration import ConfigurationManager
from mycroft.messagebus.service.ws import WebsocketEventHandler
from mycroft.util import validate_param
from mycroft.lock import Lock  # creates/supports PID locking file


__author__ = 'seanfitz', 'jdorleans'

settings = {
    'debug': True
}

# --------------------------------------

#__co-author__ = 'jcasoft'		# Only for Web Client 	

from datetime import date
import tornado.escape
#import tornado.web
import os
import json
import time

import tornado.httpserver
import tornado.websocket
import tornado.gen
from tornado.options import define, options
import multiprocessing
from netifaces import interfaces, ifaddresses, AF_INET

from mycroft.messagebus.client.ws import WebsocketClient
from mycroft.messagebus.message import Message
from threading import Thread


ws = None

 
# --------------------------------------
clients = [] 

for ifaceName in interfaces():
	ip = addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )][0]

input_queue = multiprocessing.Queue()
output_queue = multiprocessing.Queue()


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html',ip=ip)

class StaticFileHandler(tornado.web.RequestHandler):
	def get(self):
		self.render('main.js')
 
class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        clients.append(self)
	self.write_message("Mycroft connected OK")
        self.write_message("Welcome to Mycroft")
 
    def on_message(self, message):
	utterance = json.dumps(message)
	msg_recv = "- " + utterance

	if utterance:
	    self.write_message(msg_recv)
	    lang = 'en-us'
	    data = {"lang": lang, "session": "", "utterances": [utterance]}
    	    ws.emit(Message('recognizer_loop:utterance', data))
            t = Thread(target = self.newThread)
            t.start()



    def newThread(self):
	global wait_response
	global skill_response
        timeout = 0
        while wait_response:
	    wait_response = True
            time.sleep(1)
	    timeout = timeout + 1

	skill_response = skill_response.replace("Checking for Updates","")
	skill_response = skill_response.replace("Skills Updated. Mycroft is ready","")
	self.write_message(skill_response)

	skill_response = ""
	wait_response = True

        timeout = 0
        while timeout < 10 or wait_response:
            time.sleep(1)
	    timeout = timeout + 1
	     

	if len(skill_response) > 0:
		self.write_message(skill_response)

	wait_response = True
	skill_response = ""

 
    def on_close(self):
        clients.remove(self)



def connect():
    ws.run_forever()


def handle_speak(event):
    response = event.data['utterance']
    global skill_response, wait_response
    skill_response = ""
    wait_response = False
    skill_response = response
# --------------------------------------



def main():

    global skill_response, wait_response
    wait_response = True
    skill_response = ""

    global ws
    ws = WebsocketClient()
    event_thread = Thread(target=connect)
    event_thread.setDaemon(True)
    event_thread.start()

    ws.on('speak', handle_speak)

    import tornado.options
    lock = Lock("service")
    tornado.options.parse_command_line()
    config = ConfigurationManager.get().get("websocket")

    host = config.get("host")
    port = config.get("port")
    route = config.get("route")
    validate_param(host, "websocket.host")
    validate_param(port, "websocket.port")
    validate_param(route, "websocket.route")

    routes = [
        (route, WebsocketEventHandler),
	tornado.web.url(r"/", IndexHandler),
	tornado.web.url(r"/static/(.*)", tornado.web.StaticFileHandler, {'path':  './'}),
	tornado.web.url(r"/ws", WebSocketHandler)
    ]

    settings = {
        "debug": True,
        "template_path": os.path.join(os.path.dirname(__file__), "templates"),
        "static_path": os.path.join(os.path.dirname(__file__), "static"),
    }
    

    application = web.Application(routes, **settings)
    httpServer = tornado.httpserver.HTTPServer(application)

    tornado.options.parse_command_line()
    httpServer.listen(port)

    tornado.ioloop.IOLoop.instance().start()



if __name__ == "__main__":
    main()


