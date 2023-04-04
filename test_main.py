import unittest
import logging
from lib.Modbus import Device, LoggingDevice, ModbusRegister
from lib.Publisher import Publisher
import solis_5g_modbus
import lib.Register
from sqlalchemy import create_engine, select, insert
from sqlalchemy.orm import Session

logging.disable(logging.INFO)

class MockPublish():
    def __init__(self, rc=0):
        self.published = {}
        self.rc = rc

    def publish(self, topic, payload):
        class rv():
            def __init__(self, rc=0):
                self.rc = rc

        self.published[topic] = payload
        return rv(self.rc)

class MockRegister(ModbusRegister):
    def __init__(self, register, type=..., function_code=4, decimals=0, signed=False, increment_only=False, validator=None, value=None) -> None:
        super().__init__(register, type, function_code, decimals, signed, increment_only, validator)
        self.value = value

    def read(self, inst=None):
        result = self.value
        for _ in range(0, self.decimals):
            result = result / 10
        return self.validator(result)

class MockInstrument():
    def __init__(self) -> None:
        pass

    def get_instrument(self):
        return None

class TestMain(unittest.TestCase):
    def test_bad_increment_register(self):
        device = Device(MockInstrument)
        publisher = Publisher('solis', mqtt=MockPublish())
        solis_5g_modbus.read_registers_and_publish(
            {
                'total_today': MockRegister(123, increment_only=True, value=1.0)
            },
            device,
            publisher
        )

        self.assertEqual(device.state['total_today'], 1.0)

        solis_5g_modbus.read_registers_and_publish(
            {
                'total_today': MockRegister(123, increment_only=True, value=0.1)
            },
            device,
            publisher
        )

        self.assertEqual(device.state['total_today'], 1.0)

    def test_increment_resets_on_zero_value(self):
        device = Device(MockInstrument)
        publisher = Publisher('solis', mqtt=MockPublish())
        solis_5g_modbus.read_registers_and_publish(
            {
                'total_today': MockRegister(123, increment_only=True, value=1.0)
            },
            device,
            publisher
        )

        self.assertEqual(1.0, device.state['total_today'])

        solis_5g_modbus.read_registers_and_publish(
            {
                'total_today': MockRegister(123, increment_only=True, value=0)
            },
            device,
            publisher
        )

        self.assertEqual(0, device.state['total_today'])

    def test_register_written_to_state_log(self):
        Base = lib.Register.Base
        engine = create_engine("sqlite+pysqlite:///:memory:", echo=True, future=True)
        Base.metadata.create_all(engine)
        session = Session(engine)
        device = LoggingDevice(MockInstrument, session)

        device.read_registers({'my_register': MockRegister(123, value=123)})

        self.assertEqual(session.get(lib.Register.Register, 1).name, 'my_register')
        self.assertEqual(session.get(lib.Register.RegisterHistory, 1).state, 123)

    def test_validaton(self):
        device = Device(MockInstrument)

        values = device.read_registers(
            {
                'test_none_validator_value': MockRegister(123, increment_only=True, value=1.0),
                'test_valid_validator_value': MockRegister(123, increment_only=True, value=1.0, validator=lambda x: x if x == 1.0 else None),
                'test_invalid_validator_value': MockRegister(123, increment_only=True, value=1.0, validator=lambda x: x if x != 1.0 else None)
            }
        )

        self.assertEqual(values['test_none_validator_value'], 1.0)
        self.assertEqual(values['test_valid_validator_value'], 1.0)
        self.assertIsNone(values['test_invalid_validator_value'])

        mqtt = MockPublish()
        publisher = Publisher('solis', mqtt)
        publisher.publish_state(values)
        self.assertEqual(mqtt.published['solis/test_none_validator_value'], 1.0)
        self.assertEqual(mqtt.published['solis/test_valid_validator_value'], 1.0)
        self.assertFalse(mqtt.published.get('solis/test_invalid_validator_value'))

    def test_publish_failure(self):
        mqtt = MockPublish(rc=4)
        publisher = Publisher('solis', mqtt)
        self.assertEqual((True, 4), publisher.publish_state({'test_value': 69}))

