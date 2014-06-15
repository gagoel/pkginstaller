import sys
import os
import json
import unittest
import logging.config
import shutil

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../pkginstaller'))

from pkginstaller.internal.setup_packages import SetupPackages
from tests import VERBOSE

class TestSetupPackages(unittest.TestCase):
   
    @classmethod 
    def setUpClass(cls):
        # testcase temp directory, it will delete after tests execution.
        curr_file_dir = os.path.abspath(os.path.dirname(__file__))
        cls.temp_dir = os.path.join(curr_file_dir, 'temp_setup_test_packages')

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
        logging.shutdown()

    def test_download(self):
        setup_pkg_config_list = \
            self.test_config['test-setup-packages']['packages']
        pkg_cache_dir = os.path.join(self.temp_dir, 'src_repo')
        pkg_extract_root_dir = os.path.join(self.temp_dir, 'src')
        pkg_build_root_dir = os.path.join(self.temp_dir, 'build')
        pkg_install_root_dir = os.path.join(self.temp_dir, 'install')

        setup_packages_obj = SetupPackages(
            setup_pkg_config_list,
            pkg_cache_dir,
            pkg_extract_root_dir,
            pkg_build_root_dir,
            pkg_install_root_dir,
            verbose=VERBOSE
        )
        setup_packages_obj.download()
    
    def test_extract(self):
        setup_pkg_config_list = \
            self.test_config['test-setup-packages']['packages']
        pkg_cache_dir = os.path.join(self.temp_dir, 'src_repo')
        pkg_extract_root_dir = os.path.join(self.temp_dir, 'src')
        pkg_build_root_dir = os.path.join(self.temp_dir, 'build')
        pkg_install_root_dir = os.path.join(self.temp_dir, 'install')

        setup_packages_obj = SetupPackages(
            setup_pkg_config_list,
            pkg_cache_dir,
            pkg_extract_root_dir,
            pkg_build_root_dir,
            pkg_install_root_dir,
            verbose=VERBOSE
        )
        setup_packages_obj.extract()
    
    def test_install(self):
        setup_pkg_config_list = \
            self.test_config['test-setup-packages']['packages']
        pkg_cache_dir = os.path.join(self.temp_dir, 'src_repo')
        pkg_extract_root_dir = os.path.join(self.temp_dir, 'src')
        pkg_build_root_dir = os.path.join(self.temp_dir, 'build')
        pkg_install_root_dir = os.path.join(self.temp_dir, 'install')

        setup_packages_obj = SetupPackages(
            setup_pkg_config_list,
            pkg_cache_dir,
            pkg_extract_root_dir,
            pkg_build_root_dir,
            pkg_install_root_dir,
            verbose=VERBOSE
        )
        setup_packages_obj.install()

if __name__ == "__main__":
    unittest.main()
