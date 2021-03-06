import celery
import importlib
import sensorrunner

importlib.reload(sensorrunner)
from sensorrunner.celery_app import setup_app
from sensorrunner.sa import SWITCHLOW, SESSION_SWITCHLOW
import datetime as dt
import time
from sensorrunner.user_config import USER_CONFIG
from sensorrunner.run.run import build_devices_from_config
from sensorrunner.secrets import REDIS_GLOBAL_host, REDIS_GLOBAL_port

GPIODEMUX = None
app = setup_app()

# import redis

# REDIS_CLIENT = redis.Redis(host=REDIS_GLOBAL_host, port=REDIS_GLOBAL_port, db=8)


# def only_one(function=None, key="", timeout=None):
#     """Enforce only one celery task at a time."""
#     # adapted from
#     # http://loose-bits.com/2010/10/distributed-task-locking-in-celery.html
#     def _caller(*args, **kwargs):
#         """Caller."""
#         ret_value = None

#     return _caller


@app.task(bind=True, queue="q_demux_log")
def _log_demux(self, row):
    if row:
        if isinstance(row, SWITCHLOW):
            # have_lock = False
            # lock = REDIS_CLIENT.lock("_log_demux", timeout=2)
            # try:
            #     have_lock = lock.acquire(blocking=False)
            #     if have_lock:
            row.add(SESSION_SWITCHLOW)
            # finally:
            #     if have_lock:
            #         lock.release()
        else:
            raise ValueError(f"unable to match entry {row} to accepted row types")
    else:
        pass


@app.task(bind=True, queue="q_demux_run")
def _demux_run_select(self, dev_dict, wait_secs=0.5):

    # have_lock = False
    # lock = REDIS_CLIENT.lock("_demux_run_select", timeout=8)
    # wait_secs is used to control time between tasks
    global GPIODEMUX
    # https://docs.celeryproject.org/en/latest/userguide/tasks.html#instantiation
    if dev_dict is None:
        raise ValueError("no dev_dict is present")

    try:
        cur_name = dev_dict["name"]
    except KeyError:
        raise ValueError(f"no name is specified in {dev_dict}")

    try:
        dev_type = dev_dict["device_type"]
    except KeyError:
        raise ValueError(
            f"no `device_type` specified for {cur_name}\n> dev_dict: {dev_dict}"
        )

    try:
        cur_run_params = dev_dict["params"]["run"]
    except KeyError:
        raise ValueError(
            f"no run params specified for {cur_name}\n> dev_dict: {dev_dict}"
        )

    try:
        unit = cur_run_params["unit"]
    except KeyError:
        raise ValueError(f"no unit is specified for {cur_name}\n> dev_dict: {dev_dict}")

    # NOTE: I'm not sure how best to handle this.. passing through the queue is
    # not currently an options since it is not serialized by standard methods
    if GPIODEMUX is None:
        gpio_demux_wrapped = build_devices_from_config(
            {"GPIODemux": USER_CONFIG["GPIODemux"]}
        )
        GPIODEMUX = gpio_demux_wrapped["GPIODemux"]
    else:
        pass

    wait = dt.timedelta(seconds=wait_secs).seconds

    # run device
    # TODO: will need to alter this in the future depending on the device type
    # entry = None
    # try:
    #     have_lock = lock.acquire(blocking=False)
    #     if have_lock:
    #         try:
    #             if dev_type == "switch_low":
    #                 start, stop = GPIODEMUX.return_value(cur_name, cur_run_params)
    #                 entry = SWITCHLOW(name=cur_name, start=start, stop=stop, unit=unit)
    #         except Exception as e:
    #             raise Exception(f"unable: {e}")
    # finally:
    #     if have_lock:
    #         lock.release()
    entry = None
    try:
        if dev_type == "switch_low":
            start, stop = GPIODEMUX.return_value(cur_name, cur_run_params)
            entry = SWITCHLOW(name=cur_name, start=start, stop=stop, unit=unit)
    except Exception as e:
        raise Exception(f"unable: {e}")

    # allow wait between devices, even on fail
    time.sleep(max(0, wait))

    return entry


@app.task(bind=True, queue="collect")
def GPIODemux_run(self, dev_dict):
    return celery.chain(_demux_run_select.s(dev_dict), _log_demux.s()).apply_async()
