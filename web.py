import uasyncio as asyncio
import utime
import machine
import json
from microdot_asyncio import Microdot, send_file, redirect

web = Microdot()

@web.route('/')
async def root(request):
	return send_file("index.html")

@web.route('/uptime')
async def uptime(request):
    return "I've been awake {} seconds".format(int(utime.ticks_us()/1000000))

@web.route("/setup", methods=["GET", "POST"])
async def setup(request):
	if request.method == "POST":
		ap = request.form.get("ssid")
		pw = request.form.get("password")
		im = request.form.get("inmod")
		om = request.form.get("outmod")
		try:
			mp = int(request.form.get("maxpower"))
		except (TypeError, ValueError):
			mp = None
		if all((ap, pw, mp, im, om)):
			with open("config.json", "w") as fp:
				json.dump({
					"ap": ap,
					"pw": pw,
					"mp": mp,
					"im": im,
					"om": om,
				}, fp)
		return redirect("/")
	return send_file("setup.html") # , {"Content-Type": "text/html"}

@web.route("/reboot")
async def reboot(request):
	asyncio.get_event_loop().create_task(_reboot())
	return redirect("/")

async def _reboot():
	await asyncio.sleep(1)
	machine.reset()

async def main():
	print ("Starting web server")
	await web.start_server(port=80)
