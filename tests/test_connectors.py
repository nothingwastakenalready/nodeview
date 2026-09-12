from raffael.connectors import DiscoveredDevice, discover_network
from raffael.client_sources import normalize_client_row
from raffael.unifi import normalize_unifi_client


class StubConnector:
    name = "stub"

    def discover(self, address: str):
        return DiscoveredDevice(address, None, 1, (), self.name) if address.endswith(".1") else None


def test_discover_network_uses_connector_and_sorts_results():
    found = discover_network("192.0.2.0/30", StubConnector())
    assert [device.address for device in found] == ["192.0.2.1"]
    assert found[0].connector == "stub"


def test_normalize_unifi_client_prefers_name_and_keeps_network_metadata():
    client = normalize_unifi_client({
        "name": "iphone",
        "ip": "192.168.1.44",
        "mac": "AA-BB-CC-DD-EE-11",
        "essid": "home",
        "ap_mac": "aa:bb:cc:00:00:01",
        "is_wired": False,
    })

    assert client is not None
    assert client.name == "iphone"
    assert client.endpoint == "192.168.1.44"
    assert client.mac_address == "aa:bb:cc:dd:ee:11"
    assert client.metadata["role"] == "client"
    assert client.metadata["source"] == "unifi"
    assert client.metadata["unifi_essid"] == "home"


def test_normalize_generic_api_client_row_uses_shared_shape():
    client = normalize_client_row(
        {
            "label": "nas",
            "address": "192.168.1.30",
            "mac_address": "AA:BB:CC:DD:EE:30",
            "vendor": "example",
        },
        source="api",
        connector="generic",
    )

    assert client is not None
    assert client.name == "nas"
    assert client.endpoint == "192.168.1.30"
    assert client.mac_address == "aa:bb:cc:dd:ee:30"
    assert client.connector == "generic"
    assert client.metadata["role"] == "client"
    assert client.metadata["source"] == "api"
    assert client.metadata["api_vendor"] == "example"
