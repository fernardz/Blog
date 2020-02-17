from tcp_reader import app
from gevent.pywsgi import WSGIServer

server=WSGIServer(('0.0.0.0', 5000), app)
server.serve_forever()
