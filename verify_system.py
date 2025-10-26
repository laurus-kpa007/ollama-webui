"""
System Verification Script - Ollama WebUI v2.0
Verifies all components are properly implemented and importable
"""
import sys
import os

def print_section(title):
    """Print a section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def check_python_version():
    """Check Python version"""
    print_section("Python Environment")
    version = sys.version_info
    print(f"Python Version: {version.major}.{version.minor}.{version.micro}")

    if version.major >= 3 and version.minor >= 10:
        print("✅ Python version is compatible (3.10+)")
        return True
    else:
        print("❌ Python version must be 3.10 or higher")
        return False

def check_file_structure():
    """Check if all required files exist"""
    print_section("File Structure Verification")

    required_files = {
        'Models': [
            'models/__init__.py',
            'models/user.py',
            'models/session.py',
            'models/message.py',
            'models/plugin.py'
        ],
        'Services': [
            'services/__init__.py',
            'services/session_manager.py',
            'services/mcp_server.py',
            'services/mcp_client.py',
            'services/autogen_service.py'
        ],
        'Routes': [
            'routes/__init__.py',
            'routes/sessions.py',
            'routes/mcp.py',
            'routes/autogen.py',
            'routes/plugins.py'
        ],
        'Plugins': [
            'plugins/plugin_system.py',
            'plugins/example_plugin.py'
        ],
        'Utils': [
            'utils/config_manager.py'
        ],
        'Static': [
            'static/js/session-manager.js',
            'static/js/mcp-manager.js',
            'static/js/autogen-manager.js',
            'static/js/app.js',
            'static/css/sessions.css',
            'static/css/mcp-tools.css'
        ],
        'Templates': [
            'templates/index_new.html'
        ],
        'Core': [
            'app_new.py',
            'requirements.txt'
        ]
    }

    all_exist = True
    for category, files in required_files.items():
        print(f"\n{category}:")
        for file_path in files:
            exists = os.path.exists(file_path)
            status = "✅" if exists else "❌"
            print(f"  {status} {file_path}")
            if not exists:
                all_exist = False

    return all_exist

def check_imports():
    """Check if Python modules can be imported"""
    print_section("Python Module Imports")

    imports_to_check = [
        ('Flask', 'from flask import Flask'),
        ('SQLAlchemy', 'from flask_sqlalchemy import SQLAlchemy'),
        ('Redis', 'import redis'),
        ('AutoGen AgentChat', 'from autogen_agentchat.agents import AssistantAgent'),
        ('AutoGen Extensions', 'from autogen_ext.models.openai import OpenAIChatCompletionClient'),
        ('MCP', 'import mcp'),
        ('Pydantic', 'from pydantic import BaseModel'),
    ]

    all_imported = True
    for name, import_statement in imports_to_check:
        try:
            exec(import_statement)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name}: {str(e)}")
            all_imported = False
        except Exception as e:
            print(f"⚠️  {name}: {str(e)}")

    return all_imported

def check_local_imports():
    """Check if local modules can be imported"""
    print_section("Local Module Imports")

    # Add current directory to path
    if os.getcwd() not in sys.path:
        sys.path.insert(0, os.getcwd())

    modules_to_check = [
        ('ConfigManager', 'from utils.config_manager import ConfigManager'),
        ('Database Models', 'from models import db, User, ChatSession, Message'),
        ('Plugin System', 'from plugins.plugin_system import PluginBase, PluginManager'),
        ('AutoGen Service', 'from services.autogen_service import AutogenService, get_autogen_service'),
    ]

    all_imported = True
    for name, import_statement in modules_to_check:
        try:
            exec(import_statement)
            print(f"✅ {name}")
        except ImportError as e:
            print(f"❌ {name}: {str(e)}")
            all_imported = False
        except Exception as e:
            print(f"⚠️  {name}: {str(e)}")

    return all_imported

def check_configuration_files():
    """Check configuration files"""
    print_section("Configuration Files")

    config_files = [
        'requirements.txt',
        'AUTOGEN_0.7.5_MIGRATION.md',
        'docs/ARCHITECTURE.md',
        'README_V2.md'
    ]

    all_exist = True
    for config_file in config_files:
        exists = os.path.exists(config_file)
        status = "✅" if exists else "❌"
        print(f"  {status} {config_file}")
        if not exists:
            all_exist = False

    return all_exist

def verify_autogen_version():
    """Verify AutoGen package version"""
    print_section("AutoGen Version Check")

    try:
        # Read requirements.txt
        with open('requirements.txt', 'r') as f:
            content = f.read()

        if 'autogen-agentchat==0.7.5' in content:
            print("✅ autogen-agentchat==0.7.5 specified in requirements.txt")
            return True
        elif 'pyautogen' in content:
            print("❌ Old pyautogen package still in requirements.txt")
            return False
        else:
            print("⚠️  AutoGen package not found in requirements.txt")
            return False
    except Exception as e:
        print(f"❌ Error reading requirements.txt: {e}")
        return False

def check_database_schema():
    """Verify database schema is defined"""
    print_section("Database Schema Verification")

    try:
        from models.user import User
        from models.session import ChatSession, SessionMetadata
        from models.message import Message
        from models.plugin import UserPreference

        models_found = []

        if hasattr(User, '__tablename__'):
            models_found.append(f"✅ User (table: {User.__tablename__})")

        if hasattr(ChatSession, '__tablename__'):
            models_found.append(f"✅ ChatSession (table: {ChatSession.__tablename__})")

        if hasattr(SessionMetadata, '__tablename__'):
            models_found.append(f"✅ SessionMetadata (table: {SessionMetadata.__tablename__})")

        if hasattr(Message, '__tablename__'):
            models_found.append(f"✅ Message (table: {Message.__tablename__})")

        if hasattr(UserPreference, '__tablename__'):
            models_found.append(f"✅ UserPreference (table: {UserPreference.__tablename__})")

        for model in models_found:
            print(model)

        return len(models_found) == 5

    except Exception as e:
        print(f"❌ Error checking database schema: {e}")
        return False

def generate_report(results):
    """Generate final report"""
    print_section("Verification Summary")

    total_checks = len(results)
    passed_checks = sum(1 for r in results.values() if r)

    print(f"\nTotal Checks: {total_checks}")
    print(f"Passed: {passed_checks}")
    print(f"Failed: {total_checks - passed_checks}")
    print(f"Success Rate: {(passed_checks/total_checks)*100:.1f}%\n")

    for check, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {check}")

    print("\n" + "=" * 60)

    if passed_checks == total_checks:
        print("🎉 All checks passed! System is ready.")
        print("\nNext steps:")
        print("  1. Install dependencies: pip install -r requirements.txt")
        print("  2. Run the application: python app_new.py")
        print("  3. Access the UI: http://localhost:5000")
    else:
        print("⚠️  Some checks failed. Please review the errors above.")
        print("\nRecommended actions:")
        if not results.get('Python Version'):
            print("  - Update Python to version 3.10 or higher")
        if not results.get('Package Imports'):
            print("  - Install dependencies: pip install -r requirements.txt")
        if not results.get('File Structure'):
            print("  - Ensure all required files are present")

    print("=" * 60 + "\n")

def main():
    """Run all verification checks"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║       Ollama WebUI v2.0 - System Verification            ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
    """)

    results = {
        'Python Version': check_python_version(),
        'File Structure': check_file_structure(),
        'Configuration Files': check_configuration_files(),
        'AutoGen Version': verify_autogen_version(),
    }

    # Only check imports if files exist
    if results['File Structure']:
        results['Local Module Imports'] = check_local_imports()
        results['Database Schema'] = check_database_schema()

    # Check package imports separately
    results['Package Imports'] = check_imports()

    generate_report(results)

if __name__ == '__main__':
    main()
