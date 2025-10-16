from pyftdi.i2c import I2cController
from pyftdi.ftdi import Ftdi

devices = Ftdi.list_devices()
for dev in devices:
    print(dev)


# --- 1. Create the controller
i2c = I2cController()

# --- 2. Open the FT4232H channel (example: channel D)
# The syntax is ftdi://vendor:product/serial/port
# or shorter, e.g., ftdi://ftdi:4232h/1 for channel A
i2c.configure('ftdi://ftdi:4232h/2')  # Channel D

# --- 3. Get an I2C port for a given slave address
slave = i2c.get_port(0x68)  # Example: RTC, accelerometer, etc.

# --- 4. Write bytes
try:
    slave.write([0x00, 0x12, 0x34])
except Exception as e:
    print("Write error:", e)

# --- 5. Read bytes
try:
    data = slave.read(2)
    print("Read:", data)
except Exception as e:
    print("Read error:", e)

# --- 6. Clean up
i2c.terminate()
