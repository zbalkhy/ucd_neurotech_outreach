import socket
import time
from common import RAW_DATA, EVENTS
import numpy as np
import threading
from eventClass import EventClass
from eventType import EventType

class DeviceStreamer(EventClass):
    def __init__(self, host: str, port: int, retry_sec: int, user_context: dict):
            self.host: str = host
            self.port: int = port
            self.retry_sec: int = retry_sec
            self.user_context: dict = user_context
            self._stream_thread: threading.Thread = None
            self.shutdown: bool = False
            
            # subscribe to events
            user_context[EVENTS].add_observer(self)
            
            super().__init__()

    
    def on_notify(self, eventData: any, event: EventType) -> None:
        if event == EventType.PROGRAMEXIT:
            self.shutdown = True

    def _try_close_socket(self, s):
        try:
            if s: s.shutdown(socket.SHUT_RDWR)
        except:
            pass
        if s: s.close()
        
    # Generator that yields (t_ms:int, value:float) from 't_ms,value' lines.
    # Auto-reconnects on errors/disconnects. 
    def generate_sample(self):
        buf = b""
        while not self.shutdown:
            s = None
            try:
                s = socket.create_connection((self.host, self.port), timeout=5)
                s.settimeout(None)  # blocking
                print(f"[connected] {self.host}:{self.port}")
                buf = b""
                while True:
                    if self.shutdown:
                       self._try_close_socket(s)
                       break
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
                self._try_close_socket(s)
                print("\n[bye]")
                raise
            except Exception as e:
                print(f"[reconnect] {e}; retrying in {self.retry_sec}s…")
                self._try_close_socket(s)
                time.sleep(self.retry_sec)
    
    
    def stream(self):
        try:
            for t_ms, val in self.generate_sample(): #t_ms i time in ms and val is voltage in uv
                self.user_context[RAW_DATA].append(val)
        except:
            pass
                     
    def stream_thread(self):
        if self._stream_thread == None:
            self._stream_thread = threading.Thread(target=self.stream)
            self._stream_thread.start()