from flask_socketio import SocketIO, emit
from flask_socketio import join_room, leave_room
from flask import Flask, render_template, url_for
from threading import Thread, Event, Timer
from random import random
import queue
import time
from pymodbus.client.sync import ModbusTcpClient

app=Flask(__name__)
app.config['SECRET_KEY']='Bruh'
app.config['DEBUG']='Test'

socketio = SocketIO(app)
class ReaderThread(Thread):
    def __init__(self, ip_address='localhost',port='5021'):
        Thread.__init__(self)
        self.alive=Event()
        self.alive.set()
        self.client = ModbusTcpClient(ip_address,port=port)

    def read_device(self):
        client=self.client
        read=False
        data=0

        data_read=client.read_holding_registers(0x00,1)
        data=data_read.registers[0]
        read=True
        return (read,data)

    def run(self):
        try:
            self.client.connect()
        except:
            print('not connected')
        while self.alive.isSet():
            time.sleep(1)
            read=False
            try:
                read, data = self.read_device()
            except:
                print('lost connection')
            if read:
                socketio.emit('newvalue',{'number':data})
            if self.client:
                self.client.close()

    def join(self):
        self.alive.clear()
        Thread.join(self)


uThread=ReaderThread()
uThread.daemon = True

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def test_connect():
    global uThread

    if not uThread.isAlive():
        print("Starting Thread")
        uThread=ReaderThread()
        uThread.daemon = True
        uThread.start()

    print('Client connected')#
    print("Starting Thread")

@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
