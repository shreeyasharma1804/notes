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

### OpenEBS

- OpenEBS provides dynamic provisioning of storage using LVM.
- The volumes can be expanded
- One vg is required, check using `sudo vg`. Other PV can be merged into the existing vg using vgextend
- If a PVC requested, it is provisioned using `sudo lvcreate`. The partition is then formatted and mounted.

Define the storage class:

```
apiVersion: storage.k8s.io/v1
kind: StorageClass

metadata:
  name: openebs-lvm

provisioner: local.csi.openebs.io

allowVolumeExpansion: true

parameters:
  storage: "lvm"
  volgroup: "lvmvg" # The name of the initial volume group
  fsType: ext4

volumeBindingMode: WaitForFirstConsumer
```

Use in a PVC:

```
apiVersion: v1
kind: PersistentVolumeClaim

metadata:
  name: postgres-pvc

spec:
  accessModes:
    - ReadWriteOnce

  storageClassName: openebs-lvm

  resources:
    requests:
      storage: 20Gi
```

After a pod claims the PVC, a PV is created and bound to the PVC
