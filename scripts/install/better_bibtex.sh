
#!/bin/zsh

# Define URLs and paths
PACKAGE_JSON_URL="https://raw.githubusercontent.com/retorquere/zotero-better-bibtex/refs/heads/master/package.json"
ZOTERO_DIR="$HOME/Library/Application Support/Zotero/Profiles"
PROFILE_DIR=$(find "$ZOTERO_DIR" -maxdepth 1 -type d -name "*.default" 2>/dev/null | head -n 1)

if [[ -z "$PROFILE_DIR" ]]; then
    echo "Error: Could not find Zotero profile directory"
    exit 1
fi

# Create extensions directory if it doesn't exist
EXTENSIONS_DIR="$PROFILE_DIR/extensions"
mkdir -p "$EXTENSIONS_DIR"

# Get the package.json content
PACKAGE_JSON=$(curl -s $PACKAGE_JSON_URL)

# Extract version and email domain
VERSION=$(echo "$PACKAGE_JSON" | grep -o '"version": "[^"]*"' | cut -d'"' -f4)
EMAIL_DOMAIN=$(echo "$PACKAGE_JSON" | grep -o '"email": "[^"]*"' | cut -d'"' -f4 | cut -d'@' -f2)

# Construct extension ID and URL
EXTENSION_ID="better-bibtex@$EMAIL_DOMAIN"
BETTER_BIBTEX_URL="https://github.com/retorquere/zotero-better-bibtex/releases/download/v${VERSION}/zotero-better-bibtex-${VERSION}.xpi"

echo "Downloading and installing Better BibTeX version ${VERSION}..."
curl -L -o "$EXTENSIONS_DIR/$EXTENSION_ID.xpi" $BETTER_BIBTEX_URL

echo "Installation complete. Please restart Zotero for the changes to take effect."
