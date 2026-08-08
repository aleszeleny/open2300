# PostgreSQL Logger Timer

These units run the C `pgsql2300` logger once every minute as a user-level
systemd service. The units assume the project is located at:

```text
~/src/open2300
```

Build the logger first:

```bash
cd ~/src/open2300
make lib2300 pgsql2300
```

Install the user units:

```bash
mkdir -p ~/.config/systemd/user
cp systemd/pgsql2300.service systemd/pgsql2300.timer ~/.config/systemd/user/
systemctl --user daemon-reload
```

Enable user services to continue after logout, then enable and start the
timer:

```bash
sudo loginctl enable-linger "$USER"
systemctl --user enable --now pgsql2300.timer
```

Check the timer schedule:

```bash
systemctl --user list-timers --all
systemctl --user status pgsql2300.timer
```

The service is a `oneshot` unit. After a successful run it normally shows as
`inactive (dead)` with `status=0/SUCCESS`; the timer remains active and starts
it again on the next minute boundary.

Use `systemctl --user`, not plain `systemctl`, because these are user units:

```bash
systemctl --user status pgsql2300.service
systemctl --user show pgsql2300.service \
    -p ActiveState -p Result -p ExecMainStatus
```

On some Raspberry Pi installations, the user journal is not persistent. It is
therefore normal for this command to show no entries even when the service ran
successfully:

```bash
journalctl --user -u pgsql2300.service
```

For detailed diagnostics, stop the timer and run the logger directly:

```bash
systemctl --user disable --now pgsql2300.timer
cd ~/src/open2300
LD_LIBRARY_PATH=. ./pgsql2300 ./open2300.conf
```

Set `LOG_LEVEL 3` in `open2300.conf` for maximum diagnostic output. Re-enable
the timer afterwards:

```bash
systemctl --user enable --now pgsql2300.timer
```

To remove the timer:

```bash
systemctl --user disable --now pgsql2300.timer
rm ~/.config/systemd/user/pgsql2300.service
rm ~/.config/systemd/user/pgsql2300.timer
systemctl --user daemon-reload
```
