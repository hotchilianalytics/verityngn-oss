#!/usr/bin/env python3
"""
Check if secrets are properly configured for Streamlit deployment.

Usage:
    python scripts/check_secrets.py
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.secrets_loader import load_secrets, verify_credentials, print_credential_status


def main():
    print("\n" + "=" * 70)
    print("🔍 VERITYNGN SECRETS CONFIGURATION CHECK")
    print("=" * 70 + "\n")

    # Try to load secrets
    print("Step 1: Loading secrets...")
    loaded = load_secrets()

    if not loaded:
        print("\n❌ WARNING: No secrets were loaded!")
        print("   Please check your configuration.\n")

    print("\nStep 2: Verifying credentials...")
    all_ok = print_credential_status()

    if all_ok:
        print("✅ All credentials are configured!")
        print("\n🚀 You're ready to deploy!\n")
        print("Next steps:")
        print("  • Local:  streamlit run ui/streamlit_app.py")
        print("  • Docker: docker-compose -f docker-compose.streamlit.yml up")
        print("  • Cloud:  Push to GitHub and deploy on share.streamlit.io\n")
        return 0
    else:
        print("\n❌ Some credentials are missing.\n")
        print("📝 Setup Instructions:\n")
        print("For local development:")
        print("  1. Copy: cp .streamlit/secrets.toml.example .streamlit/secrets.toml")
        print("  2. Edit: nano .streamlit/secrets.toml")
        print("  3. Fill in your credentials")
        print("  4. Run this check again\n")
        print("For Streamlit Cloud:")
        print("  1. Deploy your app on share.streamlit.io")
        print("  2. Go to app settings → Secrets")
        print("  3. Paste contents from .streamlit/secrets.toml.example")
        print("  4. Update with your actual credentials\n")
        print("See STREAMLIT_QUICKSTART.md for detailed instructions.\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())

















