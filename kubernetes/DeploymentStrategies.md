## Helm

### Repository

- A helm repository is a remote git repository which contains an index.yml file containing all the available charts in the repo, and the tar files of the chart+values+templates
- Helm projects are scaffold through:

```bash
helm create helm-app
# Creates the chart.yml, values.yml and templates. Here, the chart name is helm-app

helm package helm-app
# Compress all the above code into a tar file in the same directory

helm repo index .
# Create index.yaml, which contains chart_name: tar file mapping

# Push to index and package to git, this repo will be used to run commands like helm add repo
# Also push the chart code itself to git, to maintain the changes made to the boilerplate itself
```

#### Making changes to repo

- If a general setting is changed, Make the changes in the code, change the chart version, re-package and re-index
- If an application level is made, Make the changes in the code, change the chart version and the app version, re-package and re-index
- Lint

```bash
helm lint <chart-direcotry>
```

- All chart versions will be available via index.yaml
- In case of multiple chart versions, the latest version is used by default
- helm repo add basically runs GET https://example.com/charts/index.yaml, thus github pages are required so that the GET request returns a valid yaml file

#### Repository Operations

- Add a repository

```bash
# This works by fetching https://charts.bitnami.com/bitnami/index.yml and installing it under the name bintami
helm repo add bitnami https://charts.bitnami.com/bitnami
```

- List all added repos

```bash
helm repo list
NAME          	URL
bitnami         https://shreeyasharma1804.github.io/helm-charts/
```

- Update the repo

```bash
helm repo update
# Only updates the repository index
```

- Search for a chart

```bash
helm search repo <chart name>
```

### Viewing data

#### View the installed chart version (repo_name/chart_name)

```bash
helm show chart bitnami/redis
```

#### View the default repo values

```bash
helm show values bitnami/redis
```

### Templating and dry installs

#### Print the template of the K8s objects which will installed from the chart under the release name redis

```bash
helm template redis bitnami/redis
```

#### Print the template with custom values

```bash
helm template redis bitnami/redis -f values.yaml
```

#### dry-run the installation

```bash
helm install redis bitnami/redis --dry-run --debug
```

# dry-run the upgrade

```bash
helm upgrade redis bitnami/redis --dry-run --debug
```

### Release management

#### Install a new release (release_name repo/chart_name)

```bash 
helm install redis bitnami/redis
```

####  Upgrade a release, this is run after helm repo update to install the new chart versions

```bash
helm upgrade redis bitnami/redis
```

#### Upgrade and install

```bash
helm upgrade --install redis bitnami/redis
```

#### Install with custom values.yaml

```bash
helm install redis bitnami/redis -f cluster-config/production/values.yaml
```

#### List all releases

```bash
helm list
helm list -A
```

#### Uninstall a release

```bash
helm uninstall redis
```

#### Release status

```bash
helm status redis
```

#### Get the values being used in the current release

```bash
helm get values redis
```

#### Check the history of the release

```bash
helm history redis
```

#### Rollback release to a previous version

```bash
helm rollback redis <required revision number>
```

#### Diff the currently installed release with the values in ./chart

```bash
helm diff upgrade redis ./chart
```

### Restart pods if a change is made in configmap

- Kubernetes only restarts the pods of a deployment if the pod template is changed.
- Whether a pod has been restarted can be checked with the "AGE" column of pod describe command.
- Whenever a pod is restarted, a new replicaset is created. The older one is kept for rollback purposes. Check with `kubectl get rs`
- To ensure that the pods are restarted every-time the configmap is changed, add to the pod metadata:

```yml
annotations:
  checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
```

### Blue-green deployments

- Use 2 deployments for the same app, and make the changes to only one of the deployment
- Keep the service pointed to the older deployment
- Once the changes are validated, the service can point to the new pods

### Canary deployments

- x% pods run using the new image tag whereas 100-x% servers run the old image tag

```yml
# deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.appName }}-deployment
  labels:
    app: {{ .Values.appName }}
spec:
  {{- if .Values.canary.enabled }}
  replicas: 3
  {{- else }}
  replicas: 4
  {{- end }}
  selector:
    matchLabels:
      app: {{ .Values.appName }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels:
        app: {{ .Values.appName }}
    spec:
      containers:
        - name: {{ .Values.appName }}-container
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          ports:
          - containerPort: 5000
          envFrom:
          - configMapRef:
              name: {{ .Values.appName }}-configmap

# deployment-canary.yml
{{- if .Values.canary.enabled }}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Values.appName }}-canary-deployment
  labels:
    app: {{ .Values.appName }}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: {{ .Values.appName }}
  template:
    metadata:
      annotations:
        checksum/config: {{ include (print $.Template.BasePath "/configmap.yaml") . | sha256sum }}
      labels:
        app: {{ .Values.appName }}
    spec:
      containers:
        - name: {{ .Values.appName }}-container
          image: "{{ .Values.image.repository }}:{{ .Values.image.canaryTag }}"
          ports:
          - containerPort: 5000
          envFrom:
          - configMapRef:
              name: {{ .Values.appName }}-configmap
{{- end }}
```

### Kustomize:

- The kustomization.yml file contains all the customizations which will be applied on the manifests
- The resources field contains the manifests on which the kustomization will be applied
- The order is: recursively reach the kustomization file which contains only manifests and no resources term
- Transformation order: https://github.com/kubernetes-sigs/kustomize/pull/1154/changes#diff-08cc185c76276233438d343b0674803a4f5612b1808688a5d372f6fd14bffbd9

Documentation: https://k8s.info/docs/core/kustomize#5-key-concepts-in-depth

#### Commands

```
# Render the manifests to be deployed, the deployment is carried out via flux
kubectl kustomize overlays/dev/. 
```

#### Transformation

- nameSuffix: -dev


#### Patching

- Kustomization identifies the resource where the patch should be applied via:

```
Group + Version + Kind + Namespace + Name
```

```yaml
```

## Flux

### Bootstrapping

#### Using flux operator

- Install flux operator

```bash
helm upgrade -i flux-operator \
  oci://ghcr.io/controlplaneio-fluxcd/charts/flux-operator \
  --namespace flux-system \
  --create-namespace \
  --wait
```

- Apply flux-instance.yaml, GitRepository.yaml, kustomization.yaml (Check local repo)
- This starts the initial reconciliation
- Add the files to the git repo for future reconciliations as well

#### Manually

```bash
# Install the controllers + The flux manifests at cluster

flux bootstrap github \
  --owner=shreeyasharma1804 \
  --repository=LocalCluster \
  --branch=main \
  --path=/ \
  --personal
```

### Operations

#### Check the web UI:

```bash
kubectl -n flux-system port-forward svc/flux-operator 9080:9080
```

#### Check the installation status (Web ui can also be used)

```bash
flux check
flux version
```


#### GitRepository

- At the refresh interval, GitRepository fetches the required branch and creates an artifact if changes are detected
- Check the events (and logs as well):

```
kubectl get gitrepository -n flux-system

# Normal  NewArtifact                 3m27s  source-controller  stored artifact for commit 'Update'
# The events show the commit message which has been reconcileld
```

#### Kustomization

- Avoid cluster drift due to manual patches
- prune allows to delete objects not in git 

```bash
kubectl get kustomization -n flux-system
```

#### Force Reconcilliation

```bash
# Force a git refresh
flux reconcile source git flux-system

# Force a kustomize refresh
flux reconcile kustomization flux-system
```

#### Suspend git polling

```
flux suspend source git flux-system

# Resume
flux suspend resume git flux-system
```

Note: If the GitRepository controller creates a new artifact, the Kustomization controller also runs.
