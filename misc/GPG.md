## GPG

### Key creation and listing

Generate Keys:

```bash
gpg --gen-key
```

```bash
shreeya@Shreeyas-MacBook-Pro ~/D/C/src (main) [SIGINT]> gpg --gen-key
gpg (GnuPG) 2.4.8; Copyright (C) 2025 g10 Code GmbH
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

Note: Use "gpg --full-generate-key" for a full featured key generation dialog.

GnuPG needs to construct a user ID to identify your key.

Real name: Shreeya_Shreeya
Email address: shreeyasharmma@gmail.com
You selected this USER-ID:
    "Shreeya_Shreeya <shreeyasharmma@gmail.com>"

Change (N)ame, (E)mail, or (O)kay/(Q)uit? o
We need to generate a lot of random bytes. It is a good idea to perform
some other action (type on the keyboard, move the mouse, utilize the
disks) during the prime generation; this gives the random number
generator a better chance to gain enough entropy.
We need to generate a lot of random bytes. It is a good idea to perform
some other action (type on the keyboard, move the mouse, utilize the
disks) during the prime generation; this gives the random number
generator a better chance to gain enough entropy.
gpg: /Users/shreeya/.gnupg/trustdb.gpg: trustdb created
gpg: directory '/Users/shreeya/.gnupg/openpgp-revocs.d' created
gpg: revocation certificate stored as '/Users/shreeya/.gnupg/openpgp-revocs.d/A3A17CDEEEA82BDBD9B41A0E289C78457D249803.rev'
public and secret key created and signed.

pub   ed25519 2025-12-04 [SC] [expires: 2028-12-03]
      A3A17CDEEEA82BDBD9B41A0E289C78457D249803
uid                      Shreeya_Shreeya <shreeyasharmma@gmail.com>
sub   cv25519 2025-12-04 [E] [expires: 2028-12-03]
```
### List the keys

```bash
Print public and private keys
gpg --list-keys
gpg --list-secret-keys

# Key fingerprint and ID in long format
gpg --list-keys --fingerprint --keyid-format=long

# List key details without importing it

gpg --show-keys --keyid-format=long keyfile.asc
```

**Fingerprint**: Hash of all the public key data

**KeyID**: Uniquely identify a key

**gpg --list-keys output**:

```bash
pub   ed25519 2025-12-04 [SC] [expires: 2028-12-03]
      A3A17CDEEEA82BDBD9B41A0E289C78457D249803
uid           [ultimate] Shreeya_Shreeya <shreeyasharmma@gmail.com>
sub   cv25519 2025-12-04 [E] [expires: 2028-12-03]
```

*ed25519*: Key algorithm

2025-12-04: Creation Day

SC: Used for signing an verifying

A3A17CDEEEA82BDBD9B41A0E289C78457D249803: Key fingerprint

UID: User ID

**gpg --list-keys --fingerprint --keyid-format=long output**:

```bash
pub   ed25519/289C78457D249803 2025-12-04 [SC] [expires: 2028-12-03]
      Key fingerprint = A3A1 7CDE EEA8 2BDB D9B4  1A0E 289C 7845 7D24 9803
uid                 [ultimate] Shreeya_Shreeya <shreeyasharmma@gmail.com>
sub   cv25519/D518799335B01EC5 2025-12-04 [E] [expires: 2028-12-03]
```
289C78457D249803: KeyID

Note: Key ID is a shortened version of the fingerprint

**View the key and export it**:

```bash
# public key
gpg --export --armor [key-id]

# private key
gpg --export-secret-keys --armor [key-id]
```

*--armor*: Print the output in ascii encoding

**Importing a public key and certifying it**

```bash
# Import a public key
gpg --import <key file>
```

**List all signatures**

```bash
 gpg --list-sigs
```

```bash
shreeya@Shreeyas-MacBook-Pro ~/D/C/src (main)> gpg --list-sigs
[keyboxd]
---------
pub   ed25519 2025-12-04 [SC] [expires: 2028-12-03]
      A3A17CDEEEA82BDBD9B41A0E289C78457D249803
uid           [ultimate] Shreeya_Shreeya <shreeyasharmma@gmail.com>
sig 3        289C78457D249803 2025-12-04  [self-signature]
sub   cv25519 2025-12-04 [E] [expires: 2028-12-03]
sig          289C78457D249803 2025-12-04  [self-signature]
```

**Sign a keys**
```bash
# Check the sign on a key
shreeyasharma@Shreeyas-MacBook-Pro Downloads % gpg --check-sigs <key id: F231550C4F47E38E>
pub   ed25519 2019-01-22 [SC]
      EB85BB5FA33A75E15E944E63F231550C4F47E38E
uid           [ unknown] Alice Lovelace <alice@openpgp.example>
sig!3        F231550C4F47E38E 2019-10-15  [self-signature]
sub   cv25519 2019-01-22 [E]
sig!         F231550C4F47E38E 2019-01-22  [self-signature]
```

!: Means that the public key is in the keyring

-   Level 0: No particular verification.
-   Level 1: Verified the key owner by belief.
-   Level 2: Casual verification, e.g., checked fingerprint and photo ID.
-   Level 3: Extensive verification, e.g., checked fingerprint, verified identity with photo ID, and verified email address via correspondence
  
```bash
# Sign the key
gpg --sign-key <key id>
```

This approach by default signs the key with level 1 signature.

**Trust a key**

The value is stored in the trustdb

-   **Unknown:**  Default for any new key. You haven't decided how much you trust this person to validate others' keys.​
    
