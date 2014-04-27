import sys
import os
import json
import unittest
import logging.config

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../pkginstaller'))

from pkginstaller.install_packages import *
from tests_utils import *
PROJECT_ROOT = os.getenv('PROJECT_ROOT')


class TestInstallPackage(unittest.TestCase):
    
    def setUp(self):
        self.test_package_name = "openssl"
        self.test_package_file_name = "openssl-1.0.1g.tar.gz" 
        self.test_package_urls = ["http://www.openssl.org/source"]
        self.test_package_build_type = "imake"
        self.test_package_config_args = [
            "--openssldir=$PACKAGE_INSTALL_DIR/openssldir",
            "shared"
        ]
        self.test_package_install_check_files = [
            "$PACKAGE_INSTALL_DIR/bin/openssl"
        ]
        self.test_package_install_check_cmds = []
        
        configuration = parse_tests_configuration_file()

        logging_file = os.path.abspath("./logs/pkginstaller.log")
        if not os.path.isfile(logging_file):                                       
            file_dirname = os.path.dirname(logging_file)
            if not os.path.exists(file_dirname):
                os.makedirs(file_dirname)                            
            fd = open(logging_file, "w+")
            fd.close()             
            os.chmod(logging_file, 0o666)
       
        logging.config.dictConfig(configuration['LOGGING']) 
        
    def test_install_package(self):
        install_package(
            self.test_package_name,
            self.test_package_file_name,
            self.test_package_build_type,
            self.test_package_urls,
            self.test_package_install_check_files,
            self.test_package_install_check_cmds,
            package_configure_args = self.test_package_config_args
        )
    
    def test_install_packages(self):
        test_config_file = os.path.join(PROJECT_ROOT, "tests/test-config.json")
        
        config_dict = None
        with open(test_config_file) as conf_file:
            try:
                config_dict = json.load(conf_file)
            except Exception as e:                  
                print('CONFIGURATION FILE PARSING FAILED.')
                raise e                    
        
        pkgs_config = config_dict['packages']
        install_packages(pkgs_config)

if __name__ == "__main__":
    unittest.main()
