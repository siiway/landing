# landing

SiiWay Domains Landing Page (?)

Used project: https://github.com/donlon/cloudflare-error-page

## Preview

<landing.siiway.top>

just create a CNAME record points to it.

## Deploy

```bash
# Setup
git clone https://github.com/siiway/landing.git
cd landing
cp config.example.yaml config.yaml
# rm uv.lock - maybe needed if the machine is in EU
uv sync
# Run
uv run main.py
```
