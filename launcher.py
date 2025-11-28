import os, ctypes
from app import app
import uvicorn


def enable_vt100():
    if os.name == "nt":
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        mode = ctypes.c_uint()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        kernel32.SetConsoleMode(handle, mode.value | 0x0004)


enable_vt100()
os.environ["NO_COLOR"] = "1"
os.environ["UVICORN_NO_COLOR"] = "1"


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
