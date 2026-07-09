# Usage

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

## Prometheus node exporter integration

The `power-monitor` service writes its metrics to `/var/lib/node_exporter/pm.prom`
(see the `--out` flag in the systemd unit). For Prometheus to actually scrape
these, `prometheus-node-exporter` must have its **textfile collector** pointed at
`/var/lib/node_exporter`.

The playbook handles this automatically:

- Creates `/var/lib/node_exporter` (owned by the `daq`/`venv_user`) so the
  service can drop `pm.prom` there.
- Checks whether `prometheus-node-exporter.service` exists on the target. All of
  the steps below are skipped if it isn't installed — the playbook does **not**
  install node exporter for you.
- Ensures the exporter's `ARGS=` line in `/etc/default/prometheus-node-exporter`
  contains `--collector.textfile.directory=/var/lib/node_exporter`. This is done
  idempotently:
  - If that exact flag is already present, nothing changes.
  - If an `ARGS=` line exists, the flag is appended to it (existing args are
    preserved).
  - If there is no `ARGS=` line (or no file), the line is created.
- Restarts `prometheus-node-exporter` only when the `ARGS=` line was actually
  modified.

So after a run the exporter is started with (at least):

```
ARGS=--collector.textfile.directory=/var/lib/node_exporter
```

If you already manage node exporter's `ARGS` elsewhere (e.g. another config
management tool), note that the playbook edits `/etc/default/prometheus-node-exporter`
in place; the two must not fight over that file.

Things the playbook needs on the target

- sudo — the playbook is become: true and installs apt packages. If the ansible user on the RPi doesn't have passwordless sudo, use -K (become password) as shown.
- A daq user on the RPi — it clones/installs/runs the service as v user exists (or override venv_user=...).
- daq's SSH deploy key — the repo is cloned over SSH ( git@github.com:NCAR/dsm-i2c-sensors.git ) as the daq user on the target, so daq needs a GitHub-authorized key. Or override on the CLI: -e git_repo_url_for_i2c_sensors=https://github.com/NCAR/dsm-i2c-sensors.git if/when it's public.
