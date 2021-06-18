import copy
import pickle
import threading
import requests
import logging

from typing import List

from rocketify_sdk import EventHook
from rocketify_sdk.IntervalRunner import IntervalRunner


class Sdk:
    def __init__(self,
                 api_key: str,
                 polling_interval_seconds: int = 5,
                 debug: bool = False,
                 base_url: str = "https://api.rocketify.app"
                 ):
        if not api_key:
            raise Exception("Please provide an api key")

        self.api_key = api_key
        self.polling_interval_seconds = polling_interval_seconds
        self.debug = debug
        self.base_url = base_url
        self._config = None
        self.on_config_updated = EventHook.EventHook()
        self.on_action = EventHook.EventHook()
        self._interval_runners: List[IntervalRunner] = []
        self._stopped = False
        
    def _raise_on_stopped(self):
        if self._stopped:
            raise Exception("This sdk has been stopped")

    def _debug(self, msg):
        if self.debug:
            logging.warning(msg)

    def _update_settings(self):
        try:
            res = requests.get("%s/apps/sdk/settings" % self.base_url, headers={"Authorization": self.api_key})
            res.raise_for_status()

            prev_config = self._config
            new_config = res.json()
            if pickle.dumps(prev_config) != pickle.dumps(new_config):
                self.on_config_updated.fire(new_config)

            self._config = new_config
        except requests.RequestException as e:
            if e.response.status_code == 403:
                raise e

            self._debug("Error while updating settings: %s" % str(e))
        except Exception as e:
            self._debug("Error while updating settings: %s" % str(e))

    def _log(self, message: str, log_type: str):
        try:
            payload = {
                "message": message,
                "type": log_type,
            }

            res = requests.post(
                "%s/apps/log" % self.base_url, headers={"Authorization": self.api_key}, json=payload)
            res.raise_for_status()
        except Exception as e:
            self._debug("Error while sending log: %s" % str(e))
            logging.warning("Could not log message", str(e))

    def log(self, message: str, log_type: str = "info"):
        self._raise_on_stopped()

        if not message:
            raise Exception("Cannot send an empty message")
        if log_type not in ["error", "info", "warn", "success"]:
            raise Exception("Invalid log type %s" % log_type)

        if log_type == "error":
            logging.error(message)
        elif log_type == "warn":
            logging.warning(message)
        else:
            logging.info(message)

        self._debug("Sending log: %s %s" % (message, log_type))
        thread = threading.Thread(target=self._log, name="RemoteLog", args=[message, log_type])
        thread.start()

    def init(self):
        self._raise_on_stopped()
        self._update_settings()
        self._interval_runners.append(IntervalRunner(self._update_settings, self.polling_interval_seconds))

    def stop(self):
        self._debug("stopping")
        self.on_config_updated.clear_handlers()
        self.on_action.clear_handlers()

        for thread in self._interval_runners:
            thread.cancel()

    def get_config(self):
        return copy.deepcopy(self._config)
