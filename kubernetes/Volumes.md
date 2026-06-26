### K8s managed volume

```yml
volumes:
- name: data
  emptyDir: {}
```

This volume survives a pod restart but not a pod deletion


### PV and PVC

PV: An object which declares that a storage is available
PVC: Declare the requirement of storage by claiming a PV

If the storageClassName, capacity and accessModes match, a PVC binds to a PV

```bash
kubectl get pv -A
NAME          CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                  STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
pv-bidir      500Mi      RWO            Retain           Bound    default/pvc-bidir                     <unset>
```

The actual directory is only created after a pod uses a PVC on the node where the pod is scheduled. This can cause issues such as new pod scheduling on different nodes will create empty directories.

PV Phases:

- Available - no PVC has claimed it
- Bound - a PVC has claimed it
- Released - the PVC that claimed it was deleted, but the PV still exists

#### Static provisioning

An administrator manually declares the storage availability

```yml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-generic
spec:
  storageClassName: ""
  capacity:
    storage: 500Mi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: /mnt/static/generic
    type: DirectoryOrCreate
```

This object declares that 500MB storage is available at /mnt/static/generic. (This is not node specific)

#### Claim References

A PV is bound to a PVC based on the volumeName. In the example here, no other PVC can use this PV, unless it has the volumeName = pv-bidir

PV:

```yml
claimRef:
  namespace: default
  name: pvc-bidir
```

PVC:

```yml
volumeName: pv-bidir
```

#### Label based selection

A PV can be associated with labels:

```yml
metadata:
  name: pv-selector
  labels:
    disk-type: fast
```

And a PVC can declare the label selection:

```yml
  selector:
    matchLabels:
      disk-type: fast
```

#### Local PV

A local PV is a PV bound to a node through node affinity

```yml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-local
spec:
  storageClassName: "sc-local-wfc"
  capacity:
    storage: 1Gi
  accessModes:
    - ReadWriteOnce
  local:
    path: /mnt/disks/local
  nodeAffinity:
    required:
      nodeSelectorTerms:
      - matchExpressions:
        - key: kubernetes.io/hostname
          operator: In
          values:
          - cplane-01
```

A pod which uses a PVC which is bound to this PV will always be scheduled based on the node affinity of the PV

#### StorageClass

Storage classes omit the requirement of manual PV creation through dynamic provisioning

This storage class requires manual provisioning:

```yml
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: sc-local-wfc
provisioner: kubernetes.io/no-provisioner
volumeBindingMode: WaitForFirstConsumer
```

```yml
kubectl get storageclass
```
