"""
Unified secrets loader for Streamlit deployment.
Handles both .env files (local) and Streamlit secrets (cloud).
"""

import os
import json
import tempfile
from pathlib import Path


def _secrets_debug_enabled() -> bool:
    return os.getenv("VERITYNGN_DEBUG_SECRETS", "").strip().lower() in (
        "1",
        "true",
        "yes",
        "y",
        "on",
    )


def _override_placeholder_env_vars():
    """
    🔍 SHERLOCK MODE: Override placeholder values in environment.

    Streamlit loads .streamlit/secrets.toml into os.environ BEFORE
    our Python code runs. This function checks if environment variables
    contain placeholder values and attempts to reload them from .env.

    This fixes the issue where placeholder values from secrets.toml
    prevent real values from .env from being used.
    """
    from dotenv import dotenv_values

    if _secrets_debug_enabled():
        print("\n🔍 SHERLOCK MODE: Checking for placeholder env vars")

    placeholder_patterns = [
        "your-",
        "your_",
        "placeholder",
        "example",
        "change-me",
        "set-this",
        "TODO",
        "FIXME",
        "replace",
        "dummy",
        "test-key",
    ]

    keys_to_check = [
        "GOOGLE_SEARCH_API_KEY",
        "CSE_ID",
        "YOUTUBE_API_KEY",
    ]

    # Load .env file values directly (not via os.environ)
    env_file_locations = [
        Path(__file__).parent.parent / ".env",  # verityngn-oss/.env
        Path.cwd() / ".env",  # current working directory
    ]

    env_values = {}
    for env_file in env_file_locations:
        if env_file.exists():
            env_values = dotenv_values(env_file)
            break

    if not env_values:
        if _secrets_debug_enabled():
            print("⚠️  No .env file found to check against")
        return

    override_count = 0
    for key in keys_to_check:
        current_value = os.getenv(key, "")
        env_file_value = env_values.get(key, "")

        if current_value:
            # Check if current environment value is a placeholder
            is_placeholder = any(
                pattern in current_value.lower() for pattern in placeholder_patterns
            )

            if is_placeholder and env_file_value:
                # Override with .env file value
                if _secrets_debug_enabled():
                    print(f"🔄 Overriding placeholder {key} with .env value")
                    print(f"   Old: {current_value[:20]}...")
                    print(f"   New: {env_file_value[:15]}...{env_file_value[-5:]}")
                os.environ[key] = env_file_value
                override_count += 1

    if _secrets_debug_enabled():
        if override_count > 0:
            print(f"✅ Overrode {override_count} placeholder values with .env\n")
        else:
            print("✅ No placeholder overrides needed\n")


def _validate_loaded_secrets_sherlock():
    """
    🔍 SHERLOCK MODE: Validate loaded secrets for placeholder values.

    This diagnostic function checks if .env values are actually
    placeholders and provides clear warnings to the user.
    """
    if not _secrets_debug_enabled():
        return

    print("\n" + "=" * 80)
    print("🔍 SHERLOCK MODE: Validating loaded API keys")
    print("=" * 80)

    # Keys to check
    keys_to_check = {
        "GOOGLE_SEARCH_API_KEY": "Google Search API",
        "CSE_ID": "Custom Search Engine ID",
        "YOUTUBE_API_KEY": "YouTube Data API",
    }

    placeholder_patterns = [
        "your-",
        "your_",
        "placeholder",
        "example",
        "change-me",
        "set-this",
        "TODO",
        "FIXME",
        "replace",
        "dummy",
        "test-key",
    ]

    has_issues = False

    for env_key, label in keys_to_check.items():
        value = os.getenv(env_key, "")

        if not value:
            print(f"❌ {label} ({env_key}): MISSING (empty)")
            has_issues = True
        else:
            # Check for placeholder patterns
            is_placeholder = any(
                pattern in value.lower() for pattern in placeholder_patterns
            )

            if is_placeholder:
                # Preview the value to show it's a placeholder
                preview = value[:30] + "..." if len(value) > 30 else value
                print(f"❌ {label} ({env_key}): " "PLACEHOLDER VALUE DETECTED")
                print(f'   Current value: "{preview}"')
                print("   ⚠️  This will cause " '"API key not valid" errors!')
                has_issues = True
            else:
                # Valid key - show preview (first 15 + last 5 chars)
                if len(value) > 20:
                    preview = value[:15] + "..." + value[-5:]
                else:
                    preview = value[:8] + "..." if len(value) > 8 else value
                print(f"✅ {label} ({env_key}): Valid")
                print(f"   Preview: {preview}")

    print("=" * 80)

    if has_issues:
        print("\n🚨 CRITICAL: API KEY ISSUES DETECTED\n")
        print("Your .env file contains PLACEHOLDER or MISSING values!")
        print('This is why you\'re seeing "API key not valid" errors.\n')
        print("📋 ACTION REQUIRED:")
        print("   1. Open: /path/to/verityngn-oss/.env")
        print("   2. Replace placeholder values with your REAL API keys")
        api_url = "https://console.cloud.google.com/apis/credentials"
        print(f"   3. Get API keys from: {api_url}")
        print("   4. Restart Streamlit app\n")
        print("Example:")
        print('   GOOGLE_SEARCH_API_KEY="AIzaSyA..."  ' "# Real key, starts with AIza")
        print('   CSE_ID="0123456789abcdef..."         ' "# Real CSE ID")
        print(
            '   YOUTUBE_API_KEY="AIzaSyA..."         '
            "# Same as search key or separate\n"
        )
        print("=" * 80 + "\n")
    else:
        print("✅ All API keys look valid!\n")


