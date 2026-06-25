### K8s managed volume

```yml
volumes:
- name: data
  emptyDir: {}
```

This volume survives a pod restart but not a pod deletion
