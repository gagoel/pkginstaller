#!/usr/bin/python

import os 
import unittest

VERBOSE = 0

from test_install_packages import *
from test_setup_packages import *
from test_setup_utils import *
# good utility to debug deadlock in threads
#import stacktracer 
 
if __name__ == "__main__":
    #all_tests = unittest.TestLoader().discover('tests', pattern='*.py')
    #unittest.TextTestRunner(verbosity=2).run(all_tests)
    #stacktracer.trace_start('trace.html')
    
    
    # Setting required environment variables.
    public_repo_root = input('\nEnter public repo root : ')
    remote_host = input('Enter test remote host ip address [192.168.1.104] : ')
    remote_host_ssh_port = input('Enter test remote host ssh port [22] : ')
    remote_host_ssh_user = input('Enter test remote host ssh user : ')
    remote_host_ssh_pass = input('Enter test remote host ssh password : ')
    remote_host_temp_dir = input('Enter test remote host temp dir : ') 

    os.environ['DEV_SERVER_PUBLIC_REPO_ROOT'] = public_repo_root
    os.environ['REMOTE_HOST_IP'] = remote_host or "192.168.1.104"
    os.environ['REMOTE_HOST_SSH_PORT'] = remote_host_ssh_port or "22"
    os.environ['REMOTE_HOST_SSH_USER'] = remote_host_ssh_user
    os.environ['REMOTE_HOST_SSH_PASS'] = remote_host_ssh_pass
    os.environ['REMOTE_HOST_TEMP_DIR'] = remote_host_temp_dir

    print('') 
    unittest.main(verbosity=2)
