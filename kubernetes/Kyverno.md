```yml
apiVersion: policies.kyverno.io/v1
kind: ValidatingPolicy
metadata:
  name: check-labels
spec:
  validationActions:
    - Deny
  matchConstraints:
    resourceRules:
      - apiGroups: ["*"]
        apiVersions: ["*"]
        operations: [CREATE, UPDATE]
        resources: ["*"]
  validations:
    - message: label 'team' is required
      expression: |
          has(object.metadata.labels) &&
          has(object.metadata.labels.team) &&
          object.metadata.labels.team != ""
```

-----------------------

```yml
apiVersion: policies.kyverno.io/v1
kind: ValidatingPolicy
metadata:
  name: check-cpu-usage
spec:
  validationActions:
    - Deny
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: [CREATE, UPDATE]
        resources: ["deployments"]
  validations:
    - message: CPU requests is required
      expression: |
        object.spec.template.spec.containers.all(c, has(c.resources) && has(c.resources.requests) && has(c.resources.requests.cpu))
```

-----------------------


```yml
apiVersion: policies.kyverno.io/v1
kind: ValidatingPolicy
metadata:
  name: check-replicas
spec:
  validationActions:
    - Deny
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: [CREATE, UPDATE]
        resources: ["deployments"]
  validations:
    - message: Replicas should be less than 10
      expression: |
        object.spec.replicas <= 10
```

------------------------

```yml
apiVersion: policies.kyverno.io/v1
kind: ValidatingPolicy
metadata:
  name: check-registry
spec:
  validationActions:
    - Deny
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: [CREATE, UPDATE]
        resources: ["deployments"]
  validations:
    - message: Only one allowed image registry
      expression: |
        object.spec.template.spec.containers.all(c, c.image.matches(^"registry\\.company\\.com"))
```

------------------------

```yml
apiVersion: policies.kyverno.io/v1
kind: ValidatingPolicy
metadata:
  name: remove-privilaged-context
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ['apps']
        apiVersions: ['vi']
        operations: ['CREATE', 'UPDATE']
        resources: ['deployments']

  validations:
  - message: securityContext privileged should not be true
    expression: |
        object.spec.template.spec.containers.all(c, !has(c.securityContext) || !has(c.securityContext.privileged) || c.securityContext.privileged != true)
```

------------------------

```yml
apiVersion: policies.kyverno.io/v1
kind: MutatingPolicy
metadata:
  name: add-cpu-request
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ["apps"]
        apiVersions: ["v1"]
        operations: ["CREATE", "UPDATE"]
        resources: ["deployments"]
  mutations:
    - patchType: ApplyConfiguration
      applyConfiguration:
        expression: >
          Object{
            spec: Object.spec{
              template: Object.spec.template{
                spec: Object.spec.template.spec {
                  containers: object.spec.template.spec.containers.map(c,
                  Object.spec.template.spec.containers{
                      name: c.name
                      resources: Object.spec.template.spec.containers.resources {
                        requests: Object.spec.template.spec.containers.resources.requests{
                          cpu: has(c.resources) && has(c.resources.requests) && !has(c.resources.requests.cpu) ? c.resources.requests.cpu : "100m"
                        }
                      }
                    }
                  )
                  }
                }
              }
            }
          }
```

-----------------------

```yml
apiVersion: policies.kyverno.io/v1
kind: MutatingPolicy
metadata:
  name: add-image-pull-policy
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ['apps']
        apiVersions: ['v1']
        operations: ['CREATE', 'UPDATE']
        resources: ['DEPLOYMENTS']
  mutations:
    - patchType: ApplyConfiguration
      applyConfiguration:
        expression: >
          Object{
            spec: Object.spec{
              template: Object.spec.template{
                spec: Object.spec.template.spec{
                    containers: object.spec.template.spec.containers.map(c, Object.spec.template.spec.containers{
                        name: c.name,
                        imagePullPolicy: has(c.imagePullPolicy) ? c.imagePullPolicy : "IfNotPresent"
                    })
                }
              }
            }
          }
```

------------------------

```yml
apiVersion: policies.kyverno.io/v1
kind: MutatingPolicy
metadata:
  name: add-namespace-based-labels
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ['*']
        apiVersions: ['*']
        operations: ['CREATE', 'UPDATE']
        resources: ['*']
  matchConditions:
    - name: research-namespace
      expression: object.metadata.namespace == "research"
  mutations:
    - patchType: ApplyConfiguration
      applyConfiguration:
        expression: >
          Object{
            metadata: Object.metadata{
                labels: Object.metadata.labels {
                    sensitivity: "High"
                }
            }
          }
```

------------------------

```yml
apiVersion: policies.kyverno.io/v1
kind: MutatingPolicy
metadata:
  name: add-topology-for-deployments
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ['apps']
        apiVersions: ['v1']
        operations: ['CREATE', 'UPDATE']
        resources: ['deployments']
  matchConditions:
    - name: no-topology-policy
      expression: !has(object.spec.template.spec.topologySpreadConstraints)
  mutations:
    - patchType: ApplyConfiguration
      applyConfiguration:
        expression: >
          Object{
            spec: Object.spec{
                template: Object.spec.template {
                    spec: Object.spec.template.spec {
                        topologySpreadConstraints: Object.spec.template.spec.topologySpreadConstraints{
                            maxSkew: 1,
                            topologyKey: kubernetes.io/hostname,
                            whenUnsatisfiable: ScheduleAnyway,
                            labelSelector: Object.spec.template.spec.topologySpreadConstraints.labelSelector {
                                matchLabels: Object.spec.template.spec.topologySpreadConstraints.labelSelector.matchLabels{
                                    app: object.metadata.labels.app
                                }
                            }
                        }
                    }
                }
            }
          }
```

-------------------------

```yml
apiVersion: policies.kyverno.io/v1
kind: MutatingPolicy
metadata:
  name: imagePullPolicy-for-defaultRegistry
spec:
  matchConstraints:
    resourceRules:
      - apiGroups: ['apps']
        apiVersions: ['v1']
        operations: ['CREATE']
        resources: ['deployments']
  mutations:
    - patchType: ApplyConfiguration
      applyConfiguration:
        expression: >
          Object{
            spec: Object.spec{
              template: Object.spec.template{
                spec: Object.spec.template.spec {
                    containers: object.spec.template.spec.containers.filter(c,
                        !c.image.startsWith("registry.example.com")).map(c, Object.spec.template.spec.containers{
                            name: c.name
                            imagePullPolicy: "IfNotPresent"
                        })
                }
              }
            }
          }
```
