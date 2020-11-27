from pathlib import Path

import celery
from kombu import Queue

import celeryconf
import crummycm as ccm
from aeropi.config.template import TEMPLATE

app = celery.Celery("celery_run")


# obtain parse config
out = ccm.generate(
    "/home/pi/dev/aeropi/scratch/config_run/configs/basic_i2c.yml", TEMPLATE
)


# set Queues
# TODO: tie Queues to task
tmp = list(celeryconf.task_queues)
tmp.extend(
    [
        Queue("q_demux_run"),
        Queue("q_demux_log"),
        Queue("q_dists_run"),
        Queue("q_dists_log"),
    ]
)
celeryconf.task_queues = tuple(tmp)

app.config_from_object(celeryconf)

DEV_TASK_DIR = "./tasks"


def _obtain_relevant_task_dirs(out, device_dir):
    # NOTE: I'm not sure how I want to link the name to tasks. Right now I like
    # the concept of having a separate tasks directory, but that may change such
    # that the tasks are in the devices location and only highlevel/catchall
    # tasks are in the tasks directory
    dirs = []
    device_tasks = [
        x.name for x in list(filter(lambda x: x.is_dir(), Path(device_dir).iterdir()))
    ]
    for dev_name in out.keys():
        if dev_name in device_tasks:
            dirs.append(dev_name)
    return dirs


def _return_task_modules(out, device_dir):
    relevant_dirs = _obtain_relevant_task_dirs(out, device_dir)
    dir_name = DEV_TASK_DIR.split("/")[-1]
    m_names = []
    for d in relevant_dirs:
        m_names.append(f"{dir_name}.{d}")
    return m_names


m_names = _return_task_modules(out, DEV_TASK_DIR)
app.autodiscover_tasks(m_names, force=True)

# aeropi/scratch/config_run/configs/basic_i2c.yml
# possibly helpful later:
# https://gist.github.com/chenjianjx/53d8c2317f6023dc2fa0