def load_secrets():
    """
    Load secrets from either .env or Streamlit secrets.

    Priority (CRITICAL FIX):
    1. Load .env file FIRST (local development)
    2. Then load Streamlit secrets (but don't override .env values)
    3. Skip placeholder values in Streamlit secrets
    4. VALIDATE loaded values from .env for placeholders

    Returns:
        bool: True if secrets were loaded successfully
    """
    loaded_from = None

    # STEP 1: Load .env file FIRST (local development takes precedence)
    env_loaded = False
    try:
        from dotenv import load_dotenv

        # Try to find .env file
        possible_locations = [
            Path(__file__).parent.parent / ".env",  # verityngn-oss/.env
            Path.cwd() / ".env",  # current working directory
        ]

        for env_file in possible_locations:
            if env_file.exists():
                if _secrets_debug_enabled():
                    print(f"🔐 Loading secrets from .env file: {env_file}")
                # Don't override existing vars
                load_dotenv(env_file, override=False)
                if _secrets_debug_enabled():
                    print(f"✅ Loaded secrets from {env_file}")
                loaded_from = f".env ({env_file})"
                env_loaded = True
                break

        if not env_loaded and _secrets_debug_enabled():
            print("⚠️  No .env file found")

    except ImportError:
        if _secrets_debug_enabled():
            print("⚠️  python-dotenv not installed, cannot load .env files")
    except Exception as e:
        if _secrets_debug_enabled():
            print(f"⚠️  Could not load .env file: {e}")

    # STEP 1.5: CRITICAL FIX - Override placeholder values in environment
    # Streamlit loads .streamlit/secrets.toml into os.environ BEFORE
    # our code runs. Check if environment has placeholders and override.
    if env_loaded:
        _override_placeholder_env_vars()

    # 🔍 SHERLOCK MODE: Validate loaded .env values for placeholders
    if env_loaded:
        _validate_loaded_secrets_sherlock()

    # STEP 2: Try Streamlit secrets (Cloud deployment)
    # But DON'T override existing .env values, and skip placeholders
    try:
        import streamlit as st

        if hasattr(st, "secrets") and len(st.secrets) > 0:
            if _secrets_debug_enabled():
                print("🔐 Checking Streamlit Cloud secrets...")

            # Load GCP service account JSON (only if not already set)
            if "gcp_service_account" in st.secrets and not os.getenv(
                "GOOGLE_APPLICATION_CREDENTIALS"
            ):
                try:
                    # Create temporary file with service account JSON
                    with tempfile.NamedTemporaryFile(
                        mode="w",
                        suffix=".json",
                        delete=False,
                        dir=tempfile.gettempdir(),
                    ) as f:
                        json.dump(dict(st.secrets["gcp_service_account"]), f)
                        temp_path = f.name

                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = temp_path
                    if _secrets_debug_enabled():
                        print(f"✅ Service account loaded to: {temp_path}")
                except Exception as e:
                    if _secrets_debug_enabled():
                        print(f"⚠️  Warning: Could not load service account: {e}")

            # Load other environment variables from Streamlit secrets
            # CRITICAL: Only set if not already in environment (from .env)
            secret_count = 0
            for key in st.secrets:
                if key != "gcp_service_account":
                    # Handle both string values and nested sections
                    value = st.secrets[key]
                    if isinstance(value, str):
                        # Skip if already set (from .env)
                        if key in os.environ and os.environ[key]:
                            msg = (
                                f"ℹ️  Skipping {key} from Streamlit "
                                "secrets (already set from .env)"
                            )
                            if _secrets_debug_enabled():
                                print(msg)
                            continue

                        # CRITICAL FIX: Skip placeholder values
                        placeholder_patterns = [
                            "your-",
                            "your_",
                            "placeholder",
                            "example",
                            "change-me",
                            "set-this",
                            "TODO",
                            "FIXME",
                            "replace",
                        ]
                        is_placeholder = any(
                            pattern in value.lower() for pattern in placeholder_patterns
                        )

                        if not is_placeholder:
                            os.environ[key] = value
                            secret_count += 1
                        else:
                            if _secrets_debug_enabled():
                                msg = (
                                    f"⚠️  Skipping placeholder value for {key} "
                                    "in Streamlit secrets"
                                )
                                print(msg)

            if secret_count > 0 and _secrets_debug_enabled():
                msg = (
                    f"✅ Loaded {secret_count} additional secrets "
                    "from Streamlit Cloud"
                )
                print(msg)
                if not loaded_from:
                    loaded_from = "Streamlit Cloud"

    except ImportError:
        # Streamlit not installed - expected for non-Streamlit runs
        pass
    except Exception as e:
        if _secrets_debug_enabled():
            print(f"⚠️  Could not load Streamlit secrets: {e}")

    # Check if we have credentials
    if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv(
        "GOOGLE_SEARCH_API_KEY"
    ):
        if not loaded_from:
            loaded_from = "Environment variables"
        return True

    if not loaded_from:
        # In public Streamlit, it's OK to run without local credentials when using Cloud Run mode.
        # Callers should handle missing secrets gracefully.
        return False

    return True


