import struct
from collections import namedtuple
import uasyncio as asyncio
from machine import Pin
from umodbus.tcp import ModbusTCP

register = namedtuple('register', ('register', 'len', 'val'))

def encode_string(s, length):
	s = s.encode('ascii')
	pad = b'\0' * (2 * length - len(s))
	fmt = '>{}H'.format(length)
	return struct.unpack(fmt, s + pad)

def regs():
	return [
		# Model 1 (mandatory)
		register(40000, 2, (0, 0)), # SunSpec marker will go here
		register(40002, 1, 1),
		register(40003, 1, 66),

		register(40004, 16, encode_string('Generic', 16)), # MANUFACTURER
		register(40020, 16, encode_string('unknown', 16)), # MODEL
		register(40036, 8, encode_string('', 0)), # OPTIONS
		register(40044, 8, encode_string('0.0.1', 8)), # VERSION
		register(40052, 16, encode_string('0', 16)), # SERIAL
		register(40068, 1, 126), # MODBUS address
		register(40069, 1, 0xFFFF), # Padding

		# Model 101 (Single phase inverter)
		register(40070, 1, 101),
		register(40071, 1, 50),
		register(40072, 1, 0), # AMPS
		register(40073, 1, 0), # AMPS A
		register(40074, 1, 0xFFFF), # AMPS B
		register(40075, 1, 0xFFFF), # AMPS C
		register(40076, 1, 0), # Scale factor
		register(40077, 1, 0xFFFF), # Volts AB
		register(40078, 1, 0xFFFF), # Volts BC
		register(40079, 1, 0xFFFF), # Volts CA
		register(40080, 1, 0), # Volts AN
		register(40081, 1, 0xFFFF), # Volts BN
		register(40082, 1, 0xFFFF), # Volts CN
		register(40083, 1, 0xFFFF), # Scale factor = -1
		register(40084, 1, 0), # Total power
		register(40085, 1, 0), # Scale factor
		register(40086, 1, 0), # Freq
		register(40087, 1, 0), # Scale factor
		register(40094, 2, (0, 0)), # 32-bit energy counter
		register(40096, 1, 0), # Scale factor
		register(40103, 1, 0), # Cabinet temperature
		register(40107, 1, 0), # Scale factor
		register(40108, 1, 1), # State, default OFF
		register(40110, 4, (0, 0, 0, 0)), # Events

		# Model 120, Nameplate ratings
		register(40122, 1, 120),
		register(40123, 1, 26),
		register(40124, 1, 4), # DER_TYP = PV
		register(40125, 1, 0), # Power capability
		register(40126, 1, 0), # Scale factor

		# Model 123, immediate controls
		register(40150, 1, 123),
		register(40151, 1, 24),
		register(40155, 1, 100), # WMaxLimPct
		register(40157, 1, 0), # WMaxLimPct_RvrtTms
		register(40159, 1, 0), # WMaxLim_Ena
		register(40173, 1, 0), # WMaxLimPct_SF

		# The end
		register(40176, 4, 4*(0xFFFF,))
	]

class Sunspec(object):
	def __init__(self):
		self.client = ModbusTCP(default_value=0xFFFF)

	def set_voltage(self, phase, value):
		self.client.set_hreg(40080+phase, value)

	def set_current(self, phase, value):
		self.client.set_hreg(40073+phase, value)
	
	def set_power(self, value):
		self.client.set_hreg(40084, value)

	def set_energy(self, value):
		self.client.set_hreg(40094, (value>>16,  value & 0xFFFF))
	
	def set_state(self, value):
		self.client.set_hreg(40108, value)

	def set_manufacturer(self, value):
		self.client.set_hreg(40004, encode_string(value, 16))

	def set_model(self, value):
		self.client.set_hreg(40020, encode_string(value, 16))

	def set_version(self, value):
		self.client.set_hreg(40044, encode_string(value, 8))

	def set_serial(self, value):
		self.client.set_hreg(40052, encode_string(value, 16))

	def set_maxpower(self, value):
		self.client.set_hreg(40125, value)

	def set_enabled(self, enabled):
		# Put SunSpec marker (SunS) at 40000
		self.client.set_hreg(40000, (0x5375, 0x6e53) if enabled else (0, 0))

	def powerlimit(self):
		ena = self.client.get_hreg(40159)
		if ena:
			return self.client.get_hreg(40155)
		return None

	def reset(self):
		self.set_voltage(0, 0); self.set_voltage(1, 0); self.set_voltage(2, 0);
		self.set_current(0, 0); self.set_current(1, 0); self.set_current(2, 0);
		self.set_power(0)
		self.set_state(1) # OFF

	async def main(self):
		print ("Starting Sunspec 2017")

		led = Pin(2, mode=Pin.OUT)

		self.client.bind(local_ip='0.0.0.0', local_port=502)
		self.client.setup_registers(registers=regs())

		while True:
			try:
				# Turn on LED whenever modbus request is processed
				led.value(self.client.process())
			except Exception as e:
				print('Exception during execution: {}'.format(e))

			await asyncio.sleep(0) # Yield control
