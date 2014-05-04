import json
import sys
import os
import unittest
import logging.config
import shutil

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../pkginstaller'))

from pkginstaller.internal.setup_utils import *

class TestSetupUtils(unittest.TestCase):

    def setUp(self):
        # testcase temp directory, it will delete after tests execution.
        curr_file_dir = os.path.abspath(os.path.dirname(__file__))
        self.temp_dir = os.path.join(curr_file_dir, 'temp_setup_test_utils')

        if os.path.exists(self.temp_dir):
            raise Exception(
                'Make sure you do not have {} directory, this directory '
                'will be used by tests as temporary location and it will be '
                'deleted after operation'.format(self.temp_dir)
            )
        else:
            os.makedirs(self.temp_dir)

        # parsing configuration file
        self.test_config_file = os.path.join(
            curr_file_dir, 'tests_config.json'
        )
        self.test_config = None
        with open(self.test_config_file) as conf_file:
            try:
                self.test_config = json.load(conf_file)
            except Exception as e:                  
                print(
                    'configuration file {} parsing failed'.format(
                    self.test_config_file)
                )
                raise e

        # setting logger.
        logging.config.dictConfig(self.test_config['LOGGING']) 

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_download_file(self):
        # tar, tar.gz, tar.bz2 or tar.xz download test.
        test_file_name = "mod_wsgi-3.4.tar.gz"
        test_download_urls = "https://modwsgi.googlecode.com/files"
        test_src_repo = os.path.join(self.temp_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo
        )
        self.assertEqual(download_status, True)
        self.assertEqual(os.path.exists(file_path), True)

        # git cloning test
        test_file_name = "MySQL-for-Python-3.git"
        test_download_urls = "https://github.com/gagoel"
        test_src_repo = os.path.join(self.temp_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo
        )
        self.assertEqual(download_status, True)
        self.assertEqual(os.path.exists(file_path), True)

    def test_extract_file(self):
        test_file_name = "mod_wsgi-3.4.tar.gz"
        test_download_urls = "https://modwsgi.googlecode.com/files"
        test_src_repo = os.path.join(self.temp_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo
        )
        test_extract_path = os.path.join(self.temp_dir, 'src')
        extracted_file = extract_file(
            test_file_name, test_src_repo, test_extract_path
        )

        self.assertEqual(os.path.exists(test_extract_path), True)

    def test_replace_env_vars(self):
        test_environments = {
            "TEST_ENV1" : "TEST_ENV1_VALUE",    
            "TEST_ENV2" : "TEST_ENV2_VALUE"
        }

        for a, b in test_environments.items():
            os.environ[a] = b

        # string type
        test_string = "$TEST_ENV1/testpath"
        test_string_after_resolve = os.path.join(
            test_environments['TEST_ENV1'], "testpath"
        )
        self.assertEqual(
            test_string_after_resolve, replace_env_vars(test_string)
        )

        # list type
        test_string = ["$TEST_ENV1/testpath1", "$TEST_ENV2/testpath2"]
        resolve_test_string = replace_env_vars(test_string)
        self.assertEqual(resolve_test_string[0], "TEST_ENV1_VALUE/testpath1")
        self.assertEqual(resolve_test_string[1], "TEST_ENV2_VALUE/testpath2")

        # dict type
        test_string = {
            "key1" : ["$TEST_ENV1/testpath1", "$TEST_ENV2/testpath2"]
        }
        resolve_test_string = replace_env_vars(test_string)
        self.assertEqual(
            resolve_test_string['key1'][0], "TEST_ENV1_VALUE/testpath1"
        )
        self.assertEqual(
            resolve_test_string['key1'][1], "TEST_ENV2_VALUE/testpath2"
        )
    
    def test_run_command(self):
        cmd = ['/bin/sh', '-c', 'pwd']
        stdout, stderr = run_command(cmd)
        self.assertEqual(stderr, "")

if __name__ == "__main__":
    unittest.main()
