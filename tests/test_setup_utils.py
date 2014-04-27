import sys
import os
import unittest
import logging.config

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../src'))

from tests_utils import *
from setup_utils import *

class TestSetupUtils(unittest.TestCase):

    def setUp(self):
        project_root = os.getenv('PROJECT_ROOT')
        if project_root == None:
            raise Exception('PROJECT_ROOT environment variable is not set.')

        self.test_repo_root = os.path.join(
            project_root, 'content/test_repo/src_repo'
        )
        self.test_src_root = os.path.join(
            project_root, 'content/test_repo/src'
        )
        if not os.path.exists(self.test_repo_root):
            os.makedirs(self.test_repo_root)
        if not os.path.exists(self.test_src_root):
            os.makedirs(self.test_src_root)

        self.test_config = parse_tests_configuration_file()
        self.test_file_name = "Python-3.3.0.tar.bz2" 
        self.test_file_url = "http://www.python.org/ftp/python/3.3.0/"

        # Setting logger.
        logging.config.dictConfig(self.test_config['LOGGING']) 

    def test_download_file(self):
        # zip, tar, tar.gz, tar.bz2 or tar.xz download test.
        download_status = download_file(
            self.test_file_name, self.test_file_url, self.test_repo_root
        )
        self.assertEqual(download_status, True)

        # git cloning test

    def test_extract_file(self):
        extracted_file = extract_file(
            self.test_file_name, self.test_repo_root, self.test_src_root 
        )

    def test_replace_env_vars(self):
        test_string = "$PROJECT_ROOT/testpath"
        test_string_after_resolve = os.path.join(
            os.getenv('PROJECT_ROOT'), "testpath"
        )
        self.assertEqual(
            test_string_after_resolve, replace_env_vars(test_string)
        )

    def test_run_command(self):
        cmd = ['/bin/sh', '-c', 'pwd']
        stdout, stderr = run_command(cmd)
        self.assertEqual(stderr, None)

if __name__ == "__main__":
    unittest.main()
