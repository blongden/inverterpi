import time
import os
import paho.mqtt.client as mqtt
import logging

from lib.Modbus import LoggingDevice, Instrument, ModbusRegister
from lib.Publisher import Publisher
from lib.Register import Base

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

registers = {
    'hour': ModbusRegister(33025),
    'min': ModbusRegister(33026),
    'sec': ModbusRegister(33027),
    'dc_voltage_1': ModbusRegister(33049, decimals=1),
    'dc_current_1': ModbusRegister(33050, decimals=1),
    'dc_voltage_2': ModbusRegister(33051, decimals=1),
    'dc_current_2': ModbusRegister(33052, decimals=1),
    'inverter_temp': ModbusRegister(33093, decimals=1),
    'battery_power': ModbusRegister(33149, type=ModbusRegister.LONG, signed=True),
    'battery_voltage': ModbusRegister(33133, decimals=1),
    'battery_current': ModbusRegister(33134, decimals=1, signed=True),
    'battery_status': ModbusRegister(33135),
    'battery_soc': ModbusRegister(33139),
    'battery_soh': ModbusRegister(33140),
    'grid_power': ModbusRegister(33130, ModbusRegister.LONG, signed=True),
    'grid_imported_today': ModbusRegister(33171, decimals=1, increment_only=True),
    'grid_exported_today': ModbusRegister(33175, decimals=1, increment_only=True),
    'grid_frequency': ModbusRegister(33094, decimals=2),
    'battery_fault_1': ModbusRegister(33145),
    'battery_fault_2': ModbusRegister(33146),
    'house_power': ModbusRegister(33147),
    'current_generation': ModbusRegister(33057, type=ModbusRegister.LONG),
    'total_active_power': ModbusRegister(33263, type=ModbusRegister.LONG, signed=True),
    'generation_today': ModbusRegister(33035, decimals=1, increment_only=True),
    'battery_charge_today': ModbusRegister(33163, decimals=1, increment_only=True),
    'battery_discharge_today': ModbusRegister(33167, decimals=1, increment_only=True),
    'storage_mode': ModbusRegister(43110, function_code=3),
    'battery_charge_max_amps': ModbusRegister(43141, decimals=1, function_code=3)
}

def read_registers_and_publish(registers, device, publisher):
    state = device.read_registers(registers)
    (error, rc) = publisher.publish_state(state)
    if error:
        if rc == mqtt.MQTT_ERR_NO_CONN:
            logging.warning('MQTT is disconnected, should reconnect!')
        if rc == mqtt.MQTT_ERR_SUCCESS:
            logging.info('MQTT payload confirmed success')
    
    logging.info(state)

def get_mqtt_client(device):
    client = mqtt.Client()
    charge_mode_register = ModbusRegister(43110, function_code=6)
    charge_maxamps_register = ModbusRegister(43141, function_code=6)

    def on_connect(client, userdata, flags, rc):
        client.subscribe("solis/charge_mode")
        client.subscribe("solis/charge_maxamps")
        logging.info('Connected to MQTT')

    def on_message(client, userdata, msg):
        if msg.topic == 'solis/charge_mode':
            device.write_register(charge_mode_register, int(msg.payload))
        elif msg.topic == 'solis/charge_maxamps':
            device.write_register(charge_maxamps_register, int(msg.payload))

        logging.info(f'MQTT message received: {msg}')

    client.on_connect = on_connect
    client.on_message = on_message

    client.username_pw_set(
        os.environ.get('MQTT_USERNAME', None),
        os.environ.get('MQTT_PASSWORD', None),
    )

    client.connect(os.environ.get('MQTT_SERVER'))

    return client

if __name__ == "__main__":
    logging.basicConfig(format="%(asctime)s %(message)s", level=os.environ.get('LOG_LEVEL', logging.WARNING))    

    engine = create_engine(f"sqlite+pysqlite:///{os.path.dirname(os.path.realpath(__file__))}/inverter.db", future=True)
    Base.metadata.create_all(engine)
    session = Session(engine)
    device = LoggingDevice(Instrument, session)
    client = get_mqtt_client(device)
    publisher = Publisher(os.environ.get('MQTT_CLIENT_ID', 'solis'), client)

    i = 0
    while True:
        rc = client.loop()
        if rc != mqtt.MQTT_ERR_SUCCESS:
            print("mqtt has disconnected, reconnecting!")
            client.reconnect()

        if i % 6 == 0:
            logging.debug("Reading registers and publishing")
            read_registers_and_publish(registers, device, publisher)
            logging.debug("Reading registers and publishing complete")
        i=i+1
        time.sleep(1)
