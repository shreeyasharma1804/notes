
## Encryption algorithms

### RSA

- Public key
`n`: Very large number (p*q)
`e` = exponent

- Private key:
`d`: decryption coefficient
`p`: very large prime
`q`: very large prime

- Encrypted message:

$$
(m^e) mod n
$$

- Decrypt the message using:

$$
m^{ed} mod n = m
$$

#### Proof:

gcd(a,b) is the highest common divisor of both a and b.
Coprimes: gcd(a,b)  = 1

Euler's totient:

$$
\phi (n)
$$

Is the total number of coprimes of n

If n is a prime number:

$$
\phi (n) = n-1
$$

If n is a product of 2 prime numbers p,q:

$$
\phi (n) = (p-1)(q-1)
$$

Euler's theorum:

$$a^{\phi(b)} \bmod b = 1 \text{ where } \gcd(a,b) = 1$$

RSA:

Choose e,d such that

$$
ed = 1+k\phi(n)
$$

Should satisfy:

$$
m^{ed} mod n = m
$$

Thus

$$
m^{1+k\phi(n)} mod n = m*m^{k\phi(n)} mod n
$$

By the eurlers theorum:

$$
m^{k\phi(n)} mod n = 1
$$

if m and n are coprimes

Thus,

$$
m^{k\phi(n)} mod n = 1
$$

and

$$m^{ed} \bmod n = m$$

### Diffie-Hellman (Symmetric encryption)

Public key components:
- `n`: A very huge prime number (2000-4000 bits)

- `g`(generator): A small number

For sender A, consider its private key value to be `a`

For sender B, consider its private key value to be `b`

A calculates:

$$g^{a} \bmod n$$

B calculates:

$$g^{b} \bmod n$$

Since the above values can range between 1 to n, without figuring out the private value, they can be shared.

Consider A's public key:

$$g^{a} \bmod n$$

And it recieves:

$$g^{b} \bmod n$$

Also:

$$g^{a} \bmod n * g^{b} \bmod n = g^{a+b} \bmod n$$

Proof:

$$g^{a} = c_1n + k_1$$

$$g^{b} = c_2n + k_2$$

$$g^{a} \bmod n * g^{b} \bmod n = k_1*k_2$$

$$g^{a}*g^{b} = (c_1n + k_1)(c_2n + k_2)$$

$$g^{a}*g^{b} = c_1c_2n^{2} + c_1k_2n + c_2k_1n + k_1k_2$$

$$g^{a}*g^{b} \bmod n = k_1k_2$$

Both sides have the key:

$$g^{a+b} \bmod n$$

The shared secret is:

$$g^{ab} \bmod n$$

Which required knowing either a or b.


#### Random number generation
- /dev/random

#### Prime number generation (miller-rabin)

Initial test to check the primality of p

$$
a^{p-1} mod p = 1
$$

This test can sometimes generate false positives

Theorum: If

$$
x^2 mod p = 1
$$

then,

$$
x = 1,x = p-1
$$

Proof:
$$
x^2 = cp + 1
$$
Since x^2 is divisible by x, the cp + 1 should also be divisible by x

$$
(cp+1)modx = 0
$$

$$
(cp)modx + 1 = 0
$$

$$
pmodx + 1 = 0
$$

Below statement is true for all primes:

If p < x
$$
pmodx = p
$$

p>x
$$
pmodx = p-x
$$

$$
p = x-1
$$

To avoid false positives, the next test is used:

Calculate the following

$$
a^{p-1} mod p
$$

$$
a^{p-1/2} mod p
$$
etc

Let 

$$
a^{p-1}modp= x^2
$$

$$
a^{p-1/2}modp= x
$$

If 
$$
a^{p-1} mod p = 1 
$$

or,

$$
x^2 = x^2modp = 1
$$

and 
$$
a^{p-1/2} mod p = p-1
$$

or

$$
x = p-1
$$

Then it follows the theorum an p is prime

Prime number theorum:

For an n digit number, the probability of a random number being prime is:

$$
1/{log(10)*n}
$$

