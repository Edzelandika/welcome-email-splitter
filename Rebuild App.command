#!/bin/zsh
set -eu
cd "$(dirname "$0")"
app="Welcome Email Splitter.app"
cache="$(mktemp -d "${TMPDIR:-/tmp}/welcome-build.XXXXXX")"
trap 'rm -rf "$cache"' EXIT
echo "Rebuilding Welcome Email Splitter…"
swiftc -module-cache-path "$cache" App.swift -o "$cache/WelcomeEmailSplitter"
cp split_emails.py "$app/Contents/Resources/split_emails.py"
mv "$cache/WelcomeEmailSplitter" "$app/Contents/MacOS/WelcomeEmailSplitter"
echo "Done. Quit and reopen Welcome Email Splitter to see your changes."
read "?Press Return to close."
