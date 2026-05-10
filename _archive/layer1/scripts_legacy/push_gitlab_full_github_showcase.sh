#!/usr/bin/env bash
# Push full main to GitLab (origin), then force-push a minimal "showcase" tree to GitHub (github remote).
# Run from repo root: ./scripts/push_gitlab_full_github_showcase.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
cleanup() { rm -rf "$TMP"; }
trap cleanup EXIT

GITHUB_URL="$(git -C "$ROOT" remote get-url github)"

echo "==> 1/3  Push full main → GitLab (origin)"
git -C "$ROOT" push origin main

echo "==> 2/3  Build showcase tree (no SPEC, .specify, agent prompts, internal Fabric memos)"
DEST="$TMP/showcase"
mkdir -p "$DEST"

for item in README.md sla sla_all_roles.md SCREENSHOTS.md api dbt-project powerbi-model ml-pipeline data headhunter_ready screenshots outputs inputs scripts; do
  if [[ -e "$ROOT/$item" ]]; then
    cp -R "$ROOT/$item" "$DEST/"
  fi
done

mkdir -p "$DEST/fabric_april"
if [[ -f "$ROOT/fabric_april/README.md" ]]; then
  cp "$ROOT/fabric_april/README.md" "$DEST/fabric_april/"
fi
if [[ -d "$ROOT/fabric_april/outputs" ]]; then
  cp -R "$ROOT/fabric_april/outputs" "$DEST/fabric_april/"
fi

# Public README: drop internal single-source / agent / scaffold pointers
if [[ -f "$ROOT/README.md" ]]; then
  perl -0777 -pe 's/^Single source of truth:.*\n//m; s/^For agents:.*\n//m; s/^\*\*Repos:\*\*.*\n//m; s/^## Scaffold backup\n.*?\n---\n\n//ms' <"$ROOT/README.md" >"$DEST/README.md" 2>/dev/null || cp "$ROOT/README.md" "$DEST/README.md"
  {
    echo ""
    echo "---"
    echo ""
    echo '**Public mirror:** Code and proof artifacts only. Planning (SPEC), agent scaffolding (`.specify`, internal notes), and full Fabric work-in-progress live on the private GitLab repo.'
  } >>"$DEST/README.md"
fi

# Clone-friendly ignores (no secrets)
cat >"$DEST/.gitignore" <<'EOF'
.env
.env.*
*.env
**/secrets/
**/global.env
**/fabric.env
*.pem
*.key
credentials*.json
__pycache__/
*.pyc
.venv/
venv/
dbt-project/target/
dbt-project/logs/
dbt-project/dbt_packages/
dbt-project/.user.yml
ml-pipeline/src/mlruns/
.DS_Store
EOF

echo "==> 3/3  Init showcase repo & force-push → GitHub (github)"
cd "$DEST"
git init -q
git branch -M main
git add -A
git commit -q -m "Showcase mirror: API, dbt, Power BI, ML proofs (minimal public)"

git remote add github "$GITHUB_URL"
git push -q github main --force

echo "Done. GitLab = full history; GitHub = minimal showcase on main."
