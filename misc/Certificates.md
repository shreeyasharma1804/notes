#### Certificate types:

Details

- SAN
- Subject CN
- Issuer CN (Subject and Issuer CN is same for root cert)
- Serial number (Unique ID assigned to the certificate by the CA)
- Validity
- Public Key: (Modulus and public key exponent)
- Fingerprint: Hash value of the entire certificate content
- Signature

Certificate is verified by matching the CN, SAN with the url.

Certificate hierarchy is verified by matching the decrypted value of the signature(using next certificate's public key) and the hash value of certificate details.

Edge certificates: The certificate presented by the proxy to the user
Origin certificates: The certificate presented by the proxy to the upstream server
Client certificates: The certificate presented by the user for mutualauth

**Key Generation**

Private key generation
```bash
openssl genpkey -algorithm RSA -out private.key -pkeyopt rsa_keygen_bits:2048
```
Public key extraction
```bash
openssl rsa -in private.key -pubout -out public.pem
```
Generate CSR

CSR requires the private key to establish that the private key is owned by the csr owner
```bash
shreeya@Shreeyas-MacBook-Air ~/Documents> openssl req -new -key private.key -out request.csr
You are about to be asked to enter information that will be incorporated
into your certificate request.
What you are about to enter is what is called a Distinguished Name or a DN.
There are quite a few fields but you can leave some blank
For some fields there will be a default value,
If you enter '.', the field will be left blank.
-----
Country Name (2 letter code) []:IN
State or Province Name (full name) []:TN
Locality Name (eg, city) []:HYD
Organization Name (eg, company) []:Shreeya
Organizational Unit Name (eg, section) []:Shreeya
Common Name (eg, fully qualified host name) []:shreeya.online
Email Address []:shreeyasharmma@gmail.com
```

Self signed certificate generation (pem format)

Self signed certificates do not contain inter, root certificates. Only server signed with same subject and issuer
```bash
openssl x509 -req -in request.csr -signkey private.key -out certificate.crt -days 365
```

Generate p12 file

```bash
openssl pkcs12 -export \
               -out certificate.p12 \
               -inkey private.key \
               -in certificate.crt
```

Import in java key store (p12)
```bash
keytool -importkeystore \
     -srckeystore certificate.p12 -srcstoretype PKCS12 \
     -destkeystore keystore.jks -deststoretype PKCS12
```

Add certificate to java trust store (pem)
```bash
 keytool -importcert \
         -alias myserver \
         -file certificate.crt \
         -keystore truststore.jks \
         -storepass changeit
```

#### Certificate formats

- **pem**:

Encoding: Base64
Contains: Public Key

Can be read directly from the terminal. Identified by `-----BEGIN CERTIFICATE-----`

1. **p12**:
Encoding: Binary
Contains: Public + Private Key

View the certificates in pem format:
```bash
openssl pkcs12 -info -in <file_name>
```
One file can contain only one private key with one or more certificates

Implements the pkcs standards and is an open source replacement for jks format

3. **jks**

The java keystore/ truststore

```bash
keytool -list -v -keystore <keystore file>
```
Each entry is identified by an alias, Entry type, Certificate chain, Certificate length

Keystore has entry type: PrivateKeyEntry
Truststore has entry type: trustedCertEntry


#### Check cert sent by server

```bash
openssl s_client -showcerts -connect http://google.com:443
```
