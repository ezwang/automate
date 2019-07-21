#!/usr/bin/env python3

# Execute a sequence of actions given a json file.

import os
import sys
import time
import json
import logging
import argparse

from docker_manager import DockerManager
from vnc_manager import VNCManager


def main():
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="Run GUI automation.")
    parser.add_argument("path", nargs="?", type=str, default=None, help="The path to the script to execute.")

    args = parser.parse_args()

    if args.path is None:
        parser.print_help()
        exit()

    docker_mgr = DockerManager()
    docker_mgr.create(fast_load=True)

    exec_script(args.path)


def exec_script(path, client=None):
    logger = logging.getLogger("ScriptLoader")
    with open(path, "r") as f:
        commands = json.load(f)
    logger.info("Loaded script: {}".format(commands["name"]))
    image_path = os.path.abspath(os.path.join(os.path.dirname(path), commands["image_path"]))
    logger.info("Image path: {}".format(image_path))
    if client is None:
        client = VNCManager(5900)
    client.add_image_path(image_path)
    start = time.time()
    run_commands(client, commands["code"])
    end = time.time()
    logger.info("Script execution: {} sec".format(round(end - start, 3)))


def run_commands(client, commands):
    logger = logging.getLogger("CommandLoop")

    ret = False
    for command in commands:
        action = command["action"]
        logger.debug("Executing action: {} {}".format(action, command.get("arguments", {})))
        package, action = action.split(".", 1)
        if package == "common":
            if action == "while":
                while run_commands(client, command["condition"]):
                    ret = run_commands(client, command["callback"])
            elif action == "wait":
                time = float(command["arguments"]["time"])
                logger.debug("Waiting for {} seconds".format(time))
                time.sleep(time)
            else:
                raise NotImplementedError
        elif package == "vnc":
            ret = getattr(client, action)(**command["arguments"])
        else:
            raise NotImplementedError
        if ret:
            sc = command.get("success_callback", [])
            ret = run_commands(client, sc)
        else:
            fc = command.get("failure_callback", [])
            ret = run_commands(client, fc)
        logger.debug("Finished executing action: {}".format(action))
    return ret


if __name__ == "__main__":
    main()
