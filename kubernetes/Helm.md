- A helm repo a remote git repositry which contains an index containing all the available charts in the repo
- helm repo list: List all available repos
- helm repo add sample_repo_1 https://shreeyasharma1804.github.io/helm-charts/ : Add a repo

```
# Add a repo
helm repo add <name> <url>
helm repo add bitnami https://charts.bitnami.com/bitnami

A remote helm repo contains an index file which contains entries of chart name, chart version and its url location

The tar file contains the template, chart.yml, values.yml

# Show all added repos
helm repo list
NAME         	URL      
bitnami      	https://charts.bitnami.com/bitnami

# search for a chart (This searches the index.yml from the added repos)
helm search repo <search string>
helm search repo redis
NAME                 	CHART VERSION	APP VERSION	DESCRIPTION                                       
bitnami/redis        	27.0.10      	8.8.0      	Redis(R) is an open source, advanced key-value ...

#  Update the repo
helm repo update


#  Check the chart:
helm show chart bitnami/redis

# Check the values
helm show values bitnami/redis

# Check everything
helm show all bitnami/redis

# Render the templates, but do not install anything
helm template redis bitnami/redis

# Render the template with a custom values file
helm template redis bitnami/redis -f values.yaml

helm install redis bitnami/redis --dry-run --debug
```
