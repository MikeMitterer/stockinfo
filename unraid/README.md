# StockInfo on Unraid

StockInfo runs its dashboard and REST API in one container. The maintained
[container template](https://github.com/MikeMitterer/unraid-templates/blob/master/templates/stockinfo.xml)
uses `mangolila/stockinfo:latest`, port **8000** and persistent storage at
**`/mnt/user/appdata/stockinfo`**, mounted as `/data` inside the container.

[Project documentation](../README.md) · [Docker guide](../docker/README.md) ·
[Docker Hub](https://hub.docker.com/r/mangolila/stockinfo)

## Contents

- [Installing through Unraid Apps](#installing-through-unraid-apps)
- [Test installation with wget](#test-installation-with-wget)
- [Configuration](#configuration)
- [Data and source profiles](#data-and-source-profiles)
- [Updates and troubleshooting](#updates-and-troubleshooting)
- [Testing a local template](#testing-a-local-template)

## Installing through Unraid Apps

Use **Apps / Community Applications** in the Unraid web interface for a normal
installation:

1. Open **Apps** and search for **StockInfo**.
2. Select the application and click **Install**.
3. Check the host port and [appdata path](#configuration). Set your timezone
   if needed.
4. Apply the settings to install and start the container, then open its **WebUI**
   from the **Docker** tab, normally `http://YOUR_UNRAID_SERVER:8000/`.
   The API documentation is at `/docs`.

If Community Applications is not installed, follow the
[Unraid setup instructions](https://docs.unraid.net/community-applications/#installing-the-plugin).
If the application is not listed yet, the manual procedure below can be used
for testing; it is not the standard installation path.

StockInfo has no login. Anyone who can reach it can change or delete data.
Use a trusted network or an authenticated reverse proxy; do not expose the
port directly to the internet. See the [security model](../README.md#security-model).

[↑ Contents](#contents)

## Test installation with wget

To test the published template manually, download it as a **User template**.
This is an optional test installation; normal installations use **Apps**.
The image must be available to start the test container.

Run this command in the terminal on your Unraid server. It replaces any
existing `stockinfo-test.xml`. Never overwrite `my-stockinfo.xml` containing
saved container settings:

```bash
wget -O /boot/config/plugins/dockerMan/templates-user/stockinfo-test.xml \
  https://raw.githubusercontent.com/MikeMitterer/unraid-templates/master/templates/stockinfo.xml
```

1. Choose **Docker → Add Container** and select **stockinfo** under
   **User templates**.
2. Set a different container name, such as `stockinfo-test`, an unused host port
   and a **separate appdata directory**, such as `/mnt/user/appdata/stockinfo-test`.
   Two containers must not share the same SQLite database.
3. Check the other [settings](#configuration), start the test container and
   open its **WebUI** using the test port.

This downloads the published template with `TemplateURL` intact. To test local
XML changes, follow [Testing a local template](#testing-a-local-template).
Remove the test container and test template when finished.

[↑ Contents](#contents)

## Configuration

| Template field | Default | Meaning |
|---|---|---|
| WebUI Port | `8000` | Host port; the container port remains `8000` |
| Data (Cache DB) | `/mnt/user/appdata/stockinfo` | Persistent host directory, mounted at `/data` |
| Refresh interval (hours) | `6` | Background refresh interval |
| Cache TTL (hours) | `6` | Quote age that triggers a refresh on request |
| Metadata TTL (days) | `7` | ETF metadata refresh interval |
| Default exchange (MIC) | `XETR` | Preferred exchange for ISIN queries |
| Strict exchange | `false` | Require the preferred exchange during ISIN resolution |
| FX rate TTL (hours) | `1` | Exchange-rate cache lifetime |
| OpenFIGI API key | Empty | Optional key for a higher OpenFIGI rate limit |
| Timezone | `UTC` | Log timezone, for example `Europe/Vienna` |

Some optional fields appear in Unraid's advanced view. The template uses
bridge networking. Dashboard and API share the same port.

[↑ Contents](#contents)

## Data and source profiles

Keep the appdata directory when updating or replacing the container. It holds
the SQLite database, `sources.yaml` and other application data. The entrypoint
prepares `/data` ownership and runs the app as **UID 99 / GID 100**, matching
Unraid's `nobody:users`. The directory must be writable by that user.

The template uses a host directory, whereas `make up` uses a named Docker
volume. Data is not copied between them automatically.

To select the file-only source profile, run the following from a StockInfo
checkout with its [development prerequisites](../README.md#quick-start) set up,
on the server that owns the appdata directory. Stop an existing StockInfo
container first, or do this before its first start:

```bash
mkdir -p /mnt/user/appdata/stockinfo
./scripts/sources-profile.sh --yaml --target docker \
  --data-dir /mnt/user/appdata/stockinfo
```

Use the same host path as the template. This helper is part of the source
checkout, not the Unraid template. Its host-directory mode needs no running
Docker daemon. It backs up an existing `sources.yaml` and preserves existing
asset files. Use `--online` instead of `--yaml` to restore online sources with
a file fallback, then start the container. Source chains are loaded at startup.
See the [source configuration guide](../docs/plugins.md) for details.

[↑ Contents](#contents)

## Updates and troubleshooting

Use **Docker → stockinfo → Force Update** to pull the current image, keeping
the same appdata mapping. Do not download over the saved `my-stockinfo.xml`
to update an existing container. Before an update, stop the container and back up
the complete appdata directory to a separate location.

View logs through Unraid's container menu or with `docker logs --tail=100 stockinfo`.
The image checks `/operational`; `/health` checks whether the process runs,
and `/ready` reports whether normal requests are allowed. A pending database
migration may need confirmation in the dashboard.

[Report a problem](https://github.com/MikeMitterer/stockinfo/issues).

[↑ Contents](#contents)

## Testing a local template

For template development, use a separate test copy. From the directory
containing your edited `stockinfo.xml`, remove `TemplateURL` so Unraid does
not replace it with the published version. Replace `YOUR_UNRAID_SERVER` with
your server's address:

```bash
sed '/<TemplateURL>/d' stockinfo.xml > /tmp/stockinfo-test.xml
scp /tmp/stockinfo-test.xml \
  root@YOUR_UNRAID_SERVER:/boot/config/plugins/dockerMan/templates-user/stockinfo-test.xml
```

Choose **Docker → Add Container** and select the test template. Before starting
it, use a different container name, an unused host port and a **separate appdata
directory**, such as `/mnt/user/appdata/stockinfo-test`. Two containers must not
share the same SQLite database. Never overwrite an existing `my-stockinfo.xml`
with saved settings. Remove the test container and test template after testing.

A local XML or Docker check does not replace a test on an actual Unraid server.

[↑ Contents](#contents)
