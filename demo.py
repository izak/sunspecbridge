import uasyncio as asyncio

async def main(sunspec):
	print ("Starting Demo")

	sunspec.set_manufacturer('Demo')
	sunspec.set_model('Generic')
	sunspec.set_serial('DEADBEEF')
	sunspec.set_version('0.1')
	sunspec.set_state(4) # MPPT
	sunspec.set_energy(12000)

	sunspec.set_enabled(True)

	while True:
		for v, i in ((2300, 1), (2310, 1), (2320, 1)):
			# Solis registers
			sunspec.set_voltage(0, v)
			sunspec.set_current(0, i)
			sunspec.set_power((v * i) // 10)

			await asyncio.sleep(3)
