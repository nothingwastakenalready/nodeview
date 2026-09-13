from fastapi.testclient import TestClient

from raffael.api import create_app


def test_proxmox_vm_service_and_minipc_topology(tmp_path):
    config = tmp_path / "services.yaml"
    config.write_text("services: []\n")

    with TestClient(create_app(config_path=config, database_url=f"sqlite:///{tmp_path / 'topology.db'}")) as client:
        assert client.post(
            "/auth/register",
            json={"email": "topology@example.com", "password": "a sufficiently long password"},
        ).status_code == 201
        csrf = client.cookies.get("raffael_csrf")
        headers = {"X-CSRF-Token": csrf}

        proxmox = client.post(
            "/household/devices",
            headers=headers,
            json={
                "connector": "proxmox",
                "name": "Proxmox",
                "endpoint": "https://192.168.1.20:8006",
                "credential_ref": "keychain://raffael/proxmox",
                "metadata": {"role": "infrastructure"},
            },
        )
        assert proxmox.status_code == 201

        vm = client.post(
            "/household/devices",
            headers=headers,
            json={
                "connector": "icmp",
                "name": "Raffael-VM 105",
                "endpoint": "192.168.1.147",
                "parent_id": proxmox.json()["id"],
                "metadata": {"role": "infrastructure", "proxmox_vmid": 105},
            },
        )
        assert vm.status_code == 201

        web = client.post(
            "/household/devices",
            headers=headers,
            json={
                "connector": "generic",
                "name": "Raffael-Web",
                "endpoint": "http://192.168.1.147:8080/health",
                "parent_id": vm.json()["id"],
                "metadata": {"role": "service", "check": "http"},
            },
        )
        assert web.status_code == 201

        minipc = client.post(
            "/household/devices",
            headers=headers,
            json={
                "connector": "ssh",
                "name": "Mini-PC",
                "endpoint": "192.168.1.50",
                "credential_ref": "keychain://raffael/minipc",
                "metadata": {"role": "infrastructure"},
            },
        )
        assert minipc.status_code == 201

        docker = client.post(
            "/household/devices",
            headers=headers,
            json={
                "connector": "docker",
                "name": "Mini-PC Docker",
                "parent_id": minipc.json()["id"],
                "metadata": {"role": "service"},
            },
        )
        assert docker.status_code == 201

        devices = client.get("/household/devices").json()
        assert "credential_ref" not in devices[0]
        by_name = {item["name"]: item for item in devices}
        assert by_name["Raffael-VM 105"]["parent_id"] == by_name["Proxmox"]["id"]
        assert by_name["Raffael-Web"]["parent_id"] == by_name["Raffael-VM 105"]["id"]
        assert by_name["Mini-PC Docker"]["parent_id"] == by_name["Mini-PC"]["id"]
