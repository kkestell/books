# Books

A Ruby on Rails application deployed on the home Coolify instance and served
privately at `https://books.kestell.org`. The name has no public DNS record and
the server accepts nothing from the public internet, so the site answers only
from the LAN or over Tailscale.

## Where it runs

Application
: The Coolify application `books`, UUID `hrpve6kc1bx2wnd7y2pnioqf`, in the
`homelab` project's `production` environment, on the Coolify VM at `10.0.0.12`.

Address
: `https://books.kestell.org`. dnsmasq at `10.0.0.10` resolves the name to Caddy,
Caddy terminates TLS and forwards plain HTTP with the original `Host` header to
Coolify's Traefik proxy, and Traefik routes by hostname to the container. The
application sees the real client address and `https` scheme through
`X-Forwarded-For` and `X-Forwarded-Proto`.

Source
: Built on the VM from `github.com/kkestell/books`, branch `main`, using this
repository's Dockerfile. Coolify clones the pushed commit; it never uploads the
working tree and never pulls from a registry.

Container
: Serves port 80 through Thruster. Coolify's **Ports exposes** is `80`, and its
domain is written as `http://books.kestell.org` — see Troubleshooting.

Health check
: `GET /up`, expecting 200 from host `localhost`, with a 5-second interval,
5-second timeout, 10 retries, and a 5-second start period.

Secrets
: `RAILS_MASTER_KEY` alone, set in Coolify as a runtime variable holding the
contents of `config/master.key`. That file is both git-ignored and
docker-ignored, so the key exists in neither the repository nor the image.

## Releasing a new version

Deployment uses the `coolify` CLI, installed from Homebrew as
`coollabsio/coolify-cli/coolify-cli`. Its default context, `homelab`, points at
`https://deploy.kestell.org` with a token that can read and deploy but not
administer. The workstation has to be on the LAN or the tailnet for any of it to
work.

Coolify builds a committed revision, so push first:

```sh
git push origin main
coolify deploy name books
```

Then watch the result:

```sh
coolify app deployments list hrpve6kc1bx2wnd7y2pnioqf
coolify app logs hrpve6kc1bx2wnd7y2pnioqf --lines 100
curl https://books.kestell.org/up
```

Coolify builds the image on the VM, waits for `/up` to answer, and only then
replaces the running container. A failed build leaves the previous version
serving traffic and shows as `failed` in the deployment history.

To go back to an earlier image:

```sh
coolify app rollback images hrpve6kc1bx2wnd7y2pnioqf
coolify app rollback run hrpve6kc1bx2wnd7y2pnioqf --commit <sha>
```

Only the last two images are kept, so rollback reaches back two deployments.

## Environment variables

Runtime configuration belongs in Coolify, not in the repository:

```sh
coolify app env list hrpve6kc1bx2wnd7y2pnioqf
coolify app env create hrpve6kc1bx2wnd7y2pnioqf --key NAME --value VALUE
```

Keep every variable runtime-only. Nothing here needs a value during the build —
assets precompile under `SECRET_KEY_BASE_DUMMY=1`. Marking a variable build-time
makes Coolify inject it into the Dockerfile as `ARG` and `ENV`, and the
Dockerfile's `# check=error=true` turns BuildKit's warning about secrets in `ARG`
or `ENV` into an error that fails the build.

## Persistent storage

The application has two Coolify storage mounts, managed with
`coolify app storage`:

`books-storage`
: A named Docker volume at `/rails/storage`, on the VM's local disk. It holds
the SQLite databases, which must never sit on a network mount.
`bin/docker-entrypoint` runs `bin/rails db:prepare` at start, so a fresh volume
is initialized automatically and an existing one survives deployments and
restarts.

`books-blobs`
: A bind mount of the VM directory `/mnt/nas/books` at `/rails/blobs`. It holds
the Active Storage blobs. Production uses the `nas` Disk service in
`config/storage.yml`, whose root is `/rails/blobs`.

`/mnt/nas/books` is the NAS's hidden `Books` Samba share — `//10.0.0.2/Books`,
backed by `/mnt/archive/apps/books` on the NAS — CIFS-mounted through the VM's
`/etc/fstab` with credentials in `/etc/cifs-books.cred`. The mount maps files to
uid and gid 1000, the container's `rails` user. The NAS replicates the share's
contents to its media pool nightly, so the blobs exist on two physical devices.

The fstab entry is `nofail`: a NAS outage never blocks the VM's boot, but while
the share is unmounted, blob reads and writes fail. A container sees only the
mounts that existed when it started, so after remounting on the VM
(`sudo mount /mnt/nas/books`), restart the application:

```sh
coolify app restart hrpve6kc1bx2wnd7y2pnioqf
```

The NAS share, mount options, and nightly replica are documented in the homelab
notes at `~/src/proxmox`.

## Kamal is not used

`config/deploy.yml`, `.kamal/`, and `bin/kamal` are the files `rails new`
generates. They still name the placeholder host `192.168.0.1` and a registry at
`localhost:5555`, and nothing reads them. Deployment goes through Coolify.

## Continuous integration

`.github/workflows/ci.yml` runs Brakeman, bundler-audit, `importmap audit`,
RuboCop, the test suite, and the system tests on pushes and pull requests to
`main`. It does not deploy; deployment is the manual `coolify deploy` above.

## Troubleshooting

404 from a name that should work
: No container claims the hostname, meaning the application is stopped or its
domain is unset. Check with `coolify app get hrpve6kc1bx2wnd7y2pnioqf`.

The name does not resolve at all
: The workstation is off the LAN and off the tailnet. These names exist only in
private DNS. On macOS a stale negative answer clears with
`sudo dscacheutil -flushcache` and `sudo killall -HUP mDNSResponder`.

Deployment never becomes healthy
: `/up` did not return 200 within the start period and retries. Read
`coolify app logs hrpve6kc1bx2wnd7y2pnioqf --lines 100`.

Redirect loop
: The Coolify domain was saved as `https://books.kestell.org`. TLS terminates at
Caddy, so the domain must stay `http://`; the `https://` form makes Traefik demand
a certificate it cannot obtain and attaches a redirect to the port-80 router.

Ports other than the site itself refused
: By design. The hypervisor firewall allows the Coolify VM only SSH and ICMP from
the LAN plus port 80 from Caddy at `10.0.0.10`.

Platform-level changes — a new private name, Caddy, dnsmasq, the firewall, the
Coolify instance itself — are documented in the homelab notes at
`~/src/proxmox`.
