### Bootstrapping

```bash
# Install the controllers + The flux manifests at cluster

flux bootstrap github \
  --owner=shreeyasharma1804 \
  --repository=LocalCluster \
  --branch=main \
  --path=/ \
  --personal
```

### Kustomize setup

```bash

# Check the flux installtion status
flux check
flux version

# Dry run
kubectl kustomize cluster

# Show all the GitRepository resources and describe them
kubectl get gitrepository -n flux-system
kubectl describe gitrepository -n flux-system

# Shows all the Flux Kustomization resources and describe them
kubectl get kustomization -n flux-system
kubectl describe kustomization -n flux-system

# Force a git refresh
flux reconcile source git flux-system

# Force a kustomize refresh
flux reconcile kustomization flux-system

# Suspend git polling
flux suspend source git flux-system

# Resume
flux suspend resume git flux-system
```
