# Agones Relay HTTP

Publish Agones GameServers and Fleets details to HTTP endpoints.

**The published payload contains an entire representation of the GameServer or Fleet at the moment the event got fired. Possible types of events are OnAdd, OnUpdate and OnDelete.**

A practical usage for the Agones Relay HTTP is when the operator/user wants to keep a centralized store of all the GameServers and Fleets running across multiples clusters. In this kind of topology, the operator can deploy one Agones Relay on each cluster and point all of them to a central endpoint. Therefore, persisting this information on any kind of datastore.

This project was built on top of the [Agones Event Broadcaster](https://github.com/Octops/agones-event-broadcaster).

### Agones
> An open source, batteries-included, multiplayer dedicated game server scaling and orchestration platform that can run anywhere Kubernetes can run.

You can find great documentation on https://agones.dev/site/

**When a GameServer or Fleet state change event gets fired?**

A few examples are:
- The state of the GameServer changed during its all lifespan. Scheduled, Ready, Allocated, Shutdown, etc. 
- The GameServer status fields like address, port or player tracking fields changed.
- Then the number of replicas of a Fleet went up or down.
- Fleets status fields like: players capacity or count, allocated replicas, ready replicas and reserved replicas changed.
 
In addition to the state change events, the Agones Relay HTTP reacts to `reconcile` events. On an interval bases a complete state of the world gets published. That means all the current GameServers and Fleets states.
The reconcile interval is controlled by the flag `--sync-period`. Make sure you don't set this value to low. The consequence could be a DDoS against the endpoints.

**Important**

OnAdd, OnUpdate and OnDelete are not controled by the reconcile interval. Those events get published at the time they happen.  

## Verbs and Payloads 
| Event        | Verb          | Payload             |
| ------------ |:------------- | ------------------: |
| OnAdd        | POST          | New Obj             |
| OnUpdate     | PUT           | Old and New Obj     |
| OnDelete     | DELETE        | None (Query Params) |

Examples of the POST and PUT payloads can be found on [examples/payloads](https://github.com/Octops/agones-relay-http/tree/main/examples/payloads) folder.

For `OnDelete` events the body of the request is null. The URL of the request looks similar to:
```
DELETE http://localhost:8090/webhook?event_type=gameserver.events.deleted&name=simple-udp-pmx5c-xzfft&namespace=default
DELETE http://localhost:8090/webhook?event_type=fleet.events.deleted&name=simple-udp&namespace=default
```
List of Params

| Param        | Description               | Example                                         | 
| -----------  |:------------------------- | ----------------------------------------------- |
| name         | name of the resource      | simple-udp-pmx5c-xzfft                          |
| namespace    | namespace of the resource | default                                         |
| event_type   | type of the event fired   | fleet.events.deleted, gameserver.events.deleted |

## Diagram
Check the [diagram](docs/overview-diagram.png) from the docs folder for a visual overview of the aplication. 

## How to Install

Update the `install.yaml` file to reflect the endpoints that must be notified.

The list of endpoints can be specific for each kind of event if that is a requirement. Otherwise, just use the `--on-event-url` flag.

The url flags can be a list separated by comma.
```
--on-add-url=http://www.myendpoint.com,http://www.anotherendpoint.com/webhooks
``` 

```yaml
args:
    - --sync-period=15s # period between every reconcile cycle 
#   - --on-add-url=http://www.myendpoint.com/onadd
#   - --on-update-url=http://www.myendpoint.com/onupdate
#   - --on-delete-url=http://www.myendpoint.com/ondelete
    - --on-event-url=http://www.myendpoint.com/webhook
    - --verbose
```

Push the manifest that will create the required service account, RBAC and deployment.
```bash
$ kubectl -f deploy/install.yaml
```

## Local Server

Under the `hack` folder you can find the http server that can be used for local dev or testing. Start the server and use the url as the value for the url flags when running the agones relay application.
```bash
# Use the flag  --verbose=true to output the whole received request body
$ go run hack/server.go --verbose=false --addr=":8090" 
http server started on [::]:8090
INFO[0004] webhook received: onupdate/gameserver.events.updated
INFO[0004] webhook received: onupdate/gameserver.events.updated
INFO[0004] webhook received: onupdate/fleet.events.updated
INFO[0024] webhook received: onupdate/fleet.events.updated
INFO[0024] webhook received: onadd/gameserver.events.added
INFO[0024] webhook received: onadd/gameserver.events.added
INFO[0024] webhook received: onadd/gameserver.events.added
INFO[0024] webhook received: onadd/gameserver.events.added
INFO[0024] webhook received: onadd/gameserver.events.added
INFO[0024] webhook received: onupdate/gameserver.events.updated
INFO[0024] webhook received: onupdate/gameserver.events.updated
INFO[0024] webhook received: onadd/gameserver.events.added
INFO[0024] webhook received: onupdate/gameserver.events.updated
INFO[0024] webhook received: onupdate/gameserver.events.updated
INFO[0024] webhook received: onupdate/gameserver.events.updated
INFO[0083] webhook received: ondelete/gameserver.events.deleted default-simple-udp-9nt4c-qv7nm
INFO[0087] webhook received: ondelete/gameserver.events.deleted default-simple-udp-9nt4c-t46nx
INFO[0089] webhook received: ondelete/gameserver.events.deleted default-simple-udp-9nt4c-pt5fb
INFO[0150] webhook received: ondelete/fleet.events.deleted default-simple-udp
```

## Running

Make sure you have a valid `KUBECONFIG` file pointing to the running cluster where the Fleets and GameServers will be available.

```bash
go run main.go --kubeconfig=[PATH_TO_KUBECONFIG] --verbose --on-event-url=http://localhost:8090/webhook
```

You should expect some output simular to:

```bash
INFO[0000] starting worker                               queue=OnAdd worker=1
INFO[0000] starting worker                               queue=OnUpdate worker=1
INFO[0000] starting worker                               queue=OnDelete worker=1
{"controller_type":"v1.Fleet","message":"controller created for resource of type v1.Fleet","severity":"info","source":"controller","time":"2020-10-12T14:44:47.308991+02:00"}
{"controller_type":"v1.GameServer","message":"controller created for resource of type v1.GameServer","severity":"info","source":"controller","time":"2020-10-12T14:44:47.309462+02:00"}
{"message":"starting broadcaster","severity":"info","source":"broadcaster","time":"2020-10-12T14:44:47.309501+02:00"}
DEBU[0005] POST http://localhost:8090/webhook - 200 OK   queue=OnAdd worker=1
DEBU[0005] POST http://localhost:8090/webhook - 200 OK   queue=OnAdd worker=3
DEBU[0005] POST http://localhost:8090/webhook - 200 OK   queue=OnAdd worker=2
DEBU[0011] PUT http://localhost:8090/webhook - 200 OK    queue=OnUpdate worker=2
DEBU[0026] DELETE http://localhost:8090/webhook?name=simple-udp-9nt4c-b2xck&namespace=default&source=gameserver.events.deleted - 200 OK  queue=OnDelete worker=3
DEBU[0027] POST http://localhost:8090/webhook - 200 OK   queue=OnAdd worker=1
DEBU[0027] PUT http://localhost:8090/webhook - 200 OK    queue=OnUpdate worker=1

```

## Roadmap

- [ ] Add Authentication mechanism to HTTP Client
- [ ] Make number of workers flag based
- [ ] Option for minimal payload instead of the full K8S state
- [ ] Filter by label before publishing
- [ ] ...
