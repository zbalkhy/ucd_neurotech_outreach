import sys
from XRPLib.defaults import *
import time

def main():
    while True:
        line = sys.stdin.readline()
        if not line:
            continue
        
        cmd = line.strip()
        if cmd == 'eyesOpen':
            drivetrain.set_speed(0, 0)
        elif cmd == 'eyesClosed':
            drivetrain.set_speed(7.0, 7.0)

if __name__ == "__main__":
    main()