import numpy as np
from functools import reduce
from http import server
from threading import Thread, Condition
import socketserver
import io
import websockets
import time
import os
from motion import roll
from threading import Thread
import websockets.exceptions
import websockets.asyncio.server
import asyncio
import json
# import scipy
import socket

REAL = socket.gethostname() == 'wheels-of-fate'

if REAL:
    import picamera2
    from picamera2.encoders import JpegEncoder
    from picamera2.outputs import FileOutput
    import pigpio
    pi = pigpio.pi()


class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        self.frame = None
        self.condition = Condition()

    def write(self, buf):
        with self.condition:
            self.frame = buf
            self.condition.notify_all()

class StreamingHandler(server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/stream.mjpg':
            self.send_response(200)
            self.send_header('Age', 0)
            self.send_header('Cache-Control', 'no-cache, private')
            self.send_header('Pragma', 'no-cache')
            self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
            self.end_headers()
            try:
                while True:
                    with output.condition:
                        output.condition.wait()
                        frame = output.frame
                    self.wfile.write(b'--FRAME\r\n')
                    self.send_header('Content-Type', 'image/jpeg')
                    self.send_header('Content-Length', len(frame))
                    self.end_headers()
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
            except Exception as e:
                print("camera stream error",e)
        else:
            return super().do_GET()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True

output = StreamingOutput()

def serve():
    global output
    # os.chdir('ds')

    address = ('', 8000)

    serverc = StreamingServer
    serverc.allow_reuse_address = True
    serverc.allow_reuse_port = True
    server = serverc(address, StreamingHandler)

    print('serving ds on', address)

    if REAL:
        print("ASD")
        camera = picamera2.Picamera2()
        print("DSA")
        camera.configure(camera.create_video_configuration(main={"size": (270, 180)}))
        with camera:
            # output = StreamingOutput()
            # camera.start_recording(output, format='mjpeg')
            camera.start_recording(JpegEncoder(), FileOutput(output))
            try:
                server.serve_forever()
            finally:
                camera.stop_recording()
    else:
        server.serve_forever()


DICE = []
conns = []
async def handler(conn):
    global conns
    conns.append(conn)
    global DICE
    try:
        while True:
            print("loop start")
            data = json.loads(await conn.recv())
            DICE = data["dice"]
            print("got", data)
            if data["type"] == "convolve":
                print('calculating...')
                databack = json.dumps(convolve(data["dice"]))
                # print('calculated', databack)
                await conn.send(databack)
                # print("sent", databack)
            elif data["type"] == "advantage":
                vals = [0]*20
                for a in range(1, 21):
                    for b in range(1, 21):
                        vals[max(a, b)-1] += 1
                total = sum(vals)
                vals = list(map(lambda i: float(int(i)/total), vals))
                await conn.send(json.dumps(vals))
            elif data["type"] == "disadvantage":
                vals = [0]*20
                for a in range(1, 21):
                    for b in range(1, 21):
                        vals[min(a, b)-1] += 1
                total = sum(vals)
                vals = list(map(lambda i: float(int(i)/total), vals))

                await conn.send(json.dumps(vals))
            else:
                roll(data["dice"])
                ...

    except (websockets.exceptions.ConnectionClosed, websockets.exceptions.ConnectionClosedError, websockets.exceptions.ConnectionClosedOK, ConnectionResetError) as e:
        print("exception!!", e)

last = 0

async def listen_pin():
    global last

    print('listening')
    pi.set_mode(17, pigpio.INPUT)  # GPIO  4 as input
    while True:
        if pi.wait_for_edge(17) and (time.time()-last) >= 10:
            last = time.time()
            print("Rising edge detected")
            for c in conns:
                try:
                    print(c)
                except:
                    pass
                await c.send("true")
        else:
           print("wait for edge timed out")

if REAL:
    t2 = Thread(target=asyncio.run, args=[listen_pin()])
    t2.start()

def ws_listen():
    host = ""
    port = 9191
    async def main():
        async with websockets.asyncio.server.serve(handler, host, port):
            await asyncio.get_running_loop().create_future()  # run forever

    asyncio.run(main())

def convolve(dice):
    if len(dice) == 0:
        return []
    dice = list(map(lambda i: (np.array([1.0]*i)), dice))
    result = reduce(np.convolve, dice)
    total = sum(result)
    return list(map(lambda i: float(int(i)/total), result))

t = Thread(target=ws_listen)
t.start()
try:
    serve()
except Exception as err:
    print(err)
t.join()
if REAL:
    t2.join()
