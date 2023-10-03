import struct
import uasyncio as asyncio
from umodbus.serial import Serial as ModbusRTUMaster

def u32b(*args):
	return struct.unpack('>I', struct.pack('>2H', *args))[0]

async def main(sunspec):
	print ("Starting Solis1P Modbus-RTU")
	host = ModbusRTUMaster(
		baudrate=9600,
		pins = (17, 16),
		uart_id = 1,
		ctrl_pin = 4)

	timeout = 3

	sunspec.set_manufacturer('Solis')
	sunspec.set_model('Generic')

	while True:
		try:
			# Read serial number
			sregs = host.read_input_registers(1, 3060, 4, signed=False)
			vregs = host.read_input_registers(1, 3000, 1, signed=False)
		except OSError:
			print("No modbus-RTU response, retrying...")
			await asyncio.sleep(10)
			continue
		else:
			serial = "".join(["".join(reversed("{:x}".format(x))) for x in sregs])
			sunspec.set_serial(serial)
			sunspec.set_version("{:x}".format(vregs[0]))
			break

	# Enable
	sunspec.set_enabled(True)
	while True:
		try:
			# Solis registers
			registers = host.read_input_registers(1, 3035, 2, signed=False)
			sunspec.set_voltage(0, registers[0])
			sunspec.set_current(0, registers[1])

			power = u32b(*host.read_input_registers(1, 3004, 2, signed=False))
			sunspec.set_power(power)
			sunspec.set_state(4 if power > 0 else 2) # MPPT/Sleeping

			sunspec.set_energy(
				u32b(*host.read_input_registers(1, 3008, 2, signed=False))*1000)

			# Update power limit
			limit = sunspec.powerlimit()
			host.write_single_register(1, 3049,
				10000 if limit is None else limit * 100)

		except OSError:
			# No data from slave
			timeout = min(timeout-1, 0)
		else:
			timeout = 3

		if timeout == 0:
			sunspec.reset()

		await asyncio.sleep(1)
