# Provision agones component
helm repo add agones https://agones.dev/chart/stable

helm repo update

helm install sd-agones-release --namespace agones-system -f values.yaml agones/agones


# Install Fleet and Fleet scale policy

