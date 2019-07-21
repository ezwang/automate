#!/usr/bin/env python3

import sys
import time
import json
import logging

from docker_manager import DockerManager
from vnc_manager import VNCManager


def main(path):
    logging.basicConfig(level=logging.INFO)

    docker_mgr = DockerManager()
    docker_mgr.create()

    client = VNCManager(5900)
    with open(path, "r") as f:
        commands = json.load(f)
    run_commands(client, commands)


def run_commands(client, commands):
    logger = logging.getLogger("CommandLoop")

    ret = False
    for command in commands:
        action = command["action"]
        logger.debug("Executing action: {} {}".format(action, command.get("arguments", {})))
        if action == "while":
            while run_commands(client, command["condition"]):
                ret = run_commands(client, command["callback"])
        else:
            ret = getattr(client, action)(**command["arguments"])
        if ret:
            sc = command.get("success_callback", [])
            ret = run_commands(client, sc)
        else:
            fc = command.get("failure_callback", [])
            ret = run_commands(client, fc)
        logger.debug("Finished executing action: {}".format(action))
    return ret


if __name__ == "__main__":
    main(sys.argv[1])
