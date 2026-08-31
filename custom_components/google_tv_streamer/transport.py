"""ADB transport for Google TV Streamer devices."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

try:
    from .adb import GoogleTVStreamerADB
except ImportError:
    from adb import GoogleTVStreamerADB


class AdbTransport:
    """TCP ADB transport with injectable device construction."""

    def __init__(
        self,
        host: str,
        port: int = 5555,
        keypath: str | None = None,
        device_factory: Callable[[str, int], Any] | None = None,
        signer: Any | None = None,
    ) -> None:
        """Create a transport for host:port.

        device_factory is kept injectable so tests can run without adb-shell or
        a live streamer.
        """

        self.host = host
        self.port = port
        self.keypath = keypath
        self.signer = signer
        self._device_factory = device_factory or self._default_device_factory
        self._device: Any | None = None

    def connect(self) -> bool | None:
        """Connect to the ADB device and keep it for shell calls."""

        device = self._device_factory(self.host, self.port)
        if self.signer is not None:
            result = device.connect(rsa_keys=[self.signer])
        else:
            result = device.connect()
        self._device = device
        return result

    def shell(self, cmd: str) -> str:
        """Run a shell command on the connected device."""

        if self._device is None:
            raise RuntimeError("ADB transport is not connected")
        return self._device.shell(cmd)

    def close(self) -> None:
        """Close the underlying device connection if one is open."""

        if self._device is not None:
            self._device.close()
            self._device = None

    def _default_device_factory(self, host: str, port: int) -> Any:
        """Build the real adb-shell TCP device and RSA signer lazily."""

        from adb_shell.adb_device import AdbDeviceTcp
        from adb_shell.auth.keygen import keygen
        from adb_shell.auth.sign_pythonrsa import PythonRSASigner

        keypath = Path(self.keypath).expanduser() if self.keypath else Path.home() / ".android" / "adbkey"
        if not keypath.exists():
            keypath.parent.mkdir(parents=True, exist_ok=True)
            keygen(str(keypath))

        self.signer = PythonRSASigner.FromRSAKeyPath(str(keypath))
        return AdbDeviceTcp(host, port)


def connect_streamer(
    host: str,
    port: int = 5555,
    keypath: str | None = None,
    device_factory: Callable[[str, int], Any] | None = None,
) -> GoogleTVStreamerADB:
    """Connect to a streamer and return the shell-command client."""

    transport = AdbTransport(host, port, keypath=keypath, device_factory=device_factory)
    transport.connect()
    client = GoogleTVStreamerADB(shell_runner=transport.shell)
    client._transport = transport
    return client


def make_shell_runner(
    host: str,
    port: int = 5555,
    keypath: str | None = None,
    device_factory: Callable[[str, int], Any] | None = None,
) -> Callable[[str], str]:
    """Return a connected shell runner callable for lower-level integrations."""

    transport = AdbTransport(host, port, keypath=keypath, device_factory=device_factory)
    transport.connect()

    def shell_runner(cmd: str) -> str:
        return transport.shell(cmd)

    shell_runner._transport = transport
    return shell_runner