Sieve of eratosthenes is used to increase this probability.

#### TPM

Generate a key to be encrypted

```bash
sudo dd if=/dev/urandom of=aes_key.bin bs=32 count=1
```

List all persistent handles (Identifiers for the root keys)

```bash
shreeya@pop-os /e/nginx> sudo tpm2_getcap handles-persistent
- 0x81000001
- 0x81000002
- 0x81010001
- 0x81800000
- 0x81800001
```

Encrypt the key generated earlier using the 0x81000001 handler's public key. The public and private parts of the encrypted key are returned
```bash
 sudo tpm2_create -C 0x81000001 \
                  -u sealed.pub \
                  -r sealed.priv \
                  -i aes_key.bin
```
To ensure that the key can be decrypted only if the PCR(Platform Configuration Register) State is the same:

PCR Info:

- PCR0: BIOS/firmware
- PCR7: Secure Boot state
- PCR8–PCR14: platform-specific components
- PCR15: OS loader

Read the current hash value of PCR 0 and 7:

```bash
shreeya@pop-os /e/nginx [1]> sudo tpm2_pcrread sha256:0,7 -o pcrs.bin

  sha256:
    0 : 0xFBB41E8BB4647AB8D8FEEF3FF1D16EE852100F6E7376FF3209EDB67D7CA87974
    7 : 0xC1382134C3B9307E48FA9C73BFCDE0616B996AB1A40DE53A04F72B472D3735EA
```
Create the PCR Policy

```bash
shreeya@pop-os /e/nginx [1]> sudo tpm2_createpolicy --policy-pcr --pcr-list sha256:0,7 --pcr pcrs.bin --policy pcr.policy
9b6b1334bf6916374d3c3df7359364717aeec36fc672a191b0fcc0c45aa240a2
#outputs pcr.policy
```
Encrypt the key including the policy

```bash
shreeya@pop-os /e/nginx> sudo tpm2_create -C 0x81000001 \
                                 -u sealed.pub \
                                 -r sealed.priv \
                                 -i aes_key.bin \
                                 -L pcr.policy
name-alg:
  value: sha256
  raw: 0xb
attributes:
  value: fixedtpm|fixedparent
  raw: 0x12
type:
  value: keyedhash
  raw: 0x8
algorithm: 
  value: null
  raw: 0x10
keyedhash: 5b17fd6f63b7a73c37a8f5181421041186edd956782f96dff31a7dcc67583caf
authorization policy: 9b6b1334bf6916374d3c3df7359364717aeec36fc672a191b0fcc0c45aa240a2
```


Key decryption

```bash
# Start policy session
sudo tpm2_startauthsession --policy-session -S session.ctx

# Apply PCR policy
sudo tpm2_policypcr -S session.ctx -l sha256:0,7

# Unseal
sudo tpm2_unseal -c sealed.ctx -p session:session.ctx -o aes_key1.bin
```
Verification

```bash
shreeya@pop-os /e/nginx> sudo cat aes_key1.bin | base64
PR/pLKWGzP7slIq+SHp4h91JtxPXntjpxNbSq6kbvTw=
shreeya@pop-os /e/nginx> sudo cat aes_key.bin | base64
PR/pLKWGzP7slIq+SHp4h91JtxPXntjpxNbSq6kbvTw=
```

#### Elliptic curves (Elliptic Curve Diffie-Hellman)

Curve: 

$$
y^2 = x^3 + 7
$$

For 2 points P and Q, a line passing though them intersects the curve at -(P+Q)

Consider a point G on the curve

Consider A:

$$
A_{public} =  A_{private}G
$$

Consider B:

$$
B_{public} =  B_{private}G
$$

It’s computationally infeasible to find $A_{private}$ and $B_{private}$

Shared key:

$$
B_{private}*A_{public} = B_{private}*A_{private}G = A_{private}*(B_{private}G) = A_{private}*B_{public}
$$

Thus, A encrypts using

$$
A_{private}*B_{public}
$$

B decrypts using
$$
B_{private}*A_{public}
$$


