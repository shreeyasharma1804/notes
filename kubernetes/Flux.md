### Bootstrapping

```bash
# Install the controllers + The flux manifests at cluster

flux bootstrap github \
  --owner=shreeyasharma1804 \
  --repository=LocalCluster \
  --branch=main \
  --path=cluster/ \
  --personal
```

### Kustomize setup

```bash

# Check the flux installtion status
flux check
flux version

# Dry run
kubectl kustomize cluster

# Show all the GitRepository resources
flux get sources git

# Shows all the Flux Kustomization resources
flux get kustomizations

# Shows the kustomization details, including the reconciliation events
kubectl describe kustomization flux-system -n flux-system

# Force a git refresh
flux reconcile source git flux-system

# Force a kustomize refresh
flux reconcile kustomization flux-system

# Suspend git polling
flux suspend source git flux-system

# Resume
flux suspend resume git flux-system
```
