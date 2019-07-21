import time
import docker
import atexit
import logging


class DockerManager(object):
    def __init__(self):
        self._client = docker.from_env()
        self._containers = []
        self._logger = logging.getLogger(self.__class__.__name__)
        atexit.register(self.cleanup)

    def create(self, vnc_port=5900, web_port=6080, fast_load=False):
        """
        Creates a VNC container with a GUI and waits for it to start up.
        """
        container = self._client.containers.run(
            "dorowu/ubuntu-desktop-lxde-vnc:latest",
            auto_remove=True,
            ports={"80/tcp": web_port, "5900/tcp": vnc_port},
            detach=True
        )
        self._logger.info("Created docker container: {}".format(container.name))
        self._logger.info("Web port: {}, VNC port: {}".format(web_port, vnc_port))
        self._containers.append(container)

        if fast_load:
            time.sleep(5)
        else:
            for line in container.logs(stream=True):
                if b"GET /api/health" in line:
                    break
        self._logger.info("Docker container started: {}".format(container.name))
        return container

    def cleanup(self):
        for container in self._containers:
            self._logger.info("Removing Docker container: {}".format(container.name))
            container.kill()
