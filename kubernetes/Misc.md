- Mutating Admission policy: https://kubernetes.io/docs/reference/access-authn-authz/mutating-admission-policy/
- Validating Admission policy: https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/


- Security context: The main process inside the container runs as UID and GID 1000 on the host
```yml
securityContext:
  runAsGroup: 1000
  runAsUser: 1000
```
