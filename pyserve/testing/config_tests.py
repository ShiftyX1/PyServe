import os
import traceback
from pyserve.configuration import Configuration
from pyserve.core.config.validator import ConfigValidator


class TestConfiguration:
    def __init__(self):
        self.config = Configuration()
        
    def test_load_config(self) -> bool:
        print("\n=== Testing Configuration Loading ===")
        try:
            self.config._load_configuration()
            print("✅ Configuration loaded successfully")
            return True
        except Exception as e:
            print(f"❌ Failed to load configuration: {str(e)}")
            traceback.print_exc()
            return False
    
    def test_configuration(self) -> int:
        """
        Test configuration content
        
        Returns:
            0 - if all mandatory and optional configurations are successful
            1 - if mandatory configurations are successful, but optional are missing/invalid
            2 - if mandatory configurations are missing/invalid (critical error)
        """
        print("\n=== Testing Configuration Content ===")
        
        self.config._load_configuration()
        
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
            assert isinstance(self.config.server_config['reverse_proxy'], list)
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
    
    def test_configuration_validation(self) -> bool:
        print("\n=== Testing Configuration Validation ===")
        
        is_valid, errors = self.config.validate()
        
        if is_valid:
            print("✅ Configuration validation passed")
            return True
        else:
            print("❌ Configuration validation failed:")
            for error in errors:
                print(f"  - {error}")
            return False
    
    def test_static_directories(self) -> bool:
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
        
        if self.config.ssl_config.enabled:
            for file_type, file_path in [('cert', self.config.ssl_config.cert_file), 
                                         ('key', self.config.ssl_config.key_file)]:
                if file_path:
                    ssl_dir = os.path.dirname(file_path)
                    if ssl_dir and not os.path.exists(ssl_dir):
                        print(f"⚠️ SSL {file_type} directory '{ssl_dir}' does not exist")
                        try:
                            os.makedirs(ssl_dir, exist_ok=True)
                            print(f"✅ Created SSL {file_type} directory: {ssl_dir}")
                        except Exception as e:
                            print(f"❌ Failed to create SSL {file_type} directory: {str(e)}")
                            all_passed = False
            
        return all_passed
    
    def test_ssl_configuration(self) -> bool:
        print("\n=== Testing SSL Configuration ===")
        
        if not self.config.ssl_config.enabled:
            print("ℹ️ SSL is disabled, skipping SSL tests")
            return True
        
        print("✅ SSL is enabled")
        
        if self.config.ssl_config.cert_file:
            if os.path.isfile(self.config.ssl_config.cert_file):
                print(f"✅ SSL certificate file exists: {self.config.ssl_config.cert_file}")
            else:
                print(f"❌ SSL certificate file not found: {self.config.ssl_config.cert_file}")
                return False
        else:
            print("❌ SSL certificate file not specified")
            return False
        
        if self.config.ssl_config.key_file:
            if os.path.isfile(self.config.ssl_config.key_file):
                print(f"✅ SSL key file exists: {self.config.ssl_config.key_file}")
            else:
                print(f"❌ SSL key file not found: {self.config.ssl_config.key_file}")
                return False
        else:
            print("❌ SSL key file not specified")
            return False
        
        return True
    
    def run_all_tests(self) -> int:
        print("\n" + "="*50)
        print("Running All Configuration Tests")
        print("="*50)
        
        if not self.test_load_config():
            return 3
        
        validation_passed = self.test_configuration_validation()
        
        config_result = self.test_configuration()
        
        directories_passed = self.test_static_directories()
        
        ssl_passed = self.test_ssl_configuration()
        
        if config_result == 2:  # Critical configuration failure
            return 2
        elif not validation_passed or not ssl_passed:
            return 2  # Critical failure
        elif config_result == 1 or not directories_passed:
            return 1  # Optional failure
        else:
            print("\n" + "="*50)
            print("✅ All tests passed successfully!")
            print("="*50)
            return 0