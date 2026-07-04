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
- tls: For TLS certificates (accepts --key and --cert)
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

kubectl create secret tls tls-secret \
    --key=tls.crt \
    --cert=tls.key
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

If the secret is updated, kubelet automatically updates the mounted file contents at kubelet sync time. No restart is required

- All secrets are stored in a encrypted format in the etcd server.
- A kubelet is authorized to retrieve a Secret only if that Secret is referenced by a Pod that has been scheduled to that kubelet's node.

If a secret is static: Use env variable

If a secret can be modified: Use files

### Dynamic secret refresh (External vault)

This allows to store the secrets in a vault and not in the cluster/yaml files

- Approach1: Use cert-manager to create a certificate with a particular CA, CN, SAN etc(The format should be such that the cert is allowed to access sevrets from the vault). Create a sidecar which loads this certificate from the secret and fetches the secrets at the rate of refreshInterval. Here, every pod is responsible for managing its secrets and the k8s secret object is not used.

- Approach2: Use ESO, which updates the k8s secret and all pods mountiung the secret as a file get the renewed cert at kubelet sync interval. In both these approaches, the application should handle the file data update, maybe through inotify and update it's in memory cache.

- Approach3:
    - Vault with a webhook(The secret should be configured with a namepsace) that calls an endpoint on the cluster.
    - The API updates the k8s secret.
    - The secret update in the vault is acknowledged only after the k8s secret is updated.

#### External Secrets operators

SecretStore: Define how to connect to the secret store with authentication

```yml
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata:
  name: vault-store
spec:
  provider:
    vault:
      server: https://vault.example.com
```

ESO: Creates a kube secret named database-secret with value fetch from vault secret production/database

```yml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: db-secret
spec:
  refreshInterval: 1h

  secretStoreRef:
    name: vault-store

  target:
    name: database-secret

  data:
    - secretKey: password
      remoteRef:
        key: production/database
        property: password
```

### ConfigMap

Store environment variables, if the variables are static, mount them as environment variables, else, mount them as files

#### Defination:

```yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config

data:
  DATABASE_HOST: postgres
  DATABASE_PORT: "5432"
  LOG_LEVEL: info
```

#### Usage:

- Load as environment variables

```yml
env:
- name: DB_HOST
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: DATABASE_HOST

- name: DB_PORT
  valueFrom:
    configMapKeyRef:
      name: app-config
      key: DATABASE_PORT
```

- Mount as a file

```yml
volumes:
- name: config
  configMap:
    name: app-config

volumeMounts:
- name: config
  mountPath: /etc/config
```

#### Generators and automatic pod restart

### cert-manager

#### Issuer

```yml
apiVersion: cert-manager.io/v1
kind: Issuer
metadata:
  name: selfsigned
spec:
  selfSigned: {}
```

#### Certificate

- Create a tls secret named api-server-tls, with issuer defined in issuerRef, other details and expiry time

```yml
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: api-cert
  namespace: default
spec:
  secretName: api-server-tls

  issuerRef:
    name: selfsigned
    kind: Issuer

  commonName: api.example.com

  dnsNames:
    - api.example.com

  duration: 2160h      # 90 days
  renewBefore: 360h    # renew 15 days before expiry
```

### LimitRange

LimitRange is an admission policy managed by a controller (can be disabled in the kube-apiserver.yaml ). It defines the min,max and default resources a pod can request.

When a Pod is created, the kube-apiserver passes it through a chain of admission controllers before persisting it to etcd. The LimitRanger admission controller is the one responsible for reading the LimitRange in the namespace and injecting the default values into the Pod spec. If this controller is disabled, the LimitRange object exists but is completely ignored — Pods are admitted as-is with no defaults applied.

This is a creation-time mechanism. LimitRange does not patch existing Pods retroactively. Once you re-enable the admission controller, you must restart the Deployment so new Pods go through admission and pick up the defaults.

```yml
apiVersion: v1
kind: LimitRange
metadata:
  name: resource-limits
spec:
  limits:
  - type: Container
    min:
      cpu: "100m"
      memory: "128Mi"
    max:
      cpu: "2"
      memory: "4Gi"
    default:
      cpu: "500m"
      memory: "512Mi"
    defaultRequest:
      cpu: "250m"
      memory: "256Mi"
```

```bash
kubectl get LimitRange -n <namespace>
```

### ResourceQuata

Defines the hard limits of the overall resouces that a namespace can use

```yml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: ns-quota
spec:
  hard:
    requests.cpu: "4"
    requests.memory: 8Gi
    limits.cpu: "8"
    limits.memory: 16Gi
```

If a resource(example CPU) is in the hard limit, but there is no limit range defining the default value, then a pod which does it specify that resource requirement is rejected for creation 

### HPA

```yml
apiVersion: autoscaling/v2  
kind: HorizontalPodAutoscaler  
metadata:  
	name: api-hpa  
	namespace: production  
spec:  
	scaleTargetRef: # what to scale  
		apiVersion: apps/v1  
		kind: Deployment  
		name: api  
	minReplicas: 2  # never go below this  
	maxReplicas: 20  # never go above this  
metrics:  
	- type: Resource  
		resource:  
			name: cpu                                # This is the CPU limits
			target:  
				type: Utilization  
				averageUtilization: 60
```

The pods are scaled ccording to the formula:

```
desiredReplicas = ceil( currentReplicas × ( currentMetricValue ÷ desiredMetricValue ) )
```

- Here, the currentMetricValue is the avergae CPU utilization of all the pods in the deployment targetted by the HPA.
- If a pod requests 100m cpu, and the current utilization is 50m, the currentMetricValue is 50%.
- To use HPA, the deployment needs to define the cpu requests

Test using load generator pod for a deployment exposed with a service

```yml
kubectl run load-gen \
  --image=busybox \
  --restart=Never \
  -- sh -c "while true; do wget -q -O- http://web; done"
```

### VPA

- Generate recommendations for resouces of a deployment.
- Check the recommendations using: `kubectl describe vpa web-app-vpa -n production`
- Goldilocks provides a dashboard for this

```yml
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: web-app-vpa
  namespace: production
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: web-app

  updatePolicy:
    updateMode: "Off"

  resourcePolicy:
    containerPolicies:
    - containerName: main-app
      mode: "Auto"
      minAllowed:
        cpu: 100m
        memory: 128Mi
      maxAllowed:
        cpu: "2"
        memory: 2Gi
      controlledResources:
      - cpu
      - memory
      controlledValues: RequestsOnly
    - containerName: log-sidecar
      mode: "Off"
```
