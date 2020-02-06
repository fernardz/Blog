# import the modbus libraries we need
from pymodbus.server.asynchronous import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext

#We use twisted for the the continues call, could also use a thread for updating
#the values
from twisted.internet.task import LoopingCall

#This is the function that will be called periodically
# we define which registers and to read and modify
def updating_writer(a):
    context = a[0]
    register = 3
    slave_id = 0x00
    address = 0x00
    #Read the current values
    values = context[slave_id].getValues(register, address, count=5)
    values = [v + 1 for v in values]
    #Increase the current values
    context[slave_id].setValues(register, address, values)

#this actually setup our server and the content of the registers across
# we set the context to single as we only have the one slave context
def run_updating_server():
    store = ModbusSlaveContext(
        di=ModbusSequentialDataBlock(0, [17]*100),
        co=ModbusSequentialDataBlock(0, [17]*100),
        hr=ModbusSequentialDataBlock(0, [17]*100),
        ir=ModbusSequentialDataBlock(0, [17]*100))
    context = ModbusServerContext(slaves=store, single=True)

#Define how often the update the values and start the server
    time = 5  # 5 seconds delay
    loop = LoopingCall(f=updating_writer, a=(context,))
    loop.start(time, now=False) # initially delay by time
    StartTcpServer(context, address=("0.0.0.0", 5020))


if __name__ == "__main__":
    run_updating_server()
