### HMAC

- This is a pseudo random function

Equation:

```
HMAC(K,m)=H((K⊕opad) ∣∣ H((K⊕ipad) ∣∣ m))
m: message
K: secret
ipad: inner padding
opad: outer padding
H: SHA256
```
