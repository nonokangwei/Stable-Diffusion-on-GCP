#!/bin/bash
kubectl label clusterroles agones-allocator rbac.authorization.k8s.io/aggregate-to-admin="true"
kubectl label clusterroles agones-sdk rbac.authorization.k8s.io/aggregate-to-admin="true" 
kubectl label clusterroles agones-controller rbac.authorization.k8s.io/aggregate-to-admin="true" 
