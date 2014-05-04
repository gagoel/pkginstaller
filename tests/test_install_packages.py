import sys
import os
import json
import unittest
import logging.config
import shutil

sys.path.append(
    os.path.abspath(os.path.dirname(__file__) + '/../pkginstaller')
)

from pkginstaller import *


class TestInstallPackage(unittest.TestCase):
    
    @classmethod 
    def setUpClass(cls):
        # testcase temp directory, it will delete after tests execution.
        curr_file_dir = os.path.abspath(os.path.dirname(__file__))
        cls.temp_dir = os.path.join(
            curr_file_dir, 'temp_install_test_packages'
        )

        if os.path.exists(cls.temp_dir):
            raise Exception(
                'Make sure you do not have {} directory, this directory '
                'will be used by tests as temporary location and it will be '
                'deleted after operation'.format(cls.temp_dir)
            )
        else:
            os.makedirs(cls.temp_dir)
        
        # parsing configuration file
        cls.test_config_file = os.path.join(
            curr_file_dir, 'tests_config.json'
        )
        cls.test_config = None
        with open(cls.test_config_file) as conf_file:
            try:
                cls.test_config = json.load(conf_file)
            except Exception as e:                  
                print(
                    'configuration file {} parsing failed'.format(
                    cls.test_config_file)
                )
                raise e

        # setting logger.
        logging.config.dictConfig(cls.test_config['LOGGING']) 
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir)

    def test_install_package(self):
        test_package_name = "openssl"
        test_package_file_name = "openssl-1.0.1g.tar.gz" 
        test_package_urls = ["http://www.openssl.org/source"]
        test_package_build_type = "imake"
        test_package_config_args = [
            "--openssldir=$INSTALL_ROOT_DIR/openssldir",
            "shared"
        ]
        test_package_install_check_files = [
            "$PACKAGE_INSTALL_DIR/bin/openssl"
        ]
        test_package_install_check_cmds = []

        test_package_cache_directory = os.path.join(self.temp_dir, 'src_repo')
        test_package_extract_root_directory = \
            os.path.join(self.temp_dir, 'src')
        test_package_build_root_directory = \
            os.path.join(self.temp_dir, 'build')
        test_package_install_root_directory = \
            os.path.join(self.temp_dir, 'install')
     
        install_package(
            test_package_name,
            test_package_file_name,
            test_package_build_type,
            test_package_urls,
            test_package_install_check_files,
            test_package_install_check_cmds,
            test_package_cache_directory,
            test_package_extract_root_directory,
            test_package_build_root_directory,
            test_package_install_root_directory,
            package_configure_args = test_package_config_args
        )
    
    def test_install_packages(self):
        test_package_cache_directory = os.path.join(self.temp_dir, 'src_repo')
        test_package_extract_root_directory = \
            os.path.join(self.temp_dir, 'src')
        test_package_build_root_directory = \
            os.path.join(self.temp_dir, 'build')
        test_package_install_root_directory = \
            os.path.join(self.temp_dir, 'install')
        
        install_packages(
            self.test_config['test-install-packages']['packages'],
            test_package_cache_directory,
            test_package_extract_root_directory,
            test_package_build_root_directory,
            test_package_install_root_directory
        )

if __name__ == "__main__":
    unittest.main()
