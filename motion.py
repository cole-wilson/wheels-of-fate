import socket
import math
import time
from threading import Thread, Lock

REAL = socket.gethostname() == 'wheels-of-fate'

if REAL:
    import pigpio
    pi = pigpio.pi()



class Servo:
    def __init__(self, pin):
        self.pin = pin
        self.angle = 0

    def __repr__(self):
        return f"Servo({self.pin})"

    def set_angle(self, angle):
        if REAL:
            pi.set_servo_pulsewidth(self.pin, 500 + (2000 * (angle/180)))

        return

        delta_angle = angle - self.angle

        t = (abs(delta_angle)/360) * 1

        if delta_angle < 0:
            pi.set_servo_pulsewidth(self.pin, 500)
        else:
            pi.set_servo_pulsewidth(self.pin, 2500)
        time.sleep(t)
        pi.set_servo_pulsewidth(self.pin, 1500)

        self.angle = angle

# 234,14,15,18

servos = {
        4: Servo(2),
        6: Servo(3),
        8: Servo(4),
        10: Servo(14),
        12: Servo(15),
        20: Servo(18)
}


lock = Lock()

def dump(servo, n, lock):
    for i in range(n):
        print(servo, i, "up")
        # lock.acquire()
        servo.set_angle(80)
        time.sleep(0.5)
        # lock.release()
        print(servo, i, "down")
        # lock.acquire()
        servo.set_angle(180)
        time.sleep(0.5)
        # lock.release()
        print(servo, i, "back up")
        # servo.set_angle(0)
        time.sleep(0.5)
        print(servo, i, "done!")
    print("done with all", servo, "exiting")

if REAL:
    for s in servos.values():
        dump(s, 1, None)

def roll(dice):
    print("ROLL!!", dice)
    numbers = {20:0,12:0,10:0,8:0,6:0,4:0}
    for i in dice:
        if i not in numbers:
            numbers[i] = 0
        numbers[i] += 1

    # keys = sorted(numbers.keys())
    for k in [4, 6, 8, 12, 10, 20]:
        print(k)
        dump(servos[k], numbers[k], lock)
        # dump(servos[k], numbers[k])
        # t = Thread(target=dump, args=[servos[k], numbers[k], lock])

        # t.start()
        # time.sleep(.5)
