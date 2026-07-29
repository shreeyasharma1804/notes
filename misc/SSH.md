When you run:

ssh bob@server

the SSH server checks:

Does the user bob exist?
Is bob allowed to SSH (AllowUsers, DenyUsers, etc.)?
Does bob have a valid login shell?
Does /home/bob/.ssh/authorized_keys contain the public key matching the client's private key?
Are the file permissions and ownership correct?


If no default user is defined in ansible.cfg, inventory file, the user running the ansible becomes the ssh user
