from raffael.connectors import DiscoveredDevice, discover_network


class StubConnector:
    name = "stub"

    def discover(self, address: str):
        return DiscoveredDevice(address, None, 1, (), self.name) if address.endswith(".1") else None


def test_discover_network_uses_connector_and_sorts_results():
    found = discover_network("192.0.2.0/30", StubConnector())
    assert [device.address for device in found] == ["192.0.2.1"]
    assert found[0].connector == "stub"
