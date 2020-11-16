import time
from datetime import datetime

import typer

from demux import Demux
from i2c_mux import TofMux

from gpiozero import Device
from gpiozero.pins.mock import MockFactory
from gpiozero.pins.native import NativeFactory

import board

from sa import MyRow, SESSION_MyRow


def loop_demux(demuxer_a):
    global SESSION_MyRow
    for cur_id in demuxer_a.connect_inds:
        start = datetime.utcnow()
        demuxer_a.run_select(cur_id)
        stop = datetime.utcnow()
        cur_entry = MyRow(index=cur_id, start=start, stop=stop)
        cur_entry.add(SESSION_MyRow)
        # rest between each
        time.sleep(0.5)


def loop_dist(dists):
    out = []
    for i in dists.connect_inds:
        out.append((i, dists.obtain_reading(i, precision=4, unit="in")))
    return out


def main(dev: bool = False):

    # TODO: use only single pin lib

    # demux
    INDEX_PINS = [25, 23, 24, 17]
    PWR_PIN = 27
    UNCONNECTED = [11, 12, 13, 14, 15]  # TODO: allow for manual off of pins
    CONNECTED = []
    DELAY_SEC = 3
    ON_DURATION = 0.3

    # tof
    SCL_pin = board.SCL
    SDA_pin = board.SDA
    I2C_CHANNELS = [0, 1]

    # other
    LOOPS = 10

    if dev:
        Device.pin_factory = MockFactory()
    else:
        Device.pin_factory = NativeFactory()

    demuxer_a = Demux(
        INDEX_PINS,
        PWR_PIN,
        connected=CONNECTED,
        unconnected=UNCONNECTED,
        on_duration=ON_DURATION,
    )

    dists = TofMux(
        channels=I2C_CHANNELS,
        SCL_pin=SCL_pin,
        SDA_pin=SDA_pin,
    )

    # init
    time.sleep(2)

    # main loop
    try:
        for i in range(LOOPS):
            # demuxer_a
            loop_demux(demuxer_a)
            print("done demuxer_a")

            # dist
            ret_val = loop_dist(dists)
            print(f"dists: {ret_val}")

            time.sleep(DELAY_SEC)

    except KeyboardInterrupt:
        demuxer_a.zero()
        print("demuxer_a zeroed")


if __name__ == "__main__":
    typer.run(main)