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

A automatic rolling restart is performed by a deployment if the pod template is changed. This is possible because a new replicaset is created and the older replicaset is still available

-  Every deployments is annotated with:

```yml
Annotations: deployment.kubernetes.io/revision: 1
```

This defines the edits which have been made to the pod template of the deployment

- The deployment description also contains:

```yml
OldReplicaSets:    <none>
NewReplicaSet:     klustered-5b7c7bfc5 (0/1 replicas created)
```

- Any changes made to the pod template issue the creation of a new replicaset
- A deployment is also associated with:

```yml
generation: 8
```

This field is updated when the deployment spec changes

- If a pod is created from a deployment, not all changes are allowed on the pod. Also, the changes are not kept if the deployment is restarted
