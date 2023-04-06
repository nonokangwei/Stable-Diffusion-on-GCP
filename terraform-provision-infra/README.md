# Infrastructure Provision Step

Foobar is a Python library for dealing with word pluralization.

## Set up permissions

Make sure that you have the necessary permissions on your user account:

- ROLE: roles/artifactregistry.admin

- ROLE: roles/compute.admin

- ROLE: roles/compute.instanceAdmin.v1

- ROLE: roles/compute.networkAdmin

- ROLE: roles/container.admin

- ROLE: roles/file.editor


## Replace project parameter

edit the main.tf replace the locals with your project's. example as follow

```bash
locals {
  project_id    = "project_id"
  region        = "us-central1"
  zone          = "us-central1-f"
  gke_num_nodes = 1
}
```

## Provision Infrastructure (VPC | Subnet | NAT | FileStore | Artifact Registry | GKE | GKE FileStore PV and PVC  )

```bash
# init terraform
terraform init

# deploy Infrastructure
terraform plan
terraform apply -auto-approve

# destroy Infrastructure
terraform destroy -auto-approve
```

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)