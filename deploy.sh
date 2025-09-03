#!/bin/sh
# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
REMOTE_USER="eugene"
REMOTE_HOST="merlion"
REMOTE_PROJECT_DIR="~/iebot" # Main directory for the project on the remote server
SERVICE_NAME="iebot"
LOCAL_ENV_FILE=".env.merlion" # Local .env file to be copied and modified on remote

# Systemd service configuration
#SYSTEMD_PORT="0" # Port the service will listen on, as per systemd config

# --- Helper Functions ---
run_remote() {
    ssh "${REMOTE_USER}@${REMOTE_HOST}" "$@"
}

# --- Deployment Steps ---

echo ">>> Stopping and disabling existing service: ${SERVICE_NAME}..."
run_remote "systemctl --user stop ${SERVICE_NAME} || true"
run_remote "systemctl --user disable ${SERVICE_NAME} || true"

echo ">>> Cleaning up remote project sub-directories (keeping main project dir)..."
run_remote "mkdir -p ${REMOTE_PROJECT_DIR}" # Ensure base directory exists
run_remote "rm -rf ${REMOTE_PROJECT_DIR}/.git"

echo ">>> Transferring project files (including .git and ${LOCAL_ENV_FILE})..."
tar --no-xattrs -czf - .git "${LOCAL_ENV_FILE}" | run_remote "tar -xzf - -C ${REMOTE_PROJECT_DIR}/"

exit

echo ">>> Setting up git repository on remote in ${REMOTE_PROJECT_DIR}..."
run_remote "cd ${REMOTE_PROJECT_DIR} && git reset --hard && git clean -f -d"
run_remote "cd ${REMOTE_PROJECT_DIR} && mv ${LOCAL_ENV_FILE} .env"

echo ">>> Installing dependencies on remote..."
run_remote "python -m pip install requirements.txt"

echo ">>> Creating/Updating systemd service file: ${SERVICE_NAME}.service..."
# Note: The PATH in Environment might need adjustment if nvm/node paths change on remote.
# Using %h for home directory in WorkingDirectory.
SYSTEMD_SERVICE_CONTENT=$(cat <<EOF
[Unit]
Description=${SERVICE_NAME} server
After=network.target

[Service]
Type=simple
Environment=PATH=/usr/local/bin:/usr/bin:/bin
WorkingDirectory=%h/${REMOTE_PROJECT_DIR#\~/}
ExecStartPre=/bin/sleep 5
ExecStart=/bin/bash -c "python bot.py"

Restart=on-failure
RestartSec=7

[Install]
WantedBy=default.target
EOF
)

run_remote "mkdir -p ~/.config/systemd/user/ && cat <<'EOT_REMOTE' > ~/.config/systemd/user/${SERVICE_NAME}.service
${SYSTEMD_SERVICE_CONTENT}
EOT_REMOTE"

echo ">>> Reloading systemd daemon, starting and enabling service: ${SERVICE_NAME}..."
run_remote "systemctl --user daemon-reload"
run_remote "systemctl --user start ${SERVICE_NAME}"
run_remote "systemctl --user enable ${SERVICE_NAME}"

echo ">>> Deployment finished for ${SERVICE_NAME}."
echo ">>> Service should be accessible, check logs with: ssh ${REMOTE_USER}@${REMOTE_HOST} 'journalctl --user -u ${SERVICE_NAME} -f'"
