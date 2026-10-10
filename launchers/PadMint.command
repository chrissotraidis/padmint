#!/bin/bash
# PadMint for macOS. Double-click to start.
cd "$(dirname "$0")/app" || exit 1
# Apple's Python: it uses the system's certificates (a python.org Python needs its
# Install Certificates step first) and comes with the command line tools PadMint needs.
PYTHON=/usr/bin/python3
if "$PYTHON" -c 'import sys; sys.exit(sys.version_info < (3, 9))' 2>/dev/null; then
  "$PYTHON" -m padmint "$@"
else
  # Without Apple's command line tools, /usr/bin/python3 asks macOS to offer them itself.
  echo "PadMint needs Apple's free command line tools (they include Python and Git)."
  echo "If macOS just offered to install them, click Install and wait until it finishes."
  echo "If it didn't, type this line and press Return:  xcode-select --install"
  echo "Then double-click PadMint.command again."
fi
echo
read -r -p "Press Enter to close this window. "
