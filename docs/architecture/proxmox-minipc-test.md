# Proxmox- und Mini-PC-Testaufbau

Dieses Dokument beschreibt den kleinsten reproduzierbaren Testaufbau für eine
hierarchische Überwachung. Er funktioniert unabhängig von UniFi und verwendet
nur die vorhandenen Geräte- und Connector-Endpunkte.

## Zielbild

```text
Proxmox (proxmox / REST API)
└── Raffael-VM 105 (icmp oder ssh)
    └── Raffael-Web (generic / HTTP :8080)

Mini-PC (icmp oder ssh)
└── Docker (docker API)
    └── Home Assistant (generic / HTTP)
```

Proxmox wird nur einmal verbunden. Der Connector kann anschließend Nodes,
VMs und Container als Kinder anlegen. Einzelne Betriebssystemprozesse werden
nicht automatisch als eigene Geräte angelegt; überwacht werden stattdessen
relevante Dienste. Eine Prozessprüfung per SSH oder Agent bleibt eine optionale
Vertiefung.

## Einrichtung über die Website/API

1. Unter **Geräte → Gerät hinzufügen** ein Infrastrukturgerät `Proxmox`
   anlegen, zum Beispiel mit `https://192.168.1.20:8006`.
2. Die Zugangsdaten als geheime Credential-Referenz hinterlegen. Passwörter
   und Tokens gehören nicht in die Geräte-Metadaten.
3. Die erkannte VM oder den Container unter dem Proxmox-Gerät anlegen. Als
   einfachen ersten Check `icmp` verwenden; für Dienstmetriken `ssh`.
4. Den Raffael-Webdienst als Kind der VM mit `generic` und
   `http://192.168.1.147:8080/health` eintragen.
5. Den Mini-PC als eigenes Gerät mit `icmp` oder `ssh` anlegen.
6. Darunter den Docker-Connector und die gewünschten HTTP/TCP-Dienste als
   Kinder anlegen.

Die gleichen Schritte lassen sich zum Testen mit der API ausführen:

```bash
# nach Registrierung: CSRF-Token aus dem Browser-Cookie verwenden
curl -X POST http://127.0.0.1:8080/household/devices \
  -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" \
  -d '{"connector":"proxmox","name":"Proxmox","endpoint":"https://192.168.1.20:8006","credential_ref":"keychain://raffael/proxmox"}'

# die zurückgegebene id als parent_id verwenden
curl -X POST http://127.0.0.1:8080/household/devices \
  -H 'Content-Type: application/json' -H "X-CSRF-Token: $CSRF" \
  -d '{"connector":"generic","name":"Raffael-Web","endpoint":"http://192.168.1.147:8080/health","parent_id":1,"metadata":{"role":"service"}}'
```

## Erwartetes Verhalten

- Ein nicht erreichbarer Proxmox-Host markiert seine Kinder als nicht
  erreichbar, ohne für jeden Dienst einen separaten Netzwerkfehler zu melden.
- Ist nur ein Dienst defekt, bleibt der Host grün und ausschließlich der Dienst
  wird kritisch.
- Ein Mini-PC kann ohne UniFi überwacht werden: ICMP reicht für Erreichbarkeit;
  SSH/SNMP oder ein späterer Agent liefern Ressourcen und Dienstmetriken.
- Clients werden mit `POST /household/clients` angelegt und erhalten über
  `parent_id` denselben Abhängigkeitsbaum.

## Automatisierter Test

`tests/test_topology.py` erstellt diesen Aufbau in einer frischen SQLite-
Datenbank und prüft die Eltern-Kind-Beziehungen. Er benötigt keine echte
Proxmox-, Docker- oder Mini-PC-Verbindung und ist daher für CI geeignet:

```bash
pytest tests/test_topology.py
```

Der Test ist ein Vertrag für die spätere Connector-Laufzeit: Discovery darf
weitere Kinder hinzufügen, aber die einfache manuelle Einrichtung muss stabil
bleiben.
