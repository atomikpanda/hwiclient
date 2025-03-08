# README
## Overview

`hwiclient` is a Python library designed to control Lutron Homeworks Illuminations systems. It provides an easy-to-use interface for interacting with lighting, shades, and other devices within the Lutron Homeworks ecosystem.

## Features

- Control lights and shades
- Monitor device status
- Schedule events
- Integrate with other home automation systems

## Installation

You can install `hwiclient` using pip:

```bash
pip install hwiclient
```

## Usage

Here's a basic example of how to use `hwiclient`:

```python
import asyncio
from hwiclient.homeworks import HomeworksHub

from hwiclient.connection.login import (
    LutronCredentials,
    LutronServerAddress,
)
from hwiclient.connection.state import ConnectionState as CS

async def turn_on_a_light_example(hub: HomeworksHub):
    light = hub.devices.find_dimmer_device_named("Dining Chandelier")
    command = light.action.turn_on()
    await hub.enqueue_command(command)
    
# Connection Loop
async def _connect(hub: HomeworksHub):
    connection = await hub.connect(LutronServerAddress("1.1.1.1", 23))

    try:
        logged_in = False
        while not logged_in:
            (old_state, new_state) = await connection.on_next_state_change
            _LOGGER.debug(f"THE STATE CHANGED {old_state} {new_state}")
            if new_state == CS.CONNECTED_READY_FOR_LOGIN_ATTEMPT:
                await connection.attempt_login(LutronCredentials("user", "pass"))
            if new_state == CS.CONNECTED_LOGGED_IN:
                logged_in = True
                await turn_on_a_light_example(hub)
            if new_state == CS.CONNECTED_LOGIN_INCORRECT:
                continue
        await connection.on_connection_lost
    except Exception as exc:
        _LOGGER.error(exc)
        raise exc
    finally:
        connection.close()
        await _connect(hub)

# Read devices from config and start connection process
 with open(homeworks_config_file, "r") as file:
        parsed = yaml.safe_load(file)
        hub = HomeworksHub(homeworks_config=parsed)
        asyncio.create_task(_connect(hub))
```

## License

This project is licensed under the Apache 2.0 License. See the [LICENSE](LICENSE) file for details.

## Contact

For any questions or issues, please open an issue on the [GitHub repository](https://github.com/atomikpanda/hwiclient).