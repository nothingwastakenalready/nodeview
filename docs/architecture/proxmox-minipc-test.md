# proxmox and mini-pc test shape

this is the smallest repeatable topology test for hierarchical monitoring.
it does not need unifi and only uses the existing device and connector
endpoints.

## target shape

```text
proxmox (proxmox / rest api)
└── raffael-vm 105 (icmp or ssh)
    └── raffael-web (generic / http :8080)

mini-pc (icmp or ssh)
└── docker (docker api)
    └── home assistant (generic / http)
```

proxmox is connected once. later, the connector can create nodes, vms and
containers below it. operating-system processes are not automatically modeled as
devices; relevant services are monitored instead. process checks through ssh or
an agent stay a deeper follow-up.

## setup through ui/api

1. create an infrastructure device named `proxmox`, for example
   `https://192.168.1.20:8006`.
2. store credentials as a secret reference. passwords and tokens do not belong
   in device metadata.
3. create the discovered vm or container below the proxmox device. use `icmp`
   as the first simple check, or `ssh` later for host metrics.
4. add the raffael web service below the vm with `generic` and
   `http://192.168.1.147:8080/health`.
5. add the mini-pc as its own device with `icmp` or `ssh`.
6. add docker and the relevant http/tcp services below it.

the same shape can be created through the api:

```bash
# after registration: use the csrf token from the browser cookie
curl -X POST http://127.0.0.1:8080/household/devices \
  -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" \
  -d '{"connector":"proxmox","name":"proxmox","endpoint":"https://192.168.1.20:8006","credential_ref":"keychain://raffael/proxmox"}'

# use the returned id as parent_id
curl -X POST http://127.0.0.1:8080/household/devices \
  -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" \
  -d '{"connector":"generic","name":"raffael-web","endpoint":"http://192.168.1.147:8080/health","parent_id":1,"metadata":{"role":"service"}}'
```

## expected behavior

- if the proxmox host is unreachable, its children can be marked affected
  without turning every service into a separate mystery.
- if only one service is broken, the host stays healthy and the service is the
  thing that goes critical.
- the mini-pc can be monitored without unifi. icmp is enough for reachability;
  ssh, snmp or a later agent can add resource and service metrics.
- clients created with `POST /household/clients` can use `parent_id` to join
  the same dependency tree.

## automated test

`tests/test_topology.py` builds this shape in a fresh sqlite database and checks
the parent/child relationships. it does not need a real proxmox, docker or
mini-pc connection:

```bash
pytest tests/test_topology.py
```

the test is a contract for the later connector runtime. discovery may add more
children, but the simple manual setup must stay stable.
