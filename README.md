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
