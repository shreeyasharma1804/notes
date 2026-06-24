### Deployments

- Check the history of a deployment:

```bash
kubectl rollout history deployment/myapp
```

- Rollback

```bash
kubectl rollout history deployment/myapp --revision=2
```

- Rolling restart

```bash
kubectl rollout restart deployment/myapp
```
