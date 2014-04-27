import sys
import os
import json
import unittest
import logging.config

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../src'))

from tests_utils import *
from setup_packages import SetupPackages

class TestSetupPackages(unittest.TestCase):
    
    def setUp(self):
        self.project_root = os.getenv('PROJECT_ROOT')
        if self.project_root == None:
            raise Exception('PROJECT_ROOT environment variable is not set.')

        self.test_file_name = "Python-3.3.0.tar.bz2" 
        self.test_file_url = "http://www.python.org/ftp/python/3.3.0/"
        configuration = parse_tests_configuration_file()
        self.test_packages_config = configuration['setup.packages']
        self.externals_dir = "content/test_repo"
        
        # Setting logger.
        logging.config.dictConfig(configuration['LOGGING']) 

    def test_download(self):
        setup_packages_obj = SetupPackages(
            self.test_packages_config, externals_dir=self.externals_dir
        )
        setup_packages_obj.download()
    
    def test_extract(self):
        setup_packages_obj = SetupPackages(
            self.test_packages_config, externals_dir=self.externals_dir
        )
        setup_packages_obj.extract()
    
    def test_install(self):
        setup_packages_obj = SetupPackages(
            self.test_packages_config, externals_dir=self.externals_dir
        )
        setup_packages_obj.install()

if __name__ == "__main__":
    unittest.main()
