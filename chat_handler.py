import tornado.ioloop
import tornado.web
import tornado.websocket
import os
import logging
from tornado.options import define, options, parse_command_line

define("port", default=8888, help="run on the given port", type=int)


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")


class ChatHandler(tornado.websocket.WebSocketHandler):
    clients = dict()
    latest_messages = []
    MAX_CACHE_SIZE = 3

    def open(self, *args):
        self.id = self.get_argument("user_token")
        print self.id, " user_token, msg length:" + str(len(self.latest_messages))
        # TODO check if it is valid id
        self.stream.set_nodelay(True)
        self.clients[self.id] = {"id": self.id, "object": self}
        # send history message
        for msg in self.latest_messages:
            self.write_message(msg)

    def on_close(self):
        print "WebSocket closed"
        if self.id in self.clients:
            del self.clients[self.id]
        self.send_to_all("%s left the room:" % self.id)

    @classmethod
    def record_latest_message(cls, chat):
        cls.latest_messages.append(chat)
        if len(cls.latest_messages) > cls.MAX_CACHE_SIZE:
            cls.latest_messages = cls.latest_messages[-cls.MAX_CACHE_SIZE:]
            # TODO put it into redis

    @classmethod
    def send_to_all(cls, message):
        logging.info("sending message to %d waiters", len(cls.clients))
        for id, waiter in cls.clients.items():
            try:
                waiter["object"].write_message(message)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        logging.info("got message %r", message)
        # TODO json message format for various message type
        # parsed = tornado.escape.json_decode(message)
        # chat = {
        #     "id": str(uuid.uuid4()),
        #     "body": parsed["body"],
        #     }
        # chat["html"] = tornado.escape.to_basestring(
        #     self.render_string("message.html", message=chat))
        """
        when we receive some message we want some message handler..
        for this example i will just print message to console
        """
        print "Client %s received a message : %s" % (self.id, message)
        # self.write_message(u"You said: " + message)
        self.record_latest_message(message)
        self.send_to_all(message)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', IndexHandler),
            (r'/chat', ChatHandler),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            xsrf_cookies=True,
        )
        super(Application, self).__init__(handlers, **settings)

app = Application()

if __name__ == '__main__':
    parse_command_line()
    app.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()