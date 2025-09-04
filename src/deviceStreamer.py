import socket
import time
from common import RAW_DATA
import numpy as np
import threading

class DeviceStreamer():
    def __init__(self, host: str, port: int, retry_sec: int, user_context: dict):
            self.host: str = host
            self.port: int = port
            self.retry_sec: int = retry_sec
            self.user_context: dict = user_context
            self._stream_thread: threading.Thread = None


    def generate_sample(self):
        """
        Generator that yields (t_ms:int, value:float) from 't_ms,value' lines.
        Auto-reconnects on errors/disconnects. 
        """
        print("stream thread")
        buf = b""
        while True:
            s = None
            try:
                s = socket.create_connection((self.host, self.port), timeout=5)
                s.settimeout(None)  # blocking
                print(f"[connected] {self.host}:{self.port}")
                buf = b""
                while True:
                    chunk = s.recv(4096)
                    if not chunk:
                        raise ConnectionError("server closed connection")
                    buf += chunk
                    while b"\n" in buf:
                        line, buf = buf.split(b"\n", 1)
                        line = line.strip()
                        if not line or line.startswith(b"#"):
                            continue
                        try:
                            t_ms_b, val_b = line.split(b",", 1)
                            yield int(t_ms_b), float(val_b)
                        except Exception:
                            # skip malformed lines
                            pass
            except KeyboardInterrupt:
                # clean disconnect then bubble up to exit
                try:
                    if s: s.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                if s: s.close()
                print("\n[bye]")
                raise
            except Exception as e:
                print(f"[reconnect] {e}; retrying in {self.retry_sec}s…")
                try:
                    if s: s.shutdown(socket.SHUT_RDWR)
                except:
                    pass
                if s: s.close()
                time.sleep(self.retry_sec)
    
    def stream(self):
        try:
            for t_ms, val in self.generate_sample(): #t_ms i time in ms and val is voltage in uv
                # Put whatever you code is here
                self.user_context[RAW_DATA].append(val)
        except:
            pass
                     
    def stream_thread(self):
        print("stream thread")
        if self._stream_thread == None:
            print("stream thread")
            self._stream_thread = threading.Thread(target=self.stream)
            self._stream_thread.start()