# PostgreSQL Logger Timer

These units run the C `pgsql2300` logger once every minute as a system-level
systemd service, under a dedicated, unprivileged `weather` system user (member
of the `dialout` group for serial/USB access to the weather station), reading
its config from `/etc/open2300/open2300.conf`.

Build and install the logger and its shared library first (use `install-rpi`
on Raspberry Pi OS so the library lands in the right multiarch lib dir):

```bash
cd ~/src/open2300
make lib2300 pgsql2300
sudo make install-rpi      # or: sudo make install
```

Then install the service. This creates the `weather` system user if it
doesn't exist yet (and adds it to `dialout`), copies `open2300-dist.conf` to
`/etc/open2300/open2300.conf` only if that file isn't already there, installs
the unit files to `/etc/systemd/system`, and enables + starts the timer:

```bash
sudo make install-pgsql-service
```

Edit `/etc/open2300/open2300.conf` with your real station/DB settings — it is
never overwritten by a re-run of `make install-pgsql-service`.

The service is a `oneshot` unit with `RuntimeMaxSec=40`, so a hung read from
the station is killed after 40 seconds rather than blocking the next run.

Check the timer schedule and service status with plain `systemctl` (these are
system units, not user units):

```bash
systemctl list-timers --all
systemctl status pgsql2300.timer
systemctl status pgsql2300.service
journalctl -u pgsql2300.service
```

For detailed diagnostics, stop the timer and run the logger directly as the
`weather` user:

```bash
sudo systemctl disable --now pgsql2300.timer
sudo -u weather /usr/local/bin/pgsql2300 /etc/open2300/open2300.conf
```

Set `LOG_LEVEL 3` in `/etc/open2300/open2300.conf` for maximum diagnostic
output. Re-enable the timer afterwards:

```bash
sudo systemctl enable --now pgsql2300.timer
```

To remove the service (leaves the `weather` user, group membership, and
`/etc/open2300/open2300.conf` untouched):

```bash
sudo make uninstall-pgsql-service
```
