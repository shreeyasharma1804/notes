### K8s managed volume

- A volume is created if a pod/deployment decalres it at the location: `/var/lib/kubelet/pods/<pod-uid>/volumes/kubernetes.io~empty-dir/`
- If a pod is restarted, the same volume is mounted on it, because the pod has the same uid.
- If a pod is evicted/deleted, the volume is deleted by the garbage collector and the data is lost
- In a deployment, all pods get a seperate volumne.

```yml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: writer
    image: busybox
    command: ["sh", "-c", "echo Hello > /shared/message && sleep 3600"]
    volumeMounts:
    - name: data
      mountPath: /shared
  volumes:
  - name: data
    emptyDir: {}
```

### HostPath

- The container mounts the node's directory in its file system
- The containers ability to read/write to this location depends on its user permissions

### PV

- PV: An object which declares that a storage is available.
- Defines the capacity and accessMode.
- A PV can be created manually (static provisioning) or automatically (dynamic provisioning through storageClassName)
- Access mode ReadWriteOnce means that the storage is mounted on only one node at a time
- A PV is not partitioned among multiple PVCs.
- One PV binds to exactly one PVC, so, to use hostPath across 5 nodes, 5 PVs should declare that.
- If a hostPath volume is only available on specific nodes, use node affinity on the pods which use the volume

- Static PV (uses hostPath)

```yml
# Static provisioning (This is not node specific)

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

- Local PV (It is a PV with node affinity, a pod which uses a PVC which is bound to this PV will always be scheduled based on the node affinity of the PV)

```yml
apiVersion: v1
kind: PersistentVolume
metadata:
  name: pv-local
spec:
  storageClassName: ""
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

```bash
kubectl get pv -A
NAME          CAPACITY   ACCESS MODES   RECLAIM POLICY   STATUS   CLAIM                  STORAGECLASS   VOLUMEATTRIBUTESCLASS   REASON   AGE
pv-bidir      500Mi      RWO            Retain           Bound    default/pvc-bidir                     <unset>
```

- PVs with claimRef only allow a PVC with that name to bind to them

```yml
# PV
claimRef:
  namespace: default
  name: pvc-bidir

# PVC
volumeName: pv-bidir
```

- PVs also support labels, and the PVCs can declare a label as a requirement before binding to a PV

```yml
# PV

metadata:
  name: pv-selector
  labels:
    disk-type: fast

# PVC

  selector:
    matchLabels:
      disk-type: fast
```

### PVC

- PVC: An object which decalres the requirement of storage
- Defines the storageClassName, required capacity and accessModes mode. If these requirements match the declaration in a PV, the PVC and PV bind
- A PVC affects the PV state:
  - Available - no PVC has claimed it
  - Bound - a PVC has claimed it
  - Released - the PVC that claimed it was deleted, but the PV still exists
- The reclaim policy of a PV decided what happens to a PV if its PVC is deleted
  - Reclaim: The PV is deleted if the PVC is deleted
  - Retain: After the PVC is deleted, the PV goes to the Released State. The claimRef still points to the deleted PVC and removing it makes the PV in the Available state again which can be bound to another PVC. The claimRef is removed throug patching


#### Usage in a deployment (Avoid this)

- Create a PVC
- Use in a deployment:

```
volumes:
- name: data
  persistentVolumeClaim:
    claimName: app-data      # The name of the PVC
```

- All the replica pods use the same PVC
- Considerations:
  - If the pod uses a hostPath PVC, and the storage is only available on specific nodes, then node affinity should be defined on the pods, otherwise the scheduling will fail. If the deployment has multiple replicas and they cannot be scheduled on the same node, and some other node does not have the hostPath directory, the pod will remain in pending state.
  - If a pod uses a local PV, kubernetes tries to  schedule the pod on the node that has the PV. If this is not possible for a pod or the replicas, it sits in Pending state
 
#### Usage in a StatefulSet

- Every stateful pod: pod-0 is tied to the same PVC: PVC-0
- Stateful sets support VolumeClaimTemplates, which automatically create PVCs for each replica with consistent names.

```yml
  volumeClaimTemplates:
  - metadata:
      name: data
    spec:
      accessModes:
        - ReadWriteOnce
      storageClassName: ""
      resources:
        requests:
          storage: 20Gi
```

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

The storage class creates a PV when a pod is created which references the PVC if volumeBindingMode: WaitForFirstConsumer, and creates the PV immediately if volumeBindingMode: Immediate

### OpenEBS

- OpenEBS provides dynamic provisioning of storage using LVM.
- The volumes can be expanded
- One vg is required, check using `sudo vg`. Other PV can be merged into the existing vg using vgextend
- If a PVC requested, it is provisioned using `sudo lvcreate`. The partition is then formatted and mounted.

Define the storage class:

```yml
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

```yml
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

- If volume expansion is true, the storage declared in a PVC can be increased.

### NFS

A Storage class with the NFS csi as the provisioner can be used to create a NFS volume. With PVC policy `ReadWriteMany`, multiple pods can write to the same location

### Management

- How to create volume expansion requests automatically for a PVC
- How to monitor performance

### Benchmarking using FIO (Flexible I/O)

```
apiVersion: batch/v1
kind: Job
metadata:
  name: storage-check
  namespace: storage-lab
spec:
  template:
    spec:
      restartPolicy: Never

      nodeSelector:
        kubernetes.io/hostname: cplane-01

      containers:
      - name: fio
        image: lfedge/eden-fio-tests:1b1b353
        command:
          - /bin/sh
          - -c
          - >
            fio --name=randwrite
            --filename=/data/testfile
            --size=1G
            --bs=4k
            --rw=randwrite
            --runtime=25
            --time_based
            --direct=1
            --output=/data/fio-result.txt
            && cat /data/fio-result.txt

        volumeMounts:
        - name: data-vol
          mountPath: /data

      volumes:
      - name: data-vol
        persistentVolumeClaim:
          claimName: app-data-pvc
```
