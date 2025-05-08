from .configure import Configuration
import os
import traceback
import sys

class TestConfiguration:
    def __init__(self):
        self.config = Configuration()
        
    def test_load_config(self):
        print("\n=== Testing Configuration Loading ===")
        try:
            self.config.load_config()
            print("✅ Configuration loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load configuration: {str(e)}")
            traceback.print_exc()
            return False

    def test_configuration(self):
        """
        Тестирует содержимое конфигурации
        Возвращает: 
            0 - если все обязательные и необязательные конфигурации успешны
            1 - если обязательные конфигурации успешны, но необязательные отсутствуют/неверны
            2 - если обязательные конфигурации отсутствуют/неверны (критическая ошибка)
        """
        print("\n=== Testing Configuration Content ===")
        self.config.load_config()
        
        mandatory_passed = True
        optional_passed = True
        
        try:
            assert self.config.server_config != {}
            assert 'host' in self.config.server_config
            assert 'port' in self.config.server_config
            print("✅ Server configuration: OK")
        except AssertionError:
            print("❌ Server configuration: Missing or incomplete (CRITICAL)")
            mandatory_passed = False
        
        try:
            assert self.config.http_config != {}
            assert 'static_dir' in self.config.http_config
            assert 'templates_dir' in self.config.http_config
            print("✅ HTTP configuration: OK")
        except AssertionError:
            print("❌ HTTP configuration: Missing or incomplete (CRITICAL)")
            mandatory_passed = False
        
        try:
            assert self.config.logging_config != {}
            assert 'level' in self.config.logging_config
            print("✅ Logging configuration: OK")
        except AssertionError:
            print("⚠️ Logging configuration: Missing or incomplete (WARNING)")
            optional_passed = False
        
        try:
            assert isinstance(self.config.redirections, list)
            print("✅ Redirections: OK")
        except AssertionError:
            print("⚠️ Redirections: Not configured properly (WARNING)")
            optional_passed = False
        
        try:
            assert 'reverse_proxy' in self.config.server_config
            print("✅ Reverse proxy configuration: OK")
        except AssertionError:
            print("⚠️ Reverse proxy configuration: Not configured (OPTIONAL)")
        if mandatory_passed and optional_passed:
            print("\n✅ All configuration tests passed")
            return 0
        elif mandatory_passed:
            print("\n⚠️ Mandatory configuration tests passed, but some optional tests failed")
            return 1
        else:
            print("\n❌ Critical configuration tests failed - server cannot start properly")
            return 2

    def test_static_directories(self):
        print("\n=== Testing Static Directories ===")
        all_passed = True
        
        static_dir = self.config.http_config.get('static_dir', './static')
        if not os.path.exists(static_dir):
            print(f"⚠️ Static directory '{static_dir}' does not exist")
            try:
                os.makedirs(static_dir, exist_ok=True)
                print(f"✅ Created static directory: {static_dir}")
            except Exception as e:
                print(f"❌ Failed to create static directory: {str(e)}")
                all_passed = False
        else:
            print(f"✅ Static directory exists: {static_dir}")
            
        templates_dir = self.config.http_config.get('templates_dir', './templates')
        if not os.path.exists(templates_dir):
            print(f"⚠️ Templates directory '{templates_dir}' does not exist")
            try:
                os.makedirs(templates_dir, exist_ok=True)
                print(f"✅ Created templates directory: {templates_dir}")
            except Exception as e:
                print(f"❌ Failed to create templates directory: {str(e)}")
                all_passed = False
        else:
            print(f"✅ Templates directory exists: {templates_dir}")
            
        return all_passed