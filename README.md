# landing

SiiWay Domains Landing Page (?)

Project used: https://github.com/donlon/cloudflare-error-page

## Preview

[landing.siiway.top](https://landing.siiway.top)

just create a CNAME record points to it.

> remember to enable `proxied` switch in cf dash, or `reverse proxy` / `CDN`.

## Deploy

```bash
# Setup
git clone https://github.com/siiway/landing.git
cd landing
cp config.example.yaml config.yaml
uv sync
# Run
uv run main.py
```

<!--
## Usage

You can run the Worker defined by your new project by executing `wrangler dev` in this
directory. This will start up an HTTP server and will allow you to iterate on your
Worker without having to restart `wrangler`.

### Types and autocomplete

This project also includes a pyproject.toml with some requirements which
set up autocomplete and type hints for this Python Workers project.

To get these installed you'll need `uv`, which you can install by following
https://docs.astral.sh/uv/getting-started/installation/.

Once `uv` is installed, you can run the following:

```
uv venv
uv sync
```

Then point your editor's Python plugin at the `.venv` directory. You should then have working
autocomplete and type information in your editor.
-->