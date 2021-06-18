# Rocketify Python SDK

## Introduction

The Rocketify SDK allows you to connect your Python application
with [Rocketify](https://rocketify.rocketcop.io).

## Usage

```python

from rocketify_sdk import Sdk


def on_config_updated(new_config):
    print('config updated', new_config)


if __name__ == "__main__":
    sdk = Sdk(api_key="<ROCKETIFY_APP_API_KEY>", polling_interval_seconds=5, debug=True)
    sdk.on_config_updated += on_config_updated
    
    # Make sure to call init before doing any action
    sdk.init()

    sdk.log("App successfully started")
    
    config = sdk.get_config()
    
    # Don't forget to call stop to prevent rocketify-sdk from running in the background
    sdk.stop()

```