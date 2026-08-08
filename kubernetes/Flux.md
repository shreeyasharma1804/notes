### CLI Commands

```bash
# Install the controllers + The flux manifests at cluster

flux bootstrap github \
  --owner=shreeyasharma1804 \
  --repository=LocalCluster \
  --branch=main \
  --path=cluster/ \
  --personal
```
