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

- If a pod is created from a deployment, not all changes are allowed on the pod. Also, the changes are not kept if the deployment is restarted. Similar to a deployment, if an edit is accepted, the pod generation is updated

### Replicasets

- Change the desired number of replicas

```bash
kubectl scale deployment <deployment name> --replicas=1
```

- For a replicaset to reconcile, the replicaset controller should be running
- For any errors, check the controller logs

```bash
kubectl -n kube-system logs kube-controller-manager-cplane-01
```

### Secrets

#### Types:

- generic: Generic user data
- tls: For TLS certificates
- docker-registry: Docker registry login information

#### Declaration:

- Declare in file: Here, the data is base64 encoded

```yml
apiVersion: v1
kind: Secret
metadata:
  name: db-secret

type: Opaque

data:
  username: YWRtaW4=
  password: cGFzc3dvcmQ=
```

- Command

```bash
kubectl create secret generic db-secret \
    --from-literal=username=admin \
    --from-literal=password=password

kubectl create secret generic tls-secret \
    --from-file=tls.crt \
    --from-file=tls.key
```

#### Usage

- Environment variables: Inside the pod, the secret is available as an environment variable

```yml
env:
- name: DB_USER
  valueFrom:
    secretKeyRef:
      name: db-secret
      key: username

- name: DB_PASSWORD
  valueFrom:
    secretKeyRef:
      name: db-secret
      key: password
```

If the secret is updated, a pod restart is required

- Mount as a file: Inside the pod, the secret is available as files /etc/secrets/username and /etc/secrets/password

```yml
volumes:
- name: secret-volume
  secret:
    secretName: db-secret

containers:
- volumeMounts:
  - mountPath: /etc/secrets
    name: secret-volume
```

If the secret is updated, kubelet automatically updates the mounted file contents. No restart is required

- All secrets are stored in a encrypted format in the etcd server.
- A kubelet is authorized to retrieve a Secret only if that Secret is referenced by a Pod that has been scheduled to that kubelet's node.
