- Module: A single functionality, example `ansible.builtin.ping`
- Collection: A collection of modules, example `ansible.builtin`
- List all installed modules: `ansible-galaxy collection list`

### Inventory files

- Defining children in hosts

```yml
[A]
serverA

[B]
serverB

[C:children]
A
B
```

- To view the inventory graph

```bash
ansible-inventory -i <inventory_file> --graph
```

### Ansible CLI command

- `ansible` is a cli tool to run ad-hoc commands

```bash
ansible servers -i /root/hosts -m shell -a 'uptime'

#Equivalent to 

- hosts: servers
  tasks:
    - name: Show uptime
      ansible.builtin.shell: uptime
```

### Templating

- Templating is used to render a file by filling in all the variables and copy the file to remote servers, 
- Jinja templating is used. .j2 files are copied from control node to servers and the `{{ variable }}` is expanded according to the variable defined in the play


### Fact Gathering

- Ansible gathers host specific facts
- Disable this if no decisions are made in the play based on a host configuration such as RAM, hostname etc

### Variables

#### CLI variables

```bash
-e "env=prod region=us-east-1"
```

#### Inline variables:

- If this variable is defined in a play, it is only scoped for that play
- If this variable is defined in a task, it is only scoped for that task

```yml
- hosts: web
  vars:
    app_name: myapp
    app_port: 8080
```

#### Load variables for a file:

- vars_files is only valid at a play level
- All the variables are scoped to the play defining it

```yml
- hosts: web
  vars_files:
    - vars/common.yml
    - vars/{{ env }}.yml
```

#### include_vars

- Since `vars_files` cannot work inside a task, `include_vars` can be used to include variables from a file inside a task.
- Once defined, these variables can be accessed from the subsequent tasks in the play

```yml
- name: Load application variables
  ansible.builtin.include_vars:
    file: vars/app.yml
```

#### host_vars

- Inline variables defined in the inventory file specific to a particular remote server

#### group_vars

- For a host group `A` defined at: `inventory/prod/hosts.yml`, it's host specific variables can be defined at `inventory/prod/group_vars/A.yml`
- Common variables required for all the hosts can be defined using all.yml: `inventory/prod/group_vars/all.yml`
- Scoped across the entire playbook executed for an inventory


#### `set_fact`

- `vars`, `vars_files` etc and all the above variable types are static and resolved before a play is executed.
- For dynamic values, `set_facts` is used, it's executed as a task and thus the values are computed at runtime

```yml
- set_fact:
    app_port: "{{ previous_play_output*2 }}"
```

#### Precedence

```bash
group_vars < vars < -e
```

### Tasks

Task level parameters: Task name and the Ansible module to be executed

#### import_tasks

- Statically import a task from another file

```yml
- import_tasks: setup.yml
```

#### include_tasks

- Dynamically import a task from another file and execute it
- The task executed under the include_tasks/import_tasks directive inherit all variables in scope at the point where it is included.

```yml
- hosts: web
  tasks:
    - name: Install web server tasks
      include_tasks: install_nginx.yml
      when: ansible_hostname == "abc"
```

### Roles

- Role skeleton directory can be created using

```bash
ansible-galaxy init <role-name>
```

```
roles/nginx/
├── defaults/main.yml
├── vars/main.yml
├── tasks/main.yml
├── templates/
```

- Role files can only contain task lists, not plays
- When a role is imported, the tasks.main.yml tasks are executed. Variable files which are imported: defaults/main.yml and vars/main.yml

#### roles

Statically import and execute a role at a play level

```yaml
- hosts: web
  roles:
    - nginx
```

#### import_role

Statically import and execute a role at a task level

```yml
- name: Play
  tasks: 
	- name: Install nginx
	  import_role:
		  name: nginx
```

#### include_role

Dynamically import and execute a role at a task level

```yml
- name: Conditionally run nginx role
  include_role:
    name: nginx
  when: install_nginx
```

### Password management

- Provide the password required to SSH into the remote server
```bash
--ask-pass
```

- Provide the password required to become a different user 
```bash
--ask-become-pass
```

### Optimizations

#### Plugins

Enable plugins in ansible.cfg to profile the tasks

```ini
[defaults]
callbacks_enabled = timer, profile_tasks, profile_roles
```

#### Disable fact gathering if not required

#### forks

Define fork value in ansible.cfg to decide the number of hosts the play can be executed on simultaneously.

```ini
[defaults]
forks = 20
```

#### SSH optimizations (Multiplexing)

- Instead of creating a new SSH connection every time, check if an existing connection exists, if yes, use that.
- Stream IDs similar to HTTP 2 are used to distinguish between different SSH sessions 

```bash
# ControlMaster: If a master exists, use it, otherwise create a new conenction and become the master

ssh -vvv -o ControlMaster=auto \
        -o ControlPersist=60s \
        -o ControlPath=/tmp/ssh-%r@%h:%p \
        demo@test.rebex.net

debug1: auto-mux: Trying existing master at '/tmp/ssh-demo@test.rebex.net:22'
```

#### SSH optimizations (Pipelining)

- Instead of copying the generated python module over SSH and then send a command to execute it, SSH pipelining is used:

```bash
cat test.py | ssh demo@test.rebex.net 'python'
```
