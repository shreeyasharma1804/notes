### Repository

- A helm repository is a remote git repositry which contains an index.yml file containing all the available charts in the repo, and the tar files of the chart+values+templates

```bash
# Add a repo (repo_name url)
helm repo add bitnami https://charts.bitnami.com/bitnami

# List all added repos
helm repo list

# Update the repo (fetch remote)
helm repo update (Only updates the repository index)

# Search the charts in a repo
helm search repo <chart name>
```

### View the data

```
# View the chart (repo_name/chart_name)
helm show chart bitnami/redis

# View the values
helm show values bitnami/redis

helm show all bitnami/redis
```

### Render and dry runs

```
# Render the template (release_name repo_name/chart_name)
helm template redis bitnami/redis

# Render with custom values
helm template redis bitnami/redis -f values.yaml

# perform linitng
helm lint ./chart

# Installation dry-run
helm install redis bitnami/redis --dry-run --debug

# Upgrade dry-run
helm upgrade redis bitnami/redis --dry-run --debug
```

### Release management

```
# Install a new release (release_name repo/chart_name)
helm install redis bitnami/redis

# Upgrade a release, this is run after helm repo update to install the new chart versions
helm upgrade redis bitnami/redis

# Install and upgrade
helm upgrade --install redis bitnami/redis

# List releases
helm list
helm list -A

# Uninstall a release
helm uninstall redis

# Release status
helm status redis

# Get the values being used in the current release
helm get values redis

# Get all the variables of the release
helm get all redis

# Check the history of the release
helm history redis

# Rollback release to a previous version
helm rollback redis 2

# Diff the currently installed release with the values in ./chart
helm diff upgrade redis ./chart
```

### Restart pods if a change is made in configmap

- Kubernetes only restarts the pods of a deployment if the pod template is changed.
- Whether a pod has been restarted can be checked with the "AGE" column of pod describe command.
- Whenever a pod is restarted, a new replicaset is created. The older one is kept for rollback purposes
