import json
import sys
import os
import unittest
import logging.config
import shutil
import paramiko

sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/../pkginstaller'))

from pkginstaller.internal.setup_utils import *

from tests import VERBOSE

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

        # Remote host data
        self.remote_host = os.environ['REMOTE_HOST_IP'] 
        self.remote_ssh_port = int(os.environ['REMOTE_HOST_SSH_PORT'])
        self.remote_ssh_user = os.environ['REMOTE_HOST_SSH_USER']
        self.remote_ssh_pass = os.environ['REMOTE_HOST_SSH_PASS']
        self.temp_remote_dir = os.environ['REMOTE_HOST_TEMP_DIR']

        if is_path_exists(self.temp_remote_dir, self.remote_host,
            self.remote_ssh_port, self.remote_ssh_user, self.remote_ssh_pass
        ):
            raise Exception(
                'Make sure you do not have {} directory, this directory '
                'will be used by tests as temporary location and it will be '
                'deleted after operation'.format(self.temp_remote_dir)
            )
        else:
            mkdirs(
                self.temp_remote_dir,
                remote_host=self.remote_host,
                remote_ssh_port=self.remote_ssh_port,
                remote_ssh_user=self.remote_ssh_user,
                remote_ssh_pass=self.remote_ssh_pass
            )
        
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        remove_dir(self.temp_remote_dir, self.remote_host,
            self.remote_ssh_port, self.remote_ssh_user, self.remote_ssh_pass)
        logging.shutdown()

    def test_is_path_exists_localhost(self):
        temp_dir = os.path.join(self.temp_dir, 'test-is-path-exists')

        path_status = is_path_exists(temp_dir)
        self.assertEqual(path_status, False)

        mkdirs(temp_dir)
        path_status = is_path_exists(temp_dir)
        self.assertEqual(path_status, True)

    def test_is_path_exists_remotehost(self):
        temp_dir = os.path.join(self.temp_remote_dir, 'test-is-path-exists')

        path_status = is_path_exists(
            temp_dir,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual(path_status, False)

        mkdirs(
            temp_dir,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )

        path_status = is_path_exists(
            temp_dir,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual(path_status, True)

    def test_create_file_localhost(self):
        temp_dir = os.path.join(self.temp_dir, 'test-create-file-dir')

        mkdirs(temp_dir)
        temp_file = os.path.join(temp_dir, 'testfile')
        temp_file_data = 'This is test file data'
        create_file_status = create_file(temp_file, temp_file_data)
        self.assertEqual(create_file_status, True)

        file_obj = open(temp_file, 'r')
        file_data = file_obj.read()
        file_obj.close()
        self.assertEqual(file_data, temp_file_data)

    def test_create_file_remotehost(self):
        temp_dir = os.path.join(self.temp_remote_dir, 'test-create-file-dir')

        mkdirs(
            temp_dir,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )

        temp_file = os.path.join(temp_dir, 'testfile')
        temp_file_data = 'This is test file data'
        create_file_status = create_file(
            temp_file,
            temp_file_data,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual(create_file_status, True)

        t = paramiko.Transport((self.remote_host, self.remote_ssh_port))
        t.connect(username=self.remote_ssh_user, password=self.remote_ssh_pass)
        sftp = paramiko.SFTPClient.from_transport(t)
        sftpfile_obj = sftp.open(temp_file, 'r')
        file_data = sftpfile_obj.read()
        sftpfile_obj.close()
        sftp.close()
        
        self.assertEqual(file_data.decode('utf-8'), temp_file_data)

    def test_remove_file_localhost(self):
        temp_dir = os.path.join(self.temp_dir, 'test-remove-file-dir')

        mkdirs(temp_dir)
        temp_file = os.path.join(temp_dir, 'testfile')
        temp_file_data = 'This is test file data'
        create_file_status = create_file(temp_file, temp_file_data)
        self.assertEqual(create_file_status, True)
        
        path_status = is_path_exists(temp_file)
        self.assertEqual(path_status, True)

        remove_file_status = remove_file(temp_file)
        self.assertEqual(remove_file_status, True)
        
        path_status = is_path_exists(temp_file)
        self.assertEqual(path_status, False)

    def test_remove_file_remotehost(self):
        temp_dir = os.path.join(self.temp_remote_dir, 'test-remove-file-dir')

        mkdirs(
            temp_dir,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )

        temp_file = os.path.join(temp_dir, 'testfile')
        temp_file_data = 'This is test file data'
        create_file_status = create_file(
            temp_file,
            temp_file_data,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual(create_file_status, True)
        
        path_status = is_path_exists(
            temp_file,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual(path_status, True)

        remove_file_status = remove_file(
            temp_file,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual(remove_file_status, True)
        
        path_status = is_path_exists(
            temp_file,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual(path_status, False)
    
    def test_remove_dir_localhost(self):
        temp_dir = os.path.join(self.temp_dir, 'test-remove-dir')

        mkdirs(temp_dir)
        temp_file = os.path.join(temp_dir, 'testfile')
        create_file_status = create_file(
            temp_file, 'This is test file')
        self.assertEqual(create_file_status, True)

        remove_dir_status = remove_dir(temp_dir)
        self.assertEqual(remove_dir_status, True)

    def test_remove_dir_remotehost(self):
        temp_dir = os.path.join(self.temp_remote_dir, 'test-remove-dir')

        mkdirs(
            temp_dir,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )

        temp_file = os.path.join(temp_dir, 'testfile')
        create_file_status = create_file(
            temp_file,
            'This is test file',
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual(create_file_status, True)

        remove_dir_status = remove_dir(
            temp_dir,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )

        self.assertEqual(remove_dir_status, True)

    def test_is_file_downloaded_localhost(self):
        """
        tar, tar.gz, tar.bz2 or tar.xz download test.
        """
        test_file_name = "mod_wsgi-3.4.tar.gz"
        test_download_urls = "https://modwsgi.googlecode.com/files"
        test_src_repo = os.path.join(self.temp_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        # Checking download status before download
        downloaded_status = is_file_downloaded(
            test_file_name, test_download_urls, test_src_repo, verbose=VERBOSE
        )
        self.assertEqual(downloaded_status, False)
 
        # Downloading file.
        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo, verbose=VERBOSE
        )
        self.assertEqual(download_status, True)
        self.assertEqual(os.path.exists(file_path), True)
        
        # Checking download status after download
        downloaded_status = is_file_downloaded(
            test_file_name, test_download_urls, test_src_repo, verbose=VERBOSE
        )
        self.assertEqual(downloaded_status, True)

        """
        git cloning test
        """
        test_file_name = "MySQL-for-Python-3.git"
        test_download_urls = "https://github.com/gagoel"
        test_src_repo = os.path.join(self.temp_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)
        
        # Checking download status before download
        downloaded_status = is_file_downloaded(
            test_file_name, test_download_urls, test_src_repo, verbose=VERBOSE
        )
        self.assertEqual(downloaded_status, False)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo, verbose=VERBOSE
        )
        self.assertEqual(download_status, True)
        self.assertEqual(os.path.exists(file_path), True)
        
        # Checking download status after download
        downloaded_status = is_file_downloaded(
            test_file_name, test_download_urls, test_src_repo, verbose=VERBOSE
        )
        self.assertEqual(downloaded_status, True)

    def test_is_file_downloaded_remotehost(self):
        """
        tar, tar.gz, tar.bz2 or tar.xz download test.
        """
        test_file_name = "mod_wsgi-3.4.tar.gz"
        test_download_urls = "https://modwsgi.googlecode.com/files"
        test_src_repo = os.path.join(self.temp_remote_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        # Checking download status before download
        downloaded_status = is_file_downloaded(
            test_file_name, test_download_urls,
            test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        self.assertEqual(downloaded_status, False)
 
        # Downloading file.
        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        self.assertEqual(download_status, True)

        check_path_status = is_path_exists(
            file_path, remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual(check_path_status, True)
        
        # Checking download status after download
        downloaded_status = is_file_downloaded(
            test_file_name, test_download_urls, test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        self.assertEqual(downloaded_status, True)

        """
        git cloning test
        """
        test_file_name = "MySQL-for-Python-3.git"
        test_download_urls = "https://github.com/gagoel"
        test_src_repo = os.path.join(self.temp_remote_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)
        
        # Checking download status before download
        downloaded_status = is_file_downloaded(
            test_file_name, test_download_urls, test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        self.assertEqual(downloaded_status, False)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        self.assertEqual(download_status, True)
        
        check_path_status = is_path_exists(
            file_path, remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual(check_path_status, True)
        
        # Checking download status after download
        downloaded_status = is_file_downloaded(
            test_file_name, test_download_urls, test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        self.assertEqual(downloaded_status, True)

    def test_download_file_localhost(self):
        # tar, tar.gz, tar.bz2 or tar.xz download test.
        test_file_name = "mod_wsgi-3.4.tar.gz"
        test_download_urls = "https://modwsgi.googlecode.com/files"
        test_src_repo = os.path.join(self.temp_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo, verbose=VERBOSE
        )
        self.assertEqual(download_status, True)
        self.assertEqual(os.path.exists(file_path), True)

        # git cloning test
        test_file_name = "MySQL-for-Python-3.git"
        test_download_urls = "https://github.com/gagoel"
        test_src_repo = os.path.join(self.temp_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo, verbose=VERBOSE
        )
        self.assertEqual(download_status, True)
        self.assertEqual(os.path.exists(file_path), True)

    def test_download_file_remotehost(self):
        # tar, tar.gz, tar.bz2 or tar.xz download test.
        test_file_name = "mod_wsgi-3.4.tar.gz"
        test_download_urls = "https://modwsgi.googlecode.com/files"
        test_src_repo = os.path.join(self.temp_remote_dir,
            'test-download-file/src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        self.assertEqual(download_status, True)
        
        path_exists = is_path_exists(
            file_path,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        self.assertEqual(path_exists, True)

        # git cloning test
        test_file_name = "MySQL-for-Python-3.git"
        test_download_urls = "https://github.com/gagoel"
        test_src_repo = os.path.join(self.temp_remote_dir,
            'test-download-file/src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        self.assertEqual(download_status, True)
        
        path_exists = is_path_exists(
            file_path,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        self.assertEqual(path_exists, True)
 
    def test_extract_file_localhost(self):
        test_file_name = "mod_wsgi-3.4.tar.gz"
        test_download_urls = "https://modwsgi.googlecode.com/files"
        test_src_repo = os.path.join(self.temp_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo, verbose=VERBOSE
        )
        test_extract_path = os.path.join(self.temp_dir, 'src')
        extracted_file = extract_file(
            test_file_name, test_src_repo, test_extract_path, verbose=VERBOSE
        )

        self.assertEqual(os.path.exists(test_extract_path), True)

    def test_extract_file_remotehost(self):
        test_file_name = "mod_wsgi-3.4.tar.gz"
        test_download_urls = "https://modwsgi.googlecode.com/files"
        test_src_repo = os.path.join(self.temp_remote_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
        test_extract_path = os.path.join(self.temp_remote_dir, 'src')
        extracted_file_path = extract_file(
            test_file_name, test_src_repo, test_extract_path,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )

        extracted_readme = os.path.join(extracted_file_path, 'README')
        path_exists = is_path_exists(
            extracted_file_path,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )

        self.assertEqual(path_exists, True)

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
            test_string_after_resolve, replace_env_vars(
                test_string, verbose=VERBOSE)
        )

        # list type
        test_string = ["$TEST_ENV1/testpath1", "$TEST_ENV2/testpath2"]
        resolve_test_string = replace_env_vars(test_string, verbose=VERBOSE)
        self.assertEqual(resolve_test_string[0], "TEST_ENV1_VALUE/testpath1")
        self.assertEqual(resolve_test_string[1], "TEST_ENV2_VALUE/testpath2")

        # dict type
        test_string = {
            "key1" : ["$TEST_ENV1/testpath1", "$TEST_ENV2/testpath2"]
        }
        resolve_test_string = replace_env_vars(test_string, verbose=VERBOSE)
        self.assertEqual(
            resolve_test_string['key1'][0], "TEST_ENV1_VALUE/testpath1"
        )
        self.assertEqual(
            resolve_test_string['key1'][1], "TEST_ENV2_VALUE/testpath2"
        )
    
    def test_run_command_localhost(self):
        cmd = ['/bin/sh', '-c', 'pwd']
        stdout, stderr = run_command(cmd, verbose=VERBOSE)
        self.assertEqual(stderr, "")

    def test_run_command_remotehost(self):
        temp_dir = os.path.join(self.temp_remote_dir, 'test-run-command')

        mkdirs(
            temp_dir,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        
        # Downloading file and extracting it by running command on remotehost
        test_file_name = "mod_wsgi-3.4.tar.gz"
        test_download_urls = "https://modwsgi.googlecode.com/files"
        test_src_repo = os.path.join(temp_dir, 'src_repo')
        file_path = os.path.join(test_src_repo, test_file_name)

        download_status = download_file(
            test_file_name, test_download_urls, test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=VERBOSE
        )
 
        # There is no assert as it checks if we are getting output while
        # running command in case of verbose > 1
        cmd = ['tar', 'xvf', file_path]
        stdout, stderr = run_command(
            cmd, cmd_exec_dir=test_src_repo,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass,
            verbose=2
        )
        
        cmd = ['pwd']
        stdout, stderr = run_command(
            cmd, cmd_exec_dir=temp_dir,
            remote_host=self.remote_host,
            remote_ssh_port=self.remote_ssh_port,
            remote_ssh_user=self.remote_ssh_user,
            remote_ssh_pass=self.remote_ssh_pass
        )
        self.assertEqual('', stderr)
        self.assertEqual(temp_dir, stdout.strip())

if __name__ == "__main__":
    unittest.main(verbosity=2)
