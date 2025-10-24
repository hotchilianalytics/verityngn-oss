"""
Test script to validate the OSS repository extraction.

Tests:
1. Import all modules
2. Configuration loading
3. Authentication setup
4. LLM logging functionality
5. Service layer functionality
6. Basic workflow execution (if credentials available)

Run: python test_extraction.py
"""

import sys
import os
from pathlib import Path

# Add repo to path
repo_root = Path(__file__).parent
sys.path.insert(0, str(repo_root))

def test_imports():
    """Test that all modules can be imported."""
    print("=" * 60)
    print("TEST 1: Import Validation")
    print("=" * 60)
    
    tests = []
    
    # Test workflow imports
    try:
        from verityngn.workflows import pipeline
        print("✅ workflows.pipeline")
        tests.append(True)
    except Exception as e:
        print(f"❌ workflows.pipeline: {e}")
        tests.append(False)
    
    try:
        from verityngn.workflows import analysis
        print("✅ workflows.analysis")
        tests.append(True)
    except Exception as e:
        print(f"❌ workflows.analysis: {e}")
        tests.append(False)
    
    try:
        from verityngn.workflows import verification
        print("✅ workflows.verification")
        tests.append(True)
    except Exception as e:
        print(f"❌ workflows.verification: {e}")
        tests.append(False)
    
    try:
        from verityngn.workflows import reporting
        print("✅ workflows.reporting")
        tests.append(True)
    except Exception as e:
        print(f"❌ workflows.reporting: {e}")
        tests.append(False)
    
    # Test config imports
    try:
        from verityngn.config import auth
        print("✅ config.auth")
        tests.append(True)
    except Exception as e:
        print(f"❌ config.auth: {e}")
        tests.append(False)
    
    try:
        from verityngn.config import config_loader
        print("✅ config.config_loader")
        tests.append(True)
    except Exception as e:
        print(f"❌ config.config_loader: {e}")
        tests.append(False)
    
    try:
        from verityngn.config import settings
        print("✅ config.settings")
        tests.append(True)
    except Exception as e:
        print(f"❌ config.settings: {e}")
        tests.append(False)
    
    # Test LLM logging imports
    try:
        from verityngn.llm_logging import get_logger, analyze_logs
        print("✅ llm_logging")
        tests.append(True)
    except Exception as e:
        print(f"❌ llm_logging: {e}")
        tests.append(False)
    
    # Test services
    try:
        from verityngn.services.video import downloader
        print("✅ services.video.downloader")
        tests.append(True)
    except Exception as e:
        print(f"❌ services.video.downloader: {e}")
        tests.append(False)
    
    try:
        from verityngn.services.search import web_search
        print("✅ services.search.web_search")
        tests.append(True)
    except Exception as e:
        print(f"❌ services.search.web_search: {e}")
        tests.append(False)
    
    try:
        from verityngn.services.storage import gcs
        print("✅ services.storage.gcs")
        tests.append(True)
    except Exception as e:
        print(f"❌ services.storage.gcs: {e}")
        tests.append(False)
    
    # Test models
    try:
        from verityngn.models import report
        print("✅ models.report")
        tests.append(True)
    except Exception as e:
        print(f"❌ models.report: {e}")
        tests.append(False)
    
    print()
    passed = sum(tests)
    total = len(tests)
    print(f"Result: {passed}/{total} imports successful ({passed/total*100:.1f}%)")
    
    return all(tests)


