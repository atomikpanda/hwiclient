from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LutronConnectionConfig:
    credentials: LutronCredentials
    server_address: LutronServerAddress


@dataclass
class LutronServerAddress:
    host: str
    port: int


@dataclass
class LutronCredentials:
    username: str
    password: str
