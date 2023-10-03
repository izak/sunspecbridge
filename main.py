import time
import json
import uasyncio as asyncio
import network
from machine import Pin
import web

def get_config():
	try:
		with open("config.json", "r") as fp:
			d = json.load(fp)
	except (ValueError, OSError):
		return None, None, None, None, None
	else:
		try:
			return (d["ap"], d["pw"], d["mp"], d["im"], d["om"])
		except KeyError:
			return None, None, None, None, None

def main():
	# Wait before boot, and check GPIO0. If it is pulled down, then
	# skip network config and enable AP.
	enable_ap = False
	led = Pin(2, mode=Pin.OUT)
	button = Pin(0, mode=Pin.IN, pull=Pin.PULL_UP)
	for i in range(15):
		led.value(not led.value())
		enable_ap = enable_ap or (button.value() == 0)
		time.sleep(0.2)

	# Wlan connection details, and maximum power
	ap, pw, maxpower, inmod, outmod = get_config()

	# Enable AP if config could not be loaded
	enable_ap = enable_ap or ap is None

	# Start AP if button was pressed or config not done
	if enable_ap:
		print ("Starting AP mode")
		wlan = network.WLAN(network.AP_IF)
	else:
		print ("Starting STATION mode")
		wlan = network.WLAN(network.STA_IF)

	# Handle interface already up during a soft-boot
	if wlan.active() and wlan.isconnected():
		wlan.disconnect()
		time.sleep(1)

	wlan.active(True)

	if enable_ap:
		wlan.config(essid="SunspecBridge")
		while True:
			print("Waiting for AP to come up...")
			if wlan.active():
				print("AP available as {}".format(wlan.ifconfig()[0]))
				break
			time.sleep(2)
	else:
		wlan.connect(ap, pw)
		while True:
			print("Waiting for WiFi connection...")
			if wlan.isconnected():
				print("Connected to WiFi as {}".format(wlan.ifconfig()[0]))
				break
			time.sleep(2)

	# Import modules
	try:
		sunspec = __import__(outmod)
		pvinverter = __import__(inmod)
	except ImportError:
		print ("Error loading conversion layer!")
		asyncio.run(web.main())
	else:
		gc.collect()
		print ("Memory free", gc.mem_free())

		# Main loop
		print ("Starting main loop")
		sunspec_service = sunspec.Sunspec()
		sunspec_service.set_maxpower(maxpower)
		asyncio.run(asyncio.gather(web.main(), sunspec_service.main(), pvinverter.main(sunspec_service)))

if __name__ == "__main__":
	main()