def verify_credentials():
    """
    Verify that required credentials are available.

    Returns:
        dict: Status of each credential type
    """
    status = {
        "google_application_credentials": bool(
            os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        ),
        "google_search_api_key": bool(os.getenv("GOOGLE_SEARCH_API_KEY")),
        "cse_id": bool(os.getenv("CSE_ID")),
        "youtube_api_key": bool(os.getenv("YOUTUBE_API_KEY")),
        "project_id": bool(os.getenv("PROJECT_ID")),
    }

    # Check if service account file actually exists
    if status["google_application_credentials"]:
        cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if not Path(cred_path).exists():
            status["google_application_credentials"] = False
            print(f"⚠️  Service account file not found: {cred_path}")

    return status


def print_credential_status():
    """Print a summary of credential status."""
    status = verify_credentials()

    print("\n" + "=" * 60)
    print("🔐 CREDENTIAL STATUS")
    print("=" * 60)

    labels = {
        "google_application_credentials": "Google Service Account",
        "google_search_api_key": "Google Search API Key",
        "cse_id": "Custom Search Engine ID",
        "youtube_api_key": "YouTube API Key",
        "project_id": "GCP Project ID",
    }

    for key, label in labels.items():
        icon = "✅" if status[key] else "❌"
        state = "Configured" if status[key] else "MISSING"
        print(f"{icon} {label}: {state}")

    print("=" * 60 + "\n")

    all_ok = all(status.values())
    if not all_ok:
        msg = (
            "⚠️  Some credentials are missing. "
            "Check your .env file or Streamlit secrets."
        )
        print(msg)
        print("   See STREAMLIT_DEPLOYMENT_GUIDE.md " "for setup instructions.\n")

    return all_ok


# Auto-load secrets on import
if __name__ != "__main__":
    load_secrets()
