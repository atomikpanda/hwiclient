# hwiclient

An async Python client library for controlling Lutron Homeworks Illumination systems, built by reverse-engineering the proprietary HWI protocol. Designed for integration with [Home Assistant](https://www.home-assistant.io/) and other home automation platforms.

## Why This Exists

Lutron Homeworks Illumination is a commercial-grade lighting and shade control system found in high-end residential and commercial installations. The processor exposes a TCP-based control interface (HWI) on port 23 — but the protocol is proprietary, undocumented, and no open-source client existed.

I reverse-engineered the HWI protocol by analyzing the traffic between Lutron's own software and the Homeworks processor, then built this library from scratch to provide programmatic control over the system. The goal: bring Lutron Homeworks into the modern smart home ecosystem by enabling Home Assistant integration without relying on Lutron's closed tooling.

## Protocol Overview

The HWI protocol is an ASCII text protocol over a raw TCP socket. Messages are `\r\n`-delimited and use comma-separated values.

### Connection Lifecycle

```
TCP Connect (port 23)
    → Server sends "LOGIN: " prompt
    → Client sends "username,password\r\n"
    → Server responds "login successful" or "login incorrect"
    → Server sends "LNET> " prompt when ready for commands
    → Client sends commands, server pushes monitoring events
```

### Command Format

Commands follow a simple CSV structure: `COMMAND,arg1,arg2,...\r\n`

| Command | Description | Example |
|---------|-------------|---------|
| `FADEDIM` | Fade dimmer to intensity over time | `FADEDIM,50,00:00:03,00:00:00,[1:4:3:2:1]` |
| `RDL` | Request current dimmer level | `RDL,[1:4:3:2:1]` |
| `STOPDIM` | Stop an in-progress fade | `STOPDIM,[1:4:3:2:1]` |
| `KBP` | Simulate keypad button press | `KBP,[1:2:3],5` |
| `KBR` | Simulate keypad button release | `KBR,[1:2:3],5` |
| `KBH` | Simulate keypad button hold | `KBH,[1:2:3],5` |
| `KBDT` | Simulate keypad double-tap | `KBDT,[1:2:3],5` |
| `RKLS` | Request keypad LED states | `RKLS,[1:2:3]` |

### Monitoring (Server-Pushed Events)

After login, the client subscribes to real-time monitoring channels:

| Subscription | Events Received | Purpose |
|-------------|-----------------|---------|
| `DLMON` | `DL,[addr],[level]` | Dimmer level changes |
| `KBMON` | `KBP`, `KBR`, `KBH`, `KBDT` events | Keypad button activity |
| `KLMON` | `KLS,[addr],[led_states]` | Keypad LED state changes |
| `GSMON` | Green strip status | Indicator status |
| `TEMON` | Timeclock events | Scheduled event triggers |

This event-driven architecture means the client does not need to poll — the processor pushes state changes as they happen, whether triggered by physical keypads, scheduled events, or programmatic commands.

### Device Addressing

Devices use a hierarchical colon-separated address scheme, enclosed in brackets for commands:

- **Zone (dimmer/switch/fan)**: `[IntegrationID:Area:Room:Zone:SubDevice]` — e.g. `[1:4:3:2:1]`
- **Shade**: `[IntegrationID:Area:Room:Device]` — e.g. `[1:4:3:1]`
- **Keypad**: `[IntegrationID:Area:Keypad]` — e.g. `[1:2:3]`

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     HomeworksHub                         │
│                  (Main Integration Point)                │
├──────────────────────┬───────────────────────────────────┤
│   DeviceRepository   │       ConnectionCoordinator       │
│  ┌─────────────────┐ │  ┌─────────────────────────────┐  │
│  │ DimmerDevice     │ │  │  PriorityQueue              │  │
│  │ SwitchDevice     │ │  │  (monitoring cmds = high,   │  │
│  │ FanDevice        │ │  │   user cmds = normal)       │  │
│  │ ShadeDevice      │ │  ├─────────────────────────────┤  │
│  │ Keypad           │ │  │  TcpConnection              │  │
│  └────────┬────────┘ │  │  └─ LutronClientProtocol     │  │
│           │          │  │     └─ PacketBuffer           │  │
│           │          │  ├─────────────────────────────┤  │
│           ▼          │  │  DataToResponseAdapter        │  │
│  MonitoringNotifier ◄┼──┤  (protocol state machine)    │  │
│  └─ EventListeners   │  └─────────────────────────────┘  │
└──────────────────────┴───────────────────────────────────┘
```

### Key Design Decisions

**Async-first with `asyncio`**: The library is built on `asyncio.Protocol` for non-blocking TCP I/O. The connection layer uses futures to expose state transitions (`on_next_state_change`, `on_logged_in`, `on_connection_lost`), giving consumers fine-grained control over the connection lifecycle without callbacks.

**Protocol state machine**: `DataToResponseAdapter` classifies raw bytes into prompt types (`LOGIN:`, `LNET>`), login responses, and server event data. This drives the `ConnectionState` enum through a well-defined state machine from `NOT_CONNECTED` through `CONNECTED_READY_FOR_COMMAND`.

**Priority-based command queue**: Monitoring subscription commands (`DLMON`, `KBMON`, etc.) are enqueued at high priority immediately after login. User commands are dispatched only after monitoring is active, ensuring no state changes are missed.

**Event-driven device model**: Server-pushed monitoring data flows through `ServerResponseDataHandler` → `MonitoringTopicNotifier` → device-specific `EventListener` instances. Devices update their internal state reactively. Home Assistant entities subscribe to these events to stay in sync without polling.

**Device type polymorphism**: All controllable outputs extend `DimmerDevice` with type-specific behavior:
- `LightDimmerType` — continuous 0-100% dimming
- `SwitchDimmerType` — binary on/off (maps to 0 or 100)
- `FanDimmerType` — discrete speed steps (0, 25, 50, 75, 100)
- `ShadeDimmerType` — positional 0-100% open/close

Each type implements its own `turn_on()`, `turn_off()`, and level-setting logic, so the command layer emits correct `FADEDIM` parameters regardless of device type.

## Command System

The library translates high-level device actions into wire protocol commands through a layered command pipeline. Rather than having devices write raw strings to a socket, every operation is modeled as an object that validates its own parameters, serializes itself into the HWI wire format, and checks connection readiness before executing.

### Command Hierarchy

```
HubCommand (abstract)
├── HubActionCommand              # Commands that change device state
│   └── SessionActionCommand      # Requires active session (checks ready_for_command)
│       ├── FadeDimmer            # FADEDIM — fade to intensity over time
│       ├── StopDimmer            # STOPDIM — cancel in-progress fade
│       └── SetFanLevel           # FADEDIM with snapped speed steps
├── HubRequestCommand             # Commands that query state
│   └── SessionRequestCommand     # Requires active session
│       └── RequestDimmerLevel    # RDL — request current zone level
└── Sequence                      # Composite — executes list of commands in order
```

Every command implements `_perform_command(sender)` to serialize and send itself, and `_can_perform_command(sender)` to gate execution. `SessionActionCommand` and `SessionRequestCommand` add a guard that checks `sender.ready_for_command` — preventing commands from being sent before login completes or while the processor is busy.

### Execution Flow

```python
# 1. Device action creates a command object (no I/O yet)
light = hub.devices.find_dimmer_device_named("Dining Chandelier")
command = light.action.turn_on()
# → Returns FadeDimmer(intensity=100, fade=0s, delay=0s, addr=[1:4:3:1:1])

# 2. Command is enqueued on the priority queue
await hub.enqueue_command(command)

# 3. Coordinator dequeues when LNET> prompt received, calls:
await command.execute(sender)
#   → _can_perform_command checks sender.ready_for_command
#   → _perform_command serializes: "FADEDIM,100,00:00:00,00:00:00,[1:4:3:1:1]\r\n"
#   → sender.send_raw_command writes bytes to transport

# 4. Processor executes, pushes monitoring event: "DL,[1:4:3:1:1],100\r\n"
# 5. Event propagates through MonitoringTopicNotifier → device.on_event → state update
```

### Validation at Construction

Commands validate parameters eagerly in `__init__`, failing fast before anything reaches the queue:

- `FadeDimmer` enforces intensity ∈ [0, 100], requires 1–10 addresses
- `StopDimmer` enforces the same 1–10 address constraint
- `SetFanLevel` snaps arbitrary percentages to the nearest valid speed step using binary search (`bisect_left`), so a 4-speed fan maps to {0, 25, 50, 75, 100}

### Composite Commands with Sequence

`Sequence` implements the composite pattern — it holds a list of `HubCommand` objects and executes them in order. This enables multi-step operations as a single logical unit:

```python
# Request levels for all devices in a group
group.request_all_levels()
# → Sequence([RequestDimmerLevel(addr1), RequestDimmerLevel(addr2), ...])

# Set all devices in a group to 75%
group.set_level(75)
# → Sequence([FadeDimmer(75, ..., addr1), FadeDimmer(75, ..., addr2), ...])
```

## Design Patterns

### Command Pattern

Every protocol operation — dimming a light, requesting a level, pressing a keypad button — is encapsulated as a `HubCommand` object. Commands are created by device action/request methods, validated at construction, and executed later by the coordinator. This decouples intent from transport: the device layer never touches the socket, and the connection layer never knows what a "light" is.

### Strategy Pattern

`DimmerDeviceType` is the strategy interface. Each physical device type provides its own implementation:

| Strategy | `turn_on()` | `set_level(60)` | `is_dimmable` |
|----------|-------------|------------------|---------------|
| `LightDimmerType` | `FADEDIM,100,...` | `FADEDIM,60,...` | `true` |
| `SwitchDimmerType` | `FADEDIM,100,...` | `FADEDIM,100,...` (clamps >0 to 100) | `false` |
| `FanDimmerType(4)` | `FADEDIM,100,...` | `FADEDIM,50,...` (snaps to nearest step) | `true` |
| `ShadeDimmerType` | `FADEDIM,100,...` | `FADEDIM,60,...` | `true` |

The `DimmerDevice` delegates to its type's `actions()` and `requests()` methods, so the same device interface produces different wire commands depending on the physical hardware it represents. Adding a new device type means implementing one class — no changes to the command pipeline or connection layer.

### Composite Pattern

`Sequence` composes multiple `HubCommand` objects into a single command. `DimmerDeviceGroup` uses this to fan out operations across all devices in a group — `set_level()` returns a `Sequence` of individual `FadeDimmer` commands. The coordinator executes it atomically without knowing it contains multiple operations.

### Observer / Pub-Sub (Two Layers)

The event system operates at two distinct layers:

**Protocol layer** — `MonitoringTopicNotifier` dispatches raw protocol events (`DL`, `KBP`, `KLS`) to `TopicSubscriber` instances. This is where the wire protocol's monitoring data enters the application.

**Device layer** — `DeviceEventSource` provides per-device event streams. When a `DimmerDevice` receives a `DIMMER_LEVEL_CHANGED` event, it updates its internal `_level` state, then re-publishes through its own `event_source`. Consumers (like Home Assistant entities) subscribe to specific devices and event kinds, with optional `FilteredListener` wrappers that match on event data properties (address, button number, etc.).

```
Wire: "DL,[1:4:3:1:1],75"
  → ServerResponseDataHandler parses address + level
    → MonitoringTopicNotifier dispatches to subscribers
      → DimmerDevice.on_event updates self._level = 75
        → DeviceEventSource.post notifies registered listeners
          → Home Assistant entity state update
```

This two-layer design keeps protocol-level concerns (parsing, topic routing) separate from domain-level concerns (device state, UI updates). A `DimmerDeviceGroup` listens to its children's event sources and recalculates aggregate brightness, emitting its own `DEVICE_GROUP_DIMMER_LEVEL_CHANGED` event — observers compose cleanly without the protocol layer knowing groups exist.

## Installation

```bash
pip install hwiclient
```

## Usage

```python
import asyncio
from hwiclient.homeworks import HomeworksHub
from hwiclient.connection.login import LutronCredentials, LutronServerAddress
from hwiclient.connection.state import ConnectionState as CS

async def main():
    # Load device config and create hub
    with open("homeworks.yaml", "r") as f:
        config = yaml.safe_load(f)
    hub = HomeworksHub(homeworks_config=config)

    # Connect and authenticate
    connection = await hub.connect(LutronServerAddress("192.168.1.100", 23))

    logged_in = False
    while not logged_in:
        old_state, new_state = await connection.on_next_state_change
        if new_state == CS.CONNECTED_READY_FOR_LOGIN_ATTEMPT:
            await connection.attempt_login(LutronCredentials("user", "pass"))
        elif new_state == CS.CONNECTED_LOGGED_IN:
            logged_in = True

    # Control a light
    light = hub.devices.find_dimmer_device_named("Dining Chandelier")
    await hub.enqueue_command(light.action.turn_on())

    # Wait until disconnected
    await connection.on_connection_lost
```

### Device Configuration (YAML)

```yaml
devices:
  Living Room:
    dimmers:
      - name: "Recessed Lights"
        number: "1"
        address: "1:4:3:1:1"
    switches:
      - name: "Sconces"
        number: "2"
        address: "1:4:3:2:1"
    shades:
      - name: "Window Shade"
        number: "3"
        address: "1:4:3:3"
    keypads:
      - name: "Entry Keypad"
        address: "1:4:1"
        buttons:
          - name: "All On"
            number: 1
            zones:
              - number: "1"
                address: "1:4:3:1:1"
```

## Testing

```bash
pytest
```

Tests cover packet buffering, protocol state transitions, command serialization and validation, address encoding/decoding, the event pub/sub system, and hub-level integration.

## License

Apache 2.0 — see [LICENSE](LICENSE).

## Contact

For questions or issues, open an issue on the [GitHub repository](https://github.com/atomikpanda/hwiclient).