-   **Never:**  You do NOT trust this person to properly verify identities before signing keys.​
    
-   **Marginal:**  You believe the person is somewhat careful, but not careful enough to rely only on their signature.​
    
-   **Full:**  You trust this person to carefully check identity before signing; if they sign a key, you consider it valid.​
    
-   **Ultimate:**  Used only for your own keys. You trust yourself fully—GPG marks your own key as "ultimate"

```bash
shreeyasharma@Shreeyas-MacBook-Pro Downloads % gpg --edit-key FBFCC82A015E7330                  
gpg (GnuPG) 2.4.8; Copyright (C) 2025 g10 Code GmbH
This is free software: you are free to change and redistribute it.
There is NO WARRANTY, to the extent permitted by law.

pub  rsa3072/FBFCC82A015E7330
     created: 2019-10-15  expires: never       usage: SC  
     trust: never         validity: full
sub  rsa3072/7C2FAA4DF93C37B2
     created: 2019-10-15  expires: never       usage: E   
[  full  ] (1). Bob Babbage <bob@openpgp.example>

gpg> trust
pub  rsa3072/FBFCC82A015E7330
     created: 2019-10-15  expires: never       usage: SC  
     trust: never         validity: full
sub  rsa3072/7C2FAA4DF93C37B2
     created: 2019-10-15  expires: never       usage: E   
[  full  ] (1). Bob Babbage <bob@openpgp.example>

Please decide how far you trust this user to correctly verify other users' keys
(by looking at passports, checking fingerprints from different sources, etc.)

  1 = I don't know or won't say
  2 = I do NOT trust
  3 = I trust marginally
  4 = I trust fully
  5 = I trust ultimately
  m = back to the main menu

Your decision? 3

pub  rsa3072/FBFCC82A015E7330
     created: 2019-10-15  expires: never       usage: SC  
     trust: marginal      validity: full
sub  rsa3072/7C2FAA4DF93C37B2
     created: 2019-10-15  expires: never       usage: E   
[  full  ] (1). Bob Babbage <bob@openpgp.example>
Please note that the shown key validity is not necessarily correct
unless you restart the program.

gpg> quit
```

**trustdb**

To view the trust db:

```bash
gpg --export-ownertrust
```

```bash
shreeya@Shreeyas-MacBook-Pro ~/D/C/src (main)> gpg --export-ownertrust
# List of assigned trustvalues, created Thu Dec  4 11:38:17 2025 IST
# (Use "gpg --import-ownertrust" to restore them)
A3A17CDEEEA82BDBD9B41A0E289C78457D249803:6:

Format Fingerprint: Trust Level
```

-   `2` = Unknown
-   `3` = None (do NOT trust)
-   `4` = Marginal
-   `5` = Full
-   `6` = Ultimate

**Diference between signature and trust**
-   Signatures = public attestations that you verified a key (shared via keyserver)
-   Trust levels = your private decision about whether to trust someone's signatures (local only)

**Delete/revoke a key**
Revoking a key is equivalent to deleting it
```bash
gpg --output revoke.asc --gen-revoke 4873E8301E8C2A32
```
**Symmetric encryption**: Encrypt using a passphrase. Generates .asc file
```bash
gpg --armor --symmetric <file to be encrypted>
```
Encrypt using a passphrase

**Asymmetric encryption**: Encrypt for a a particular recipient. Generates .gpg file
```bash
 gpg --encrypt <file to be encrypted>
```
**Decryption**:
```bash
gpg --decrypt <encrypted_file>
```
**Encrypt and sign a file**
This command encrypts the file using recipient@example.com's public key and signs it using its own public key
```bash
 gpg --encrypt --sign --armor --recipient recipient@example.com --output <output_file> <file to be encrypted>
 ```
 The signature of the file is automatically check and printed while decrypting it using --decrypt

Signature after decyption:
```bash
gpg: encrypted with cv25519 key, ID D518799335B01EC5, created 2025-12-04
      "Shreeya_Shreeya <shreeyasharmma@gmail.com>"
import os

print(os.getcwd())
gpg: Signature made Thu Dec  4 13:47:07 2025 IST
gpg:                using EDDSA key A3A17CDEEEA82BDBD9B41A0E289C78457D249803
gpg: Good signature from "Shreeya_Shreeya <shreeyasharmma@gmail.com>" [ultimate]
```
The trust and signature can now be used to decide to read the document or not.

The signature quality (signature of the key used to sign the file and the trust value of the key which was used to sign the original key) of a decrypted file can be automated using python

**Keyservers**

- Search for a key:
```bash
gpg --keyserver keys.openpgp.org --search-keys user@example.com
```

- Import a key

```bash
gpg --keyserver keys.openpgp.org --recv-keys KEYID
```
- Upload your public key
```bash
gpg --keyserver keys.openpgp.org --send-keys YOURKEYID
```

We can also, import a key, sign and then upload it back

```bash
gpg --keyserver keyserver.ubuntu.com --recv-keys 0xA4285295FC7B1A81600062A9605C66F00D6C9793

pub   rsa4096 2021-02-13 [SC] [expires: 2029-02-11]
      A4285295FC7B1A81600062A9605C66F00D6C9793
uid           [ unknown] Debian Stable Release Key (11/bullseye) <debian-release@lists.debian.org>
sig 3        605C66F00D6C9793 2021-02-13  [self-signature]

Notice that the key has been signed by the key 605C66F00D6C9793 but the trust in [unknown] since this key is not in my trust store
```
