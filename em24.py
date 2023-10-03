import struct
import uasyncio as asyncio
from umodbus.serial import Serial as ModbusRTUMaster

def s32l(*args):
	return struct.unpack('<i', struct.pack('<2H', *args))[0]

async def main(sunspec):
	print ("Starting Modbus-RTU")
	host = ModbusRTUMaster(
		baudrate=9600,
		pins = (17, 16),
		uart_id = 1,
		ctrl_pin = 4)

	timeout = 3

	sunspec.set_manufacturer('Carlo Gavazzi')
	sunspec.set_model('EM24')

	# Read serial number
	while True:
		try:
			registers = host.read_input_registers(1, 0x1300, 7, signed=False)
		except OSError:
			print("No response, retrying...")
			await asyncio.sleep(10)
			continue
		else:
			serial = struct.unpack('14s',
				struct.pack('>7H', *registers))[0].decode("UTF-8")
			sunspec.set_serial(serial)
			break

	# Enable
	sunspec.set_enabled(True)
	timeout = 3
	while True:
		try:
			# EM24 registers
			registers = host.read_input_registers(1, 0, 6, signed=False)
			voltage = s32l(*registers[0:2])
			sunspec.set_voltage(0, voltage)
			sunspec.set_voltage(1, s32l(*registers[2:4]))
			sunspec.set_voltage(2, s32l(*registers[4:6]))

			registers = host.read_input_registers(1, 0x0C, 6, signed=False)
			sunspec.set_current(0, s32l(*registers[0:2]))
			sunspec.set_current(1, s32l(*registers[2:4]))
			sunspec.set_current(2, s32l(*registers[4:6]))

			power = s32l(*host.read_input_registers(1, 0x28, 2, signed=False))
			sunspec.set_power(power)
			sunspec.set_state(4 if power > 0 else 2) # MPPT/Sleeping

			sunspec.set_energy(
				s32l(*host.read_input_registers(1, 0x3E, 2, signed=False)))
			print (voltage*0.1)
		except OSError:
			# No data from slave
			timeout = min(timeout-1, 0)
		else:
			timeout = 3

		if timeout == 0:
			sunspec.reset()

		await asyncio.sleep(1)
