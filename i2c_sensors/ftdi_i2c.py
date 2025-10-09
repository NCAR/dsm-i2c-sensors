#!/usr/bin/env python3
# probe_ftdi_i2c.py
from time import sleep
from pyftdi.gpio import GpioAsyncController
from pyftdi.ftdi import Ftdi
from pyftdi.i2c import I2cController, I2cNackError

def toggle_gpio(url: str, pin: int, times: int = 10, period_s: float = 0.2):
    """
    Toggle one FTDI GPIO pin on/off 'times' times.
    url: e.g. 'ftdi://::/1'  (first FTDI, channel A)
    pin: 0..7  (bit position, AD0..AD7 on that channel)
    """
    mask = 1 << pin
    gpio = GpioAsyncController()
    print(f"\nOpening GPIO {url} ...")
    print(f"Toggling {url} pin {pin} (mask 0x{mask:02X}) {times} times at {1/period_s:.1f} Hz")
    try:
        # Set only 'pin' as output
        gpio.configure(url, direction=mask)           # 1=output, 0=input
        val = 0
        for _ in range(times):
            val ^= mask                                # flip the bit
            # write only output bits (writing '1' to an input would raise)
            gpio.write(val & gpio.direction)          # safe write per docs
            sleep(period_s/2)
            val ^= mask
            gpio.write(val & gpio.direction)
            sleep(period_s/2)
    finally:
        gpio.close()


def i2c_scan(ctrl = I2cController) -> list[int]:
    """Return 7-bit I2C addresses that ACK on the given FTDI URL."""
    found = []
    # 0x00–0x02 and 0x78–0x7F are reserved; scan 0x03..0x77
    # for addr in range(0x02, 0x78, 2):  # step by 2 to skip odd addresses (10-bit):
    for addr in range(0x02, 0x78):
        try:
            i2c = ctrl.get_port(addr)

            # ch = i2c.read_from(0x00, 1, False, True) | ''  # try to read one byte from register 0x00
            # print( "'{ch}'(0x{int(ch):02X}) ")
            # if  ch != '': 
            # if i2c.poll(relax = True):  # ACK?
            #     found.append(addr)
            #     print(f"*0x{addr:02X}*", end="", flush=True)
            # else:
            #     print(".", end="", flush=True)
            i2c.write(b'')  # try to write zero bytes
            found.append(addr)
            print(f"\n0x{addr:02X}\n", end="", flush=True)

        except I2cNackError:
            print("*", end="", flush=True)
            pass  # just no device here
    return found

def probe_all_channels( ctrl: I2cController):

    # toggle_gpio("ftdi://::P03X9DBD/1", pin=1, times=30, period_s=0.25)  # toggle AD0 a few times
    # toggle_gpio("ftdi://::P03X9DBD/2", pin=2, times=30, period_s=0.25)  # toggle AD0 a few times
    # toggle_gpio("ftdi://::P03X9DBD/3", pin=3, times=30, period_s=0.25)  # toggle AD0 a few times
    # toggle_gpio("ftdi://::P03X9DBD/4", pin=4, times=30, period_s=0.25)  # toggle AD0 a few times

    SER = 'P03UM9NA'           # the device with description 'I2C'

    print(f"\nProbing FTDI device S/N={SER} ... Freq={FREQ}Hz")

    for iface in (0, 1, 2, 3):       # A and B only (C/D are not I2C/MPSSE)
        url = f'ftdi://ftdi:2432hq:{SER}/{iface}'
        try:
            # ctrl.configure(url, frequency=FREQ)
            addrs = i2c_scan(ctrl, freq=FREQ)
            print(f'\n{url}:', [f'0x{a:02X}' for a in addrs])
        except Exception as e:
            print(f'\n{url}: {e.__class__.__name__}: {e}')

    # # We'll iterate each physical FTDI and probe all 4 interfaces (/1..../4)
    # for (vid, pid, bus, addr, serial,idx,descr), _ in devices:
    #     for iface in range(1, 5):  # 1..4 == channels A..D
    #         # URL = 'ftdi://::/1' 
    #         # url = f"ftdi://{vid:04x}:{pid:04x}:{serial}/{iface}"
    #         url = f"ftdi://::{serial}/{iface}"
    #         print(f"Probing {url} ...")
    #         ctrl = I2cController()
    #         try:
    #             ctrl.configure(url, frequency=FREQ)
    #             addrs = []
    #             for addr in range(0x01, 0xFF):  # common addresses to probe first
    #                 try:
    #                     if ctrl.validate_address(addr):
    #                         addrs.append(addr)
    #                         print(f"  Found device at 0x{addr:02X}")
    #                 except Exception:
    #                     pass
    #             # returns list of 7-bit addresses that ACK
    #             addrs_hex = [f"0x{a:02X}" for a in addrs]
    #             print(f"[I2C OK]  {url}  ->  found {len(addrs)} device(s): {addrs_hex}")
    #         except Exception as e:
    #             # Non-I²C channel, busy, or kernel driver attached, etc.
    #             print(f"[NO I2C]  {url}  ->  {e.__class__.__name__}: {e}")
    #         finally:
    #             try:
    #                 ctrl.close()
    #             except Exception:
    #                 pass

if __name__ == "__main__":

    devices = Ftdi.list_devices()
    if not devices:
        print("No FTDI devices found")
        exit(1)


    # devices is a list of tuples: (usb_device, (vid, pid, serial), iface)
    for d in devices:
        # print(f"Found FTDI device: VID=0x{d[1][0]:04x} PID=0x{d[1][1]:04x} S/N={d[1][2]}")
        print(f"Found FTDI device: {d}")


    FREQ = 100_000  # try 100 kHz first; bump to 400_000 if wiring is short/clean


    SER = 'P03UM9NA'           # the device with description 'I2C'
    url = f'ftdi://ftdi::{SER}/1'
    freq: int = FREQ

    print(f"\nProbing FTDI device S/N={SER} ... Freq={freq}Hz")

    ctrl = I2cController()
    ctrl.force_clock_mode(False)  # use standard I2C open-drain mode
    print(f"0x{ctrl.direction:04X}")
    try:
        while True:

            for i in (2,2):
                url = f'ftdi://ftdi::{SER}/{i}'

                ctrl.configure(url, frequency=freq,direction=0x03)  # all pins input (safe)
                print(f"\n\nProbing {url} ...")
                addrs = i2c_scan(ctrl)
                print(f'\n{url}:', [f'0x{a:02X}' for a in addrs])

    except KeyboardInterrupt:
        print("Interrupted by user")
    finally: 
        try:
            ctrl.close()
            print("Controller closed")
        except Exception:
            pass