### Webhooks

Instead of polling the server, we can define a webhook, which sends a POST call based on the event.

Usage in git:

```bash
Configure webhook in git which sends a POST call to a server when a push event occurs -> Server registers the CI job based on the POST call data
```
