## TLS 1.2 vs TLS 1.3

View the handshake data with `tls.handshake`

## TLS 1.2
```bash
curl --tls-max 1.2 --tlsv1.2 https://example.com
sudo tcpdump -i any -s 0 -w tls_handshake.pcap port 443
```

```
Client                                Server
  |                                     |
  |-------- ClientHello --------------->|  (supported cihers ersion)
  |<------- ServerHello ----------------|  (chosen cipher, ertificate)
  |<------- Certificate ----------------|
  |-------- Keyxchange --------->|  (key material)
  |-------- ChangeCipherSpec ---------->|
  |-------- Finished ------------------>|
  |<------- ChangeCipherSpec -----------|
  |<------- Finished -------------------|
  |                                     |
  |======== Application Data ========== |  ← 2 RTT before this
```

#### RTTT:1 ClientHello

- Supported ciphers: All the ciphers supported by the client (Example, `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`)
- Client Random
- Extension: Server name name=example.com (SNI)
- Extension: application_layer_protocol_negotiation
- Extension: supported_groups: The elliptical curves supported by the clients (For ECDHA)
- Extension: signature_algorithms: The signature algorithms supported by the client
- Session ID: If the client and server have the sesion ID within TTL, then both sides reuse previous master secret to derive fresh symmetric keys.


#### RTT1: ServerHello

- Cipher Suite: The Cipher suite decided by  the server.
- Server Random
- Session ID: Can be same or different
- Certificate
- Server key exchange: Sent if algorithms like diffie helman are used which require key sharing
	- curve name
	- Public key: $g^amod(n)$ for DHE and $a.G$ for ECDHE
	- Signature. (server random, client random, dh params) are hashed and signed using the server private key. The client verifies the signature. The dh params are g,n. These params are signed as an authentication that the server sent these params for this session(session random values)
- Server hello done
- For cipher `TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256`: RSA is used for signature verification using the server public key in the certificate. ECDHE is used for PreMasterSecret and AES encryption is used for encrypting all the data. The AES encryption uses the MasterSecret.
- The random values are temporary and not stored anywhere, thus, even if the server private keys are leaked, the `MasterSecret` can be never be computed, and the packets cannot  be decypted. This is forward secrecy

#### RTT2
- Client sends ECDHE public key
- After this, both the client and the server can calculate the Master secret key:
```
`MasterSecret = PRF(PreMasterSecret, ClientRandom || ServerRandom)`
```
- Sets Change cipher spec to 1, which means the shared secret will be used to communicate from now on.
- Encrypted handshake message is sent
- Server also sets Change cipher spec to 1 and sends encrypted handshake message

TLS records have a header like:
```
ContentType | Version | Length
```
`ChangeCipherSpec` is identified by:
```
ContentType = 20
```

### TLS 1.3

```
Client                                Server
  |                                     |
  |-------- ClientHello --------------->|  (key share already included)
  |<------- ServerHello ----------------|
  |<------- {Certificate} -------------|  (encrypted immediately)
  |<------- {CertificateVerify} --------|
  |<------- {Finished} -----------------|
  |                                     |
  |-------- {Finished} ---------------->|
  |======== Application Data ========== |  ← 1 RTT before this
```

#### ClientHello

- ClientRandom
- SessionID
- Supported cipher suites
- server_name: SNI
- supported_groups
- alpn
- signature_algorithm
- key_share: The ellipctical curve and public key value. The client sends its key share speculatively in the first message. The server can derive the session key immediately and start encrypting its response — certificate and all — without waiting for a second round trip.

#### ServerHello

- ServerRandom
- SessioID
- Selected Cipher Suite
- Keyshare
- ChangeCipherSpec
- TLS Encrypted data: The server computes the MasterKey and encrypts the certificate

### 0 RTT

- A previous session shared secret can be used by the client to start encryption from the 1st message onwards.

### Differences

- TLS 1.3 supports forward secrecy (if the private keys are compromised, then any past records cannot be decrypted) by removing all ciphers which do not support ephemeral keys.
- The certificates are also encrypted in TLS 1.3


### KTLS

Perform TLS handshake, encryption, decryption in the kernel space

- TLS_SW: CPU handles the cryptography
- TLS_HW: IC handles crypto on a packet by packet basis,

Check the mode being used:

```bash
cat /proc/net/tls_stat

TlsCurrTxSw              10
TlsCurrRxSw               5
TlsCurrTxDevice           2
TlsCurrRxDevice           0
```
