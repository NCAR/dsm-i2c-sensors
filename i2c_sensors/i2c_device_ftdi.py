import threading
import logging

# i2c_sensors/i2c_device_ftdi.py
"""
FTDI-backed I2C device implementation.

Implements I2CDevice using an FTDI channel (pyftdi). All virtual/base methods
are re-defined here. This module expects the package to provide:
    - I2CDevice (base class)
    - I2CDeviceConfig (base config dataclass)

The implementation tries to use pyftdi.i2c.I2cController when available.
If pyftdi is not installed, attempts to use this driver will raise
RuntimeError at runtime when calling open/read/write operations.
"""

# Try to import pyftdi. If not available, we'll raise clearly when used.
try:
    from pyftdi.i2c import I2cController  # type: ignore
    _HAS_PYFTDI = True
except Exception:
    I2cController = None  # type: ignore
    _HAS_PYFTDI = False

# Import base classes from package
from .i2c_device import I2CDevice, I2CConfig

_LOG = logging.getLogger(__name__)

class I2CDeviceFtdiConfig(I2CConfig):
    """Configuration for FTDI-backed I2C devices."""
    def __init__(self, url="ftdi://ftdi:2232h/1", frequency_hz=100000, address=None):
        try:
            super().__init__()
        except Exception:
            pass
        self.url = url
        self.frequency_hz = frequency_hz
        if address is not None:
            self.address = address
        elif not hasattr(self, "address"):
            self.address = None

class I2CDeviceFtdi(I2CDevice):
    """FTDI-based implementation of I2CDevice using pyftdi.I2cController."""
    
    def __init__(self, cfg):
        self._cfg = cfg
        self._controller = None
        self._port = None
        self._lock = threading.Lock()
        self._opened = False

    def get_config(self):
        import copy
        return copy.deepcopy(self._cfg)

    def set_config(self, cfg):
        if self._opened:
            self.close()
        self._cfg = cfg

    def open(self):
        with self._lock:
            if self._opened:
                return
            if not _HAS_PYFTDI:
                raise RuntimeError("pyftdi is required but not installed")
            self._controller = I2cController()
            try:
                self._controller.configure(self._cfg.url, frequency=self._cfg.frequency_hz)
                if not hasattr(self._cfg, "address") or self._cfg.address is None:
                    raise ValueError("I2C slave address not set")
                self._port = self._controller.get_port(self._cfg.address)
                self._opened = True
                _LOG.debug("FTDI I2C opened url=%s addr=0x%02X freq=%d",
                           self._cfg.url, self._cfg.address, self._cfg.frequency_hz)
            except:
                if self._controller:
                    try:
                        self._controller.close()
                    except:
                        pass
                self._controller = self._port = None
                self._opened = False
                raise

    def close(self):
        with self._lock:
            if not self._opened:
                return
            try:
                if self._controller:
                    self._controller.close()
            finally:
                self._controller = self._port = None
                self._opened = False

    def write(self, register, data):
        with self._lock:
            if not self._opened or not self._port:
                raise RuntimeError("Device not opened")
            try:
                self._port.write(bytes([register]) + bytes(data))
            except Exception as exc:
                _LOG.debug("FTDI I2C write error: %s", exc)
                raise

    def read(self, register, length, timeout=None):
        with self._lock:
            if not self._opened or not self._port:
                raise RuntimeError("Device not opened")
            try:
                if hasattr(self._port, "exchange"):
                    return bytes(self._port.exchange(bytes([register]), length))
                self._port.write(bytes([register]))
                return bytes(self._port.read(length))
            except Exception as exc:
                _LOG.debug("FTDI I2C read error: %s", exc)
                raise

    def write_then_read(self, write_bytes, read_length):
        with self._lock:
            if not self._opened or not self._port:
                raise RuntimeError("Device not opened")
            try:
                if hasattr(self._port, "exchange"):
                    return bytes(self._port.exchange(bytes(write_bytes), read_length))
                self._port.write(bytes(write_bytes))
                return bytes(self._port.read(read_length))
            except Exception as exc:
                _LOG.debug("FTDI I2C write_then_read error: %s", exc)
                raise

    def set_bus_speed(self, hz):
        with self._lock:
            if hz == self._cfg.frequency_hz:
                return
            self._cfg.frequency_hz = hz
            was_open = self._opened
        if was_open:
            self.close()
            self.open()

    def detect(self):
        was_closed = not self._opened
        try:
            if was_closed:
                self.open()
            with self._lock:
                if not self._port:
                    return False
                try:
                    self._port.write(b"")
                    return True
                except:
                    try:
                        self._port.read(1)
                        return True
                    except:
                        return False
        except:
            return False
        finally:
            if was_closed:
                try:
                    self.close()
                except:
                    pass

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, *args):
        self.close()