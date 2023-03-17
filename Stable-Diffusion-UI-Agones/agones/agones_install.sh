# Provision agones component
helm repo add agones https://agones.dev/chart/stable

helm repo update

helm install my-release --namespace agones-system --set agones.allocator.disableMTLS=true,agones.allocator.disableTLS=true agones/agones


# Install Fleet and Fleet scale policy

