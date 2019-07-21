#!/usr/bin/env python3

import os
import sys
import time
import json
import logging

from docker_manager import DockerManager
from vnc_manager import VNCManager


def main(path):
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ScriptLoader")

    docker_mgr = DockerManager()
    docker_mgr.create(fast_load=True)

    with open(path, "r") as f:
        commands = json.load(f)
    logger.info("Loaded script: {}".format(commands["name"]))
    image_path = os.path.abspath(os.path.join(os.path.dirname(path), commands["image_path"]))
    logger.info("Image path: {}".format(image_path))
    start = time.time()
    client = VNCManager(5900, image_path)
    run_commands(client, commands["code"])
    end = time.time()
    logger.info("Script execution: {} sec".format(round(end - start, 3)))


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
    if len(sys.argv) < 2:
        print("Usage: {} <script>".format(sys.argv[0]))
    else:
        main(sys.argv[1])
