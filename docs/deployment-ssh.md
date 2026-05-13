# SSH Deployment to cPanel

This repository ships with two deployment workflows:

- `.github/workflows/deploy-cpanel.yml` — legacy FTP/FTPS deployment (kept for fallback)
- `.github/workflows/deploy-ssh.yml` — **preferred** SSH/rsync deployment

SSH is preferred over FTP for these reasons:

- Key-based authentication (no password to leak or rotate)
- Encrypted by default and host-key pinned
- `rsync` only transfers changed files, with explicit deletes
- Easier auditing (cPanel logs SSH sessions)

The FTP workflow is left in place so a deploy is still possible if SSH access is
ever revoked or the key is lost. If you want only one path to production, disable
the FTP workflow in the GitHub Actions UI (or delete the file).

---

## One-time setup

### 1. Generate a deploy SSH key

Generate a **dedicated** keypair for GitHub Actions on your local machine. Do
not reuse a personal key.

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy@hideaway2200" -f ~/.ssh/hideaway_deploy
```

This produces:

- `~/.ssh/hideaway_deploy` — private key (goes into GitHub secrets)
- `~/.ssh/hideaway_deploy.pub` — public key (goes onto the cPanel server)

### 2. Authorize the public key in cPanel

1. Log in to cPanel.
2. Open **SSH Access** → **Manage SSH Keys**.
3. **Import Key** and paste the **public** key (`~/.ssh/hideaway_deploy.pub`).
4. Click **Manage** next to the imported key and choose **Authorize**.

Make sure SSH is enabled on your cPanel plan. On Namecheap shared hosting you may
need to open a support ticket the first time to enable SSH.

### 3. Find your SSH connection details

In cPanel, **SSH Access** shows:

- Hostname (often the same as your domain, sometimes `server123.web-hosting.com`)
- SSH port (Namecheap shared hosting commonly uses **21098**, not 22)
- SSH username (your cPanel account name, e.g. `youruser`)

### 4. Capture the host's known_hosts entry (recommended)

Pinning the host key prevents man-in-the-middle attacks. From your local machine:

```bash
ssh-keyscan -p 21098 -H your.cpanel.host >> /tmp/known_hosts_pinned
cat /tmp/known_hosts_pinned
```

Copy the resulting line(s) — that's the value of `CPANEL_KNOWN_HOSTS`.

If you skip this, the workflow falls back to running `ssh-keyscan` itself, which
trusts whatever key the server presents on first contact. Acceptable for an
initial deploy; pin it afterwards.

### 5. Add GitHub Actions secrets

Repository **Settings → Secrets and variables → Actions → New repository secret**:

| Secret name           | Required | Example                                | Notes                                                     |
| --------------------- | -------- | -------------------------------------- | --------------------------------------------------------- |
| `CPANEL_HOST`         | yes      | `hideaway2200.com`                     | Hostname or IP for SSH                                    |
| `CPANEL_USER`         | yes      | `hideaway`                             | cPanel account username                                   |
| `CPANEL_SSH_KEY`      | yes      | contents of `~/.ssh/hideaway_deploy`   | Full private key, including BEGIN/END lines               |
| `CPANEL_PORT`         | no       | `21098`                                | Defaults to `22` if omitted                               |
| `CPANEL_TARGET_DIR`   | yes      | `/home/hideaway/public_html`           | Absolute path on the server                               |
| `CPANEL_KNOWN_HOSTS`  | no       | output of `ssh-keyscan -p 21098 -H …`  | Strongly recommended; omit only for first run             |

> Paste the private key **exactly** as the file contains it. Don't strip newlines.

### 6. Test with workflow_dispatch

1. GitHub → **Actions** → **Deploy to cPanel via SSH** → **Run workflow** → `main`.
2. Watch the run. The "Validate required secrets" step will fail fast if anything
   is missing.
3. After a successful run, refresh the live site.

Once the manual run succeeds, every push to `main` will deploy automatically.

---

## What gets uploaded

`rsync` copies the working tree to `CPANEL_TARGET_DIR/` with `--delete`, so the
remote directory mirrors the repo exactly. The following are excluded:

- `.git/`, `.github/`, `.gitignore`, `.gitattributes`
- `node_modules/`
- `README.md`, `SEO-CHECKLIST.md`, `docs/`
- `cloudflare-worker.js` (server/edge-only, not part of the public site)
- `package.json`, `package-lock.json` (build metadata)
- `.env`, `.env.*`, `*.local`

If you add files that should be excluded (e.g. private notes), update the
`--exclude` list in `.github/workflows/deploy-ssh.yml`.

> `--delete` means files removed from the repo are also removed from the server.
> If you keep files on the server that are **not** in the repo (e.g. `cgi-bin`,
> `.htaccess` managed by cPanel), move them outside `CPANEL_TARGET_DIR` or add
> matching `--exclude` rules.

---

## Optional build step

If a `package.json` is added later, the workflow will automatically run
`npm ci` (or `npm install`) and then `npm run build` if a `build` script
exists. No build runs for the current static site.

---

## Security notes

- Use a **deploy-only** SSH key, never your personal key.
- Do not commit secrets, keys, or `.env` files. `.git/` is excluded from the
  rsync, but the safest rule is "if it's secret, it's not in the repo."
- Protect `main` with a branch protection rule (require PRs, require status
  checks) so deploys only happen from reviewed code.
- Rotate `CPANEL_SSH_KEY` if a maintainer with access leaves the project.
- Pin `CPANEL_KNOWN_HOSTS` after the first successful deploy.

---

## Troubleshooting

**`Permission denied (publickey)`**
The public key isn't authorized in cPanel, or `CPANEL_USER` is wrong. In cPanel
go to **Manage SSH Keys** and confirm the key shows **authorized**.

**`Host key verification failed`**
`CPANEL_KNOWN_HOSTS` doesn't match what the server presents. Regenerate it with
`ssh-keyscan -p <port> -H <host>` and update the secret.

**`rsync: change_dir … failed: No such file or directory`**
`CPANEL_TARGET_DIR` doesn't exist on the server. Create it via cPanel File
Manager or SSH (`mkdir -p`).

**Connection times out on port 22**
Shared hosting often uses a non-standard port. Set `CPANEL_PORT` (Namecheap
shared hosting commonly uses `21098`).
