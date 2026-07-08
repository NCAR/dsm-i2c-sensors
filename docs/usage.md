# Usage


2. Inventory path mismatch. The container's ANSIBLE_INVENTORY env points at /ansible/local/inventory/inventory.ini, but your actual file is /ansible/local/inventory.ini (no inventory/ subdir). So you must pass -i explicitly.

Recommended: mount the repo at runtime

From the eol-ansible-stack directory on the host:

```
cd /DATA/slavafedor/git/ISFS/eol-ansible-stack
docker-compose up -d --build   # if not already running

# start a shell with the sensors repo mounted in
docker-compose run -u ansible \
  -v /DATA/slavafedor/git/ISFS/dsm-i2c-sensors:/ansible/playbooks/
  ansible-control bash
```

Then inside the container:

```
# sanity check connectivity first
ansible -i /ansible/local/inventory.ini rpi -m ping

# run it (become needs sudo on the target; -K prompts for the sudo
ansible-playbook -i /ansible/local/inventory.ini \
  playbooks/dsm-i2c-sensors/install_i2c_pm.yml -K
```

Alternative: copy/symlink into playbooks/

If you'd rather run it the "normal" way (playbooks/ is already mou

```
cp /DATA/slavafedor/git/ISFS/dsm-i2c-sensors/install_i2c_pm.yml \
   /DATA/slavafedor/git/ISFS/eol-ansible-stack/playbooks/
# then inside the container:
ansible-playbook -i /ansible/local/inventory.ini playbooks/install_i2c_pm.yml -K
```

The runtime-mount option is cleaner since you keep editing the playbook in its own repo.

Things the playbook needs on the target

- sudo — the playbook is become: true and installs apt packages. If the ansible user on the RPi doesn't have passwordless sudo, use -K (become password) as shown.
- A daq user on the RPi — it clones/installs/runs the service as v user exists (or override venv_user=...).
- daq's SSH deploy key — the repo is cloned over SSH ( git@github.com:NCAR/dsm-i2c-sensors.git ) as the daq user on the target, so daq needs a GitHub-authorized key. Or override on the CLI: -e git_repo_url_for_i2c_sensors=https://github.com/NCAR/dsm-i2c-sensors.git if/when it's public.