def test_config_loading():
    """Test configuration loading."""
    print("\n" + "=" * 60)
    print("TEST 2: Configuration Loading")
    print("=" * 60)
    
    try:
        from verityngn.config.config_loader import get_config
        
        config = get_config()
        print("✅ Configuration loaded")
        
        # Test accessing config values
        project_id = config.get('gcp.project_id')
        print(f"   GCP Project: {project_id}")
        
        model_name = config.get('models.vertex.model_name')
        print(f"   Model: {model_name}")
        
        output_dir = config.get('output.local_dir')
        print(f"   Output Dir: {output_dir}")
        
        llm_logging = config.get('llm_logging.enabled')
        print(f"   LLM Logging: {llm_logging}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auth():
    """Test authentication setup."""
    print("\n" + "=" * 60)
    print("TEST 3: Authentication")
    print("=" * 60)
    
    try:
        from verityngn.config.auth import auto_detect_auth
        
        auth_provider = auto_detect_auth()
        print(f"✅ Auth provider created: {auth_provider.method}")
        
        # Try to get project ID
        project_id = auth_provider.get_project_id()
        if project_id:
            print(f"   Project ID: {project_id}")
        
        # Don't actually validate credentials (might not be configured yet)
        print("   Note: Credential validation skipped (may not be configured)")
        
        return True
        
    except Exception as e:
        print(f"❌ Authentication setup failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_logging():
    """Test LLM logging functionality."""
    print("\n" + "=" * 60)
    print("TEST 4: LLM Logging")
    print("=" * 60)
    
    try:
        from verityngn.llm_logging import get_logger
        
        # Create logger
        logger = get_logger({'enabled': True, 'output_dir': './test_llm_logs'})
        print("✅ LLM logger created")
        
        # Test logging a call
        call_id = logger.start_call(
            operation='test',
            prompt='This is a test prompt',
            model='gemini-2.5-flash',
            video_id='test_video'
        )
        print(f"✅ Call started: {call_id[:8]}...")
        
        # Log response
        logger.log_response(
            call_id=call_id,
            response_text='This is a test response',
            token_counts={'input': 10, 'output': 20, 'total': 30},
            duration=1.5
        )
        print("✅ Response logged")
        
        # Save call
        filepath = logger.save_call(call_id)
        if filepath:
            print(f"✅ Call saved to: {filepath}")
        
        # Get statistics
        stats = logger.get_statistics()
        print(f"✅ Statistics retrieved: {stats['total_calls']} calls")
        
        # Cleanup test logs
        import shutil
        if os.path.exists('./test_llm_logs'):
            shutil.rmtree('./test_llm_logs')
            print("   Cleaned up test logs")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM logging test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_services():
    """Test service layer basic functionality."""
    print("\n" + "=" * 60)
    print("TEST 5: Service Layer")
    print("=" * 60)
    
    results = []
    
    # Test video utils
    try:
        from verityngn.services.video import downloader
        print("✅ Video downloader module loaded")
        results.append(True)
    except Exception as e:
        print(f"❌ Video downloader: {e}")
        results.append(False)
    
    # Test search services
    try:
        from verityngn.services.search import web_search
        print("✅ Web search module loaded")
        results.append(True)
    except Exception as e:
        print(f"❌ Web search: {e}")
        results.append(False)
    
    # Test storage
    try:
        from verityngn.services.storage import gcs
        print("✅ GCS storage module loaded")
        results.append(True)
    except Exception as e:
        print(f"❌ GCS storage: {e}")
        results.append(False)
    
    # Test report generation
    try:
        from verityngn.services.report import html_generator
        print("✅ HTML generator module loaded")
        results.append(True)
    except Exception as e:
        print(f"❌ HTML generator: {e}")
        results.append(False)
    
    return all(results)


def test_workflow_creation():
    """Test workflow graph creation (without execution)."""
    print("\n" + "=" * 60)
    print("TEST 6: Workflow Creation")
    print("=" * 60)
    
    try:
        from verityngn.workflows.pipeline import create_workflow
        
        workflow = create_workflow()
        print("✅ Workflow graph created successfully")
        
        # Try to compile (doesn't execute)
        compiled = workflow.compile()
        print("✅ Workflow compiled successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def print_summary(results):
    """Print test summary."""
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    test_names = [
        "Import Validation",
        "Configuration Loading",
        "Authentication",
        "LLM Logging",
        "Service Layer",
        "Workflow Creation"
    ]
    
    for i, (name, result) in enumerate(zip(test_names, results), 1):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{i}. {name:.<40} {status}")
    
    print()
    passed = sum(results)
    total = len(results)
    print(f"Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if all(results):
        print("\n🎉 All tests passed! Repository is ready for use.")
        print("\nNext steps:")
        print("1. Configure config.yaml with your GCP settings")
        print("2. Set up authentication (service account or gcloud)")
        print("3. Try: python -m verityngn.workflows.pipeline <youtube_url>")
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        print("Common issues:")
        print("- Missing dependencies (run: pip install -r requirements.txt)")
        print("- Import path issues")
        print("- Configuration file missing")
    
    return all(results)


def main():
    """Run all tests."""
    print("=" * 60)
    print("VERITYNGN OSS REPOSITORY - EXTRACTION TEST")
    print("=" * 60)
    print()
    
    results = []
    
    # Run tests
    results.append(test_imports())
    results.append(test_config_loading())
    results.append(test_auth())
    results.append(test_llm_logging())
    results.append(test_services())
    results.append(test_workflow_creation())
    
    # Print summary
    success = print_summary(results)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()


