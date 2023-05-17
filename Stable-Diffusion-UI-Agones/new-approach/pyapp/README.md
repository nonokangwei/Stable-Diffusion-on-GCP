
# Simple Agones allocator service

## Use the dockerfile to build 

```
export REGISTRY=your-registry
docker build . -t $REGISTRY/py-gpu-sche:0.1
```


## Run in Kubernetes

Replace $REGISTY to your-registry

```yaml
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: py-gpu-sche
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: py-gpu-sche
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: admin
subjects:
- kind: ServiceAccount
  name: py-gpu-sche
  namespace: default
---
apiVersion: v1
kind: Service
metadata:
  name: ngx-scheduler
  namespace: default
spec:
  ports:
  - port: 8080
    protocol: TCP
    targetPort: 8080
  selector:
    app: ngx-scheduler
  type: NodePort
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ngx-scheduler
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ngx-scheduler
  template:
    metadata:
      labels:
        app: ngx-scheduler
    spec:
      serviceAccountName: py-gpu-sche
      containers:
      - name: py-gpu-sche
        image: $REGISTRY/py-gpu-sche:0.3.1
        ports:
        - containerPort: 8080
          protocol: TCP

```

## Interface

- Request Method: POST
- Request Path: /creategs
- Request Body: {"data": {"userid": "the-user-id"}}

Example:

```shell
curl -X POST -H "Content-Type: application/json" http://127.0.0.1:8001/creategs -d '{"data":{"userid":"xxx"}}'
```

