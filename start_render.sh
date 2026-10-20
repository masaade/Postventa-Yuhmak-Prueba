#!/usr/bin/env bash
set -euo pipefail
: "${GOOGLE_CLIENT_ID:?Falta GOOGLE_CLIENT_ID}"
: "${GOOGLE_CLIENT_SECRET:?Falta GOOGLE_CLIENT_SECRET}"
: "${COOKIE_SECRET:?Falta COOKIE_SECRET}"
: "${PUBLIC_URL:?Falta PUBLIC_URL}"
: "${YUHMAK_DATA_DIR:?Falta YUHMAK_DATA_DIR}"
mkdir -p .streamlit "$YUHMAK_DATA_DIR"
python - <<'PYCODE'
import os,toml
url=os.environ['PUBLIC_URL'].rstrip('/')
config={'auth':{'redirect_uri':url+'/oauth2callback','cookie_secret':os.environ['COOKIE_SECRET'],'google':{'client_id':os.environ['GOOGLE_CLIENT_ID'],'client_secret':os.environ['GOOGLE_CLIENT_SECRET'],'server_metadata_url':'https://accounts.google.com/.well-known/openid-configuration'}}}
with open('.streamlit/secrets.toml','w') as f:toml.dump(config,f)
PYCODE
exec streamlit run app.py --server.address=0.0.0.0 --server.port="${PORT:-8501}" --server.headless=true --server.enableCORS=true --server.enableXsrfProtection=true
