import minimalmodbus
from . import Register
from sqlalchemy import select
import logging

class ModbusRegister:
    LONG = 'long'
    REGISTER = 'register'

    def __init__(self, register, type=REGISTER, function_code=4, decimals=0, signed=False, increment_only=False, validator=None) -> None:
        self.register = register
        self.type = type
        self.function_code = function_code
        self.decimals = decimals
        self.signed = signed
        self.increment_only = increment_only

        def none_validator(value):
            return value
        self.validator = none_validator if validator is None else validator


    def write(self, inst, value):
        inst.write_register(
            self.register,
            functioncode=self.function_code,
            signed=self.signed,
            value=value
        )

    def read(self, inst):
        if self.type == ModbusRegister.REGISTER:
            return self.validator(
                inst.read_register(
                    self.register,
                    functioncode=self.function_code,
                    number_of_decimals=self.decimals,
                    signed=self.signed
                )
            )
        elif self.type == ModbusRegister.LONG:
            return self.validator(
                inst.read_long(
                    self.register,
                    functioncode=self.function_code,
                    signed=self.signed
                )
            )

class Device:
    def __init__(self, instrument) -> None:
        self.state = {}
        self.instrument = instrument()

    def instrument_setup(self):
        return None

    def register_received(self, name, state):
        pass

    def registers_completed(self):
        pass

    def read_registers(self, registers):
        result = self.state

        for name in registers.keys():
            mod_value = registers[name].read(self.instrument.get_instrument())
            if registers[name].increment_only and name in self.state and mod_value < self.state[name] and mod_value > 0:
                continue

            self.register_received(name, mod_value)
            result[name] = mod_value

        self.registers_completed()
        self.state = result

        return result

    def write_register(self, register, value):
        register.write(self.instrument.get_instrument(), value) 


class Instrument():
    def __init__(self) -> None:
        self.instrument = minimalmodbus.Instrument('/dev/ttyS0', 1, debug=False)
        self.instrument.serial.baudrate = 9600
        self.instrument.serial.timeout = 2

    def get_instrument(self):
        return self.instrument

class LoggingDevice(Device):
    def __init__(self, instrument, session) -> None:
        super().__init__(instrument)
        self.session = session
        self.registers = {}

        for register in session.query(Register.Register).all():
            self.registers[register.name] = register

    def register_received(self, name, state):
        
        if name not in self.registers:
            self.registers[name] = Register.Register(name=name)
            self.session.add(self.registers[name])
        
        my_register = self.registers[name] 
        my_register_state = Register.RegisterHistory(state=state)
        my_register_state.register = my_register
        self.session.add(my_register_state)

    def registers_completed(self):
        self.session.commit()

