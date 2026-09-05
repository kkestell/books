# Books

A Ruby on Rails application served privately at `https://books.kestell.org`.
The name has no public DNS record and the server accepts nothing from the
public internet, so the site answers only from the LAN or over Tailscale.

## Workflow

Commit and deploy often.

## Where it runs

The application is a Docker Compose project at `/opt/books` on the `books` VM
(Proxmox VM 112, `10.0.0.12`). The container is built from this repository's
Dockerfile, from a Git checkout at `/opt/books/source`, and tagged with the
full commit. The pushed commit is built; the working tree is never uploaded
and nothing is pulled from a registry.

Container
: Serves port 80 through Thruster, published as `10.0.0.12:3000`.

Address
: dnsmasq at `10.0.0.10` resolves the name to Caddy, which terminates TLS and
proxies `books.kestell.org` straight to `10.0.0.12:3000`. The application sees
the real client address and `https` scheme through `X-Forwarded-For` and
`X-Forwarded-Proto`.

Health check
: `GET /up`, expecting 200 from host `localhost`.

Secrets
: `RAILS_MASTER_KEY` alone, supplied by the mode-0600 `/opt/books/.env` and
holding the contents of `config/master.key`. That file is both git-ignored and
docker-ignored, so the key exists in neither the repository nor the image.

## Releasing a new version

Commit and push the release first. On the VM (`ssh books`), check out the
exact committed revision, start `books-database-backup.service` as a
rollback point, build a commit-tagged image, smoke-test it on loopback with
disposable databases, update the `image:` tag in `/opt/books/compose.yaml`
and its source copy in `~/src/proxmox/tools/books/compose.yaml`, recreate the
service, and verify `/up`.

The authoritative procedure, including rollback and restore, is
`~/src/proxmox/docs/deploying-applications.md`.

## Environment variables

Runtime configuration does not live in the repository. Keep every variable
runtime-only: nothing here needs a value during the build — assets precompile
under `SECRET_KEY_BASE_DUMMY=1`. The Dockerfile's `# check=error=true` turns
BuildKit's warning about secrets in `ARG` or `ENV` into an error that fails
the build.

## Persistent storage

The container has two mounts:

`/rails/storage`
: A bind mount of `/opt/books/storage` on the VM's local disk. It holds the
SQLite databases, which must never sit on a network mount.
`bin/docker-entrypoint` runs `bin/rails db:prepare` at start, so a fresh
volume is initialized automatically and an existing one survives deployments
and restarts.

`/rails/blobs`
: A bind mount of the VM directory `/mnt/nas/books`. It holds the Active
Storage blobs. Production uses the `nas` Disk service in
`config/storage.yml`, whose root is `/rails/blobs`.

`/mnt/nas/books` is the NAS's hidden `Books` Samba share — `//10.0.0.2/Books`,
backed by `/mnt/archive/apps/books` on the NAS — CIFS-mounted through the
VM's `/etc/fstab` with credentials in `/etc/cifs-books.cred`. The mount maps
files to uid and gid 1000, the container's `rails` user. The NAS replicates
the share's contents to its media pool nightly, so the blobs exist on two
physical devices.

The fstab entry is `nofail`: a NAS outage never blocks the VM's boot, but
while the share is unmounted, blob reads and writes fail. A Docker systemd
drop-in uses `RequiresMountsFor=/mnt/nas/books`, and a container sees only
the mounts that existed when it started, so after remounting
(`sudo mount /mnt/nas/books`), recreate the Compose service.

The NAS share, mount options, nightly replica, and database backups are
documented in the homelab notes at `~/src/proxmox`.

## Kamal is not used

`config/deploy.yml`, `.kamal/`, and `bin/kamal` are the files `rails new`
generates. They still name the placeholder host `192.168.0.1` and a registry
at `localhost:5555`, and nothing reads them.

## Continuous integration

`.github/workflows/ci.yml` runs Brakeman, bundler-audit, `importmap audit`,
RuboCop, the test suite, and the system tests on pushes and pull requests to
`main`. It does not deploy; releasing is the manual procedure above.

## Troubleshooting

The name does not resolve at all
: The workstation is off the LAN and off the tailnet. These names exist only
in private DNS. On macOS a stale negative answer clears with
`sudo dscacheutil -flushcache` and `sudo killall -HUP mDNSResponder`.

Host, network, backup, and restore details are documented in the homelab
notes at `~/src/proxmox`.
