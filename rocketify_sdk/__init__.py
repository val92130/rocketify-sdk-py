import copy
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
                 base_url: str = "https://api.rocketify.rocketcop.io"
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

    def _debug(self, *args):
        if self.debug:
            logging.warning(args)

    def _loop_update_settings(self):
        try:
            res = requests.get("%s/monitors/sdk/settings" % self.base_url, headers={"Authorization": self.api_key})
            res.raise_for_status()
            self._config = res.json()
            self.on_config_updated.fire(self._config)
        except requests.RequestException as e:
            if e.response.status_code == 403:
                raise e

            self._debug("Error while updating settings", e)
        except Exception as e:
            self._debug("Error while updating settings", e)

    def _loop_update_actions(self):
        try:
            res = requests.get("%s/monitors/sdk/actions" % self.base_url, headers={"Authorization": self.api_key})
            res.raise_for_status()
            actions = res.json()
            for action in actions:
                self._debug("Action received", action)
                self.on_action.fire(action.action, action.time)
        except requests.RequestException as e:
            if e.response.status_code == 403:
                raise e

            self._debug("Error while fetching actions", e)
        except Exception as e:
            self._debug("Error while fetching actions", e)

    def _log(self, message: str, log_type: str):
        try:
            payload = {
                "message": message,
                "type": log_type,
            }

            res = requests.post(
                "%s/monitors/log" % self.base_url, headers={"Authorization": self.api_key}, json=payload)
            res.raise_for_status()
        except Exception as e:
            self._debug("Error while sending log", str(e))
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

        self._debug("Sending log", message, log_type)
        thread = threading.Thread(target=self._log, name="RemoteLog", args=[message, log_type])
        thread.start()

    def init(self):
        self._raise_on_stopped()
        self._loop_update_settings()
        self._loop_update_actions()
        self._interval_runners.append(IntervalRunner(self._loop_update_settings, self.polling_interval_seconds))
        self._interval_runners.append(IntervalRunner(self._loop_update_actions, 2))

    def stop(self):
        self._debug("stopping")
        for thread in self._interval_runners:
            thread.cancel()

    def get_config(self):
        return copy.deepcopy(self._config)
