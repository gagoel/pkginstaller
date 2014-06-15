import os
import sys
import json
import re
import subprocess
import tarfile
import urllib.request
import logging
import paramiko
import stat
import shutil

from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read

logger = logging.getLogger('pkginstaller.setup_utils')

def is_file_downloaded(
    file_name,
    from_location,
    to_location,
    remote_host='localhost',
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0
):
    """Checks file downloaded or not at given location on localhost or
       remotehost.

    Args:
        file_name (str): File name which will download.
        from_location (str): URL to download file.
        to_location (str): Directory path where file will be save.
        remote_host (str): Remote host address if to_location is not local.
        remote_ssh_port (int): Remote host SSH port.
        remote_ssh_user (str): Remote host SSH User name.
        remote_ssh_pass (str): Remote host SSH Password.

    Returns:
        bool: True if file found otherwise False
        
    """
    def _is_file_exist_on_localhost(file_name, from_location, to_location):
        from_file = os.path.join(from_location, file_name)
        to_file = os.path.join(to_location, file_name)
        
        if os.path.exists(to_file):
            logger.info('File exists at %s, checking file size', to_file)

            response = urllib.request.urlopen(from_file)
            remote_file_size = response.headers['Content-Length'].strip()

            statinfo = os.stat(to_file)
            if int(remote_file_size) == statinfo.st_size:
                logger.info('File size %s matches at remote location, '\
                    'skipping download', remote_file_size
                )
                response.close()
                return True
            else:
                logger.info(
                    'Remote file size %s does not match with local file size '
                    '%s', remote_file_size, str(statinfo.st_size)
                )
                
        return False

    def _is_file_exist_on_remotehost(
        file_name, from_location, to_location, remote_host,
        remote_ssh_port, remote_ssh_user, remote_ssh_pass
    ):
        from_file = os.path.join(from_location, file_name)
        to_file = os.path.join(to_location, file_name)
        
        t = paramiko.Transport((remote_host, remote_ssh_port))
        t.connect(username=remote_ssh_user, password=remote_ssh_pass)
        sftp = paramiko.SFTPClient.from_transport(t)
            
        response = urllib.request.urlopen(from_file)
        remote_file_size = response.headers['Content-Length'].strip()
        
        statinfo = None
        try:
            statinfo = sftp.stat(to_file)
        except FileNotFoundError:
            response.close()
            sftp.close()
            return False
            
        if int(remote_file_size) == statinfo.st_size:
            logger.info('File size %s matches at remote location, '\
                'skipping download', remote_file_size
            )
            response.close()
            sftp.close()
            return True
        
        response.close()
        sftp.close()
        return False

    def _is_git_repo_exist_on_localhost(file_name, from_location, to_location):
        git_repo = os.path.join(to_location, file_name, '.git')

        if os.path.exists(git_repo):
            logger.info('Git repository exists at %s', git_repo)
            return True
        else:
            logger.info('Git repository does not exist at %s', git_repo)
            return False

    def _is_git_repo_exist_on_remotehost(
        file_name, from_location, to_location, remote_host,
        remote_ssh_port, remote_ssh_user, remote_ssh_pass
    ):
        git_repo = os.path.join(to_location, file_name, '.git')
        
        try:
            t = paramiko.Transport((remote_host, remote_ssh_port))
            t.connect(username=remote_ssh_user, password=remote_ssh_pass)
            sftp = paramiko.SFTPClient.from_transport(t)
            sftp.stat(git_repo)
            sftp.close()
        except FileNotFoundError:
            logger.info('Git repo %s does not exist.', git_repo)
            return False
        else:
            logger.info('Git repo %s found in cache', git_repo)
            return True

    # Main code
    if remote_host == "localhost" or remote_host == "127.0.0.1":
        if re.match('.*\.git$', file_name):
            return _is_git_repo_exist_on_localhost(
                file_name, from_location, to_location
            )
        else:
            return _is_file_exist_on_localhost(
                file_name, from_location, to_location
            )
    else:
        if re.match('.*\.git$', file_name):
            return _is_git_repo_exist_on_remotehost(
                file_name, from_location, to_location, remote_host,
                remote_ssh_port, remote_ssh_user, remote_ssh_pass
            )
        else:
            return _is_file_exist_on_remotehost(
                file_name, from_location, to_location, remote_host,
                remote_ssh_port, remote_ssh_user, remote_ssh_pass
            )

def download_file(
    file_name,
    from_location,
    to_location,
    remote_host='localhost',
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0
):
    """Download file and save it to destination on localhost or remotehost

    Args:
        file_name (str): File name which will download.
        from_location (str): URL to download file.
        to_location (str): Directory path where file will be save.
        remote_host (str): Remote host address if to_location is not local.
        remote_ssh_port (int): Remote host SSH port.
        remote_ssh_user (str): Remote host SSH User name.
        remote_ssh_pass (str): Remote host SSH Password.

    Returns:
        bool: True if file was successfully downloaded otherwise False
        
    """
  
    logger.debug(
        'Downloading file %s from location %s and installing to host %s to'
        ' location %s', file_name, from_location, remote_host, to_location
    )
    
    def _print_downloading_message(bytes_so_far, chunk_size, total_size):
        downloaded_size = float(bytes_so_far) / total_size
        downloaded_percentage = round(downloaded_size*100, 2)
        print("Downloaded {} of {} bytes {}%\r".format(
            bytes_so_far, total_size, downloaded_percentage), end=''
        )
        #sys.stdout.flush()
        if bytes_so_far >= total_size:
            print('\n')

    def _download_file_to_localhost(
        file_name, from_location, to_location,
        chunk_size=8192, report_hook=None
    ):
        from_file = os.path.join(from_location, file_name)
        response = urllib.request.urlopen(from_file)
        total_size = int(response.headers['Content-Length'].strip())
        
        bytes_so_far = 0

        logger.info('Total file size is %s', total_size)
        to_file = os.path.join(to_location, file_name)

        # Checks file in cache.
        if _is_file_exist_at_localhost(from_file, to_file):
            logger.info('File found in cache.')
            return total_size

        # Creating parent dirs, if does not exists.
        if not os.path.exists(to_location):
            os.makedirs(to_location)

        if verbose > 0:
            #Adding newline before printing downloaded message.
            print('\n', end='')
        write_file_handler = open(to_file, "wb")
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            
            bytes_so_far += len(chunk)
            write_file_handler.write(chunk)
            write_file_handler.flush()

            if report_hook and verbose > 0:
                report_hook(
                    bytes_so_far, chunk_size, total_size
                )

        write_file_handler.close()
        response.close()
        logger.info('Total bytes written to file is %s', bytes_so_far)
        return bytes_so_far
    
    def _download_file_to_remotehost(
        file_name, from_location, to_location, remote_host, remote_ssh_port,
        remote_ssh_user, remote_ssh_pass, chunk_size=8192, report_hook=None
    ):
        from_file = os.path.join(from_location, file_name)
        response = urllib.request.urlopen(from_file)
        total_size = int(response.headers['Content-Length'].strip())
        bytes_so_far = 0

        logger.info('Total file size is %s', total_size)
       
        to_file = os.path.join(to_location, file_name)

        # Checks file in cache.
        if _is_file_exist_at_remotehost(from_file, to_file, remote_host,
            remote_ssh_port, remote_ssh_user, remote_ssh_pass
        ):
            logger.info('File found in cache.')
            return total_size

        t = paramiko.Transport((remote_host, remote_ssh_port))
        t.connect(username=remote_ssh_user, password=remote_ssh_pass)
        sftp = paramiko.SFTPClient.from_transport(t)
        
        # Creating parent dirs, if does not exists.
        logger.info('Creating %s directory if does not exist', to_location)
        mkdirs(to_location, remote_host=remote_host,
            remote_ssh_port=remote_ssh_port, remote_ssh_user=remote_ssh_user,
            remote_ssh_pass=remote_ssh_pass, failsafe=False
        )
        
        sftp.chdir(path=to_location) 
        write_file_handler = sftp.open(file_name, "wb")
        
        if verbose > 0:
            #Adding newline before printing downloaded message.
            print('\n', end='')
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            
            bytes_so_far += len(chunk)
            write_file_handler.write(chunk)

            if report_hook and verbose > 0:
                report_hook(
                    bytes_so_far, chunk_size, total_size
                )

        write_file_handler.close()
        response.close()
        sftp.close()
        
        logger.info('Total bytes written to file is %s', bytes_so_far)
        return bytes_so_far

    def _download_git_repo_to_localhost(
        file_name, from_location, to_location
    ):
        git_repo_dir = os.path.join(to_location, file_name)

        logger.info(
            'Cloning git repository %s to location %s',
            from_location, to_location
        )
      
        # Creating parent directories if not exists.
        if not os.path.exists(to_location):
            os.makedirs(to_location)
        
        from_file = os.path.join(from_location, file_name) 
        cloning_cmd = ["git", "clone", from_file, file_name]
        stdout, stderr = run_command(
            cloning_cmd, to_location, verbose=verbose+1
        )
        
        logger.debug('Git Cloning output %s', stdout)
        if stderr != "":
            logger.info('\n%s', stderr)
            return False
        
        logger.info('Git repository cloned successfully.')    
        return True

    def _download_git_repo_to_remotehost(
        file_name, from_location, to_location, remote_host, remote_ssh_port,
        remote_ssh_user, remote_ssh_pass
    ):
        client = paramiko.SSHClient()
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.WarningPolicy())
        client.connect(remote_host, remote_ssh_port, remote_ssh_user,
            remote_ssh_pass)
        
        to_file = os.path.join(to_location, file_name)
        mkdirs(to_file, remote_host=remote_host,
            remote_ssh_port=remote_ssh_port, remote_ssh_user=remote_ssh_user,
            remote_ssh_pass=remote_ssh_pass, failsafe=False
        )

        from_file = os.path.join(from_location, file_name)
        cloning_cmd = "git clone " + from_file + " " + to_file
        
        logger.info(
            'Cloning git repository %s to remotehost %s to location %s, '
            'cloning command %s',
            from_location, remote_host, to_location, cloning_cmd
        )
        
        stdin, stdout, stderr = client.exec_command(cloning_cmd)
        client.close()
        
        stdout_str = ""
        stderr_str = ""
        for line in stdout:
            stdout_str += line.strip()
        for line in stderr:
            stderr_str += line.strip()
            
        logger.debug('Git Cloning output - %s', stdout_str)

        if "ERROR" in stderr_str or "Error" in stderr_str:
            logger.error('Git cloning error - \n%s', stderr_str)
            return False
        
        logger.info('Git repository cloned successfully.')    
        return True

    def _is_file_exist_at_localhost(from_file, to_file):
        if os.path.exists(to_file):
            logger.info('File exists at %s, checking file size', to_file)

            response = urllib.request.urlopen(from_file)
            remote_file_size = response.headers['Content-Length'].strip()

            statinfo = os.stat(to_file)
            if int(remote_file_size) == statinfo.st_size:
                logger.info('File size %s matches at remote location, '\
                    'skipping download', remote_file_size
                )
                response.close()
                return True
            else:
                logger.info(
                    'Remote file size %s does not match with local file size '
                    '%s', remote_file_size, str(statinfo.st_size)
                )
                
        return False

    def _is_file_exist_at_remotehost(from_file, to_file, remote_host,
        remote_ssh_port, remote_ssh_user, remote_ssh_pass
    ):
        t = paramiko.Transport((remote_host, remote_ssh_port))
        t.connect(username=remote_ssh_user, password=remote_ssh_pass)
        sftp = paramiko.SFTPClient.from_transport(t)
            
        response = urllib.request.urlopen(from_file)
        remote_file_size = response.headers['Content-Length'].strip()
        
        statinfo = None
        try:
            statinfo = sftp.stat(to_file)
        except FileNotFoundError:
            response.close()
            sftp.close()
            return False
            
        if int(remote_file_size) == statinfo.st_size:
            logger.info('File size %s matches at remote location, '\
                'skipping download', remote_file_size
            )
            response.close()
            sftp.close()
            return True
        
        response.close()
        sftp.close()
        return False
    
    # Main code
    status = False
    if remote_host == "localhost" or remote_host == "127.0.0.1":
        if re.match('.*\.git$', file_name):
            status = _download_git_repo_to_localhost(
                file_name, from_location, to_location
            )
        else:
            status = _download_file_to_localhost(
                file_name, from_location, to_location,
                report_hook=_print_downloading_message
            )
    else:
        if re.match('.*\.git$', file_name):
            status = _download_git_repo_to_remotehost(
                file_name, from_location, to_location, remote_host,
                remote_ssh_port, remote_ssh_user, remote_ssh_pass
            )
        else:
            status = _download_file_to_remotehost(
                file_name, from_location, to_location, remote_host,
                remote_ssh_port, remote_ssh_user, remote_ssh_pass,
                report_hook=_print_downloading_message
            )

    if status:
        logger.info('%s file downloaded successfully.', file_name)
        return True
    else:
        logger.error('file download failed %s', file_name)
        return False

def extract_file(
    file_name,
    file_source_path,
    file_dest_path,
    remote_host="localhost",
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0
):
    """ Extract file and returns the path where it was extracted.
    
    Args:
        file_name (str): File name which will be extracted.
        file_source_path (str): Source directory path where file exist.
        file_dest_path (str): Destination directory path where file will be
            extracted. 
        remote_host (str): Remote host address if to_location is not local.
        remote_ssh_port (int): Remote host SSH port.
        remote_ssh_user (str): Remote host SSH User name.
        remote_ssh_pass (str): Remote host SSH Password.

    Returns:
        str: Directory path where file has extracted.
          
    """ 
   
    logger.info(
        'Extracting file %s from location %s to location %s on host %s',
        file_name, file_source_path, file_dest_path, remote_host
    ) 
    # Checks that input file is supported archive file or not.
    supported_archive_re_pattern = \
        '.*(\.git|\.zip|\.tar|\.tar\.bz2|\.tar\.gz|\.tar\.xz)$' 
    if re.match(supported_archive_re_pattern, file_name) == None:
        raise Exception(
            'File ' + file_name + ' is not a supported archive file. ' +
            'Supported archives are git, tar, tar.bz2, tar.gz and tar.xz'
        )

    # Getting file name without extension
    file_name_without_ext = re.sub(
        '(\.git|\.tar|\.tar\.bz2|\.tar\.gz|\.tar\.xz)$', '', file_name
    )
    file_dest_path_without_ext = os.path.join(
        file_dest_path, 
        file_name_without_ext
    )
    file_abs_path = os.path.join(file_source_path, file_name)

    # If it is git repository then just copy to extract location.
    if re.match('.*\.git$', file_name):
        logger.info('git repository - copying to extract location.')
        if not is_path_exists(file_dest_path_without_ext, remote_host,
            remote_ssh_port, remote_ssh_user, remote_ssh_pass
        ):
            os.makedirs(file_dest_path_without_ext, remote_host,
                remote_ssh_port, remote_ssh_user, remote_ssh_pass)
        
        copy_cmd = ['bash', '-c', 'cp -rfv ' + file_abs_path + '/* ' + \
            file_dest_path_without_ext]
        
        stdout, stderr = run_command(
            copy_cmd,
            remote_host=remote_host,
            remote_ssh_port=remote_ssh_port,
            remote_ssh_user=remote_ssh_user,
            remote_ssh_pass=remote_ssh_pass,
            verbose=verbose
        )
        
        if stderr != "":
            raise Exception('Error in extracting git repo.')
            
        logger.info(
            'Copied git repository successfully to extraction location %s.',
            file_dest_path_without_ext
        ) 
        return file_dest_path_without_ext
    
    def _get_extract_command(file_name, file_abs_path):
        pattern_command = {
            '.*\.zip$': ['unzip', file_abs_path],    
            '.*\.tar$': ['tar', 'xvf', file_abs_path],
            '.*\.tar\.bz2$': ['tar', 'xvjf', file_abs_path],
            '.*\.tar\.gz$': ['tar', 'xvzf', file_abs_path],
            '.*\.tar\.xz$': ['tar', 'xvJf', file_abs_path]
        }
        for key, value in pattern_command.items():
            if re.match(key, file_name):
                return value
        return None
    
    if not is_path_exists(
        file_dest_path,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    ):
        mkdirs(
            file_dest_path,
            remote_host=remote_host,
            remote_ssh_port=remote_ssh_port,
            remote_ssh_user=remote_ssh_user,
            remote_ssh_pass=remote_ssh_pass,
            verbose=verbose,
            failsafe=False
        )
     
    # If file is compressed tar file or zip file.
    unzip_cmd = _get_extract_command(file_name, file_abs_path)
    stdout, stderr = run_command(
        unzip_cmd,
        file_dest_path,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    )
    if stderr != "":
        raise Exception('Error in extracting file - {}'.format(stderr))
    logger.info('File has extracted successfully at %s', file_dest_path)
    return file_dest_path_without_ext

def replace_env_vars(replacing_data, verbose=0):

    def _replace_env_vars(replaced_data):
        env_dict = os.environ
        for env_key, env_value in env_dict.items():
            re_pattern = "\$" + env_key
            replaced_data = re_replace(
                re_pattern, env_value, replaced_data, verbose=verbose
            )
        return replaced_data

    def _recursive_replace_env_vars(replaced_data):
        if type(replaced_data) is bool:
            return replaced_data
        elif type(replaced_data) is int:
            return replaced_data
        elif type(replaced_data) is str:
            return _replace_env_vars(replaced_data)
        elif type(replaced_data) is list:
            for index, item in enumerate(replaced_data):
                replaced_data[index] = _recursive_replace_env_vars(item)
            return replaced_data
        elif type(replaced_data) is dict:
            for key, value in replaced_data.items():
                replaced_data[key] = _recursive_replace_env_vars(value)
            return replaced_data
        else:
            raise Exception(
                'Object type is not supported {}'.format(type(replaced_data))
            )
    
    replaced_data = replacing_data
    logger.debug('Replacing environment variables')
    replaced_data = _recursive_replace_env_vars(replaced_data)
     
    logger.debug(
        'Replaced environment variables \n Before replacement string \n%s' + \
        '\nAfter replacement string \n%s',
        replacing_data, replaced_data
    ) 
    
    return replaced_data

def re_replace(pattern, replacement, string, verbose=0):
    p = re.compile(pattern)
    return p.sub(replacement, string)

def run_command(
    cmd_args_list,
    cmd_exec_dir=os.getcwd(),
    background=False,
    shell=False,
    remote_host="localhost",
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0
):
    
    logger.debug(
        'Executing command - \n%s \nfrom location - %s\n',
        " ".join(cmd_args_list),
        cmd_exec_dir
    )

    if remote_host == "localhost" or remote_host == "127.0.0.1":
        if background == True:
            proc = subprocess.Popen(
                cmd_args_list,
                stderr=subprocess.PIPE,
                cwd=cmd_exec_dir,
                shell=shell
            )
            return proc

        proc = subprocess.Popen(
            cmd_args_list,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cmd_exec_dir,
            shell=shell
        )

        flags = fcntl(proc.stdout, F_GETFL)
        fcntl(proc.stdout, F_SETFL, flags | O_NONBLOCK)
        flags = fcntl(proc.stderr, F_GETFL)
        fcntl(proc.stderr, F_SETFL, flags | O_NONBLOCK)

        stdout = ""
        stderr = ""
        while proc.poll() is None:
            try:
                line = read(proc.stdout.fileno(), 1024)
                if line:
                    if verbose > 1:
                        print(line.decode('utf-8'), end="")
                    stdout += line.decode('utf-8')
                line = read(proc.stderr.fileno(), 1024)
                if line:
                    if verbose > 1:
                        print(line.decode('utf-8'), end="")
                    stderr += line.decode('utf-8')
            except OSError:
                pass

        sys.stdout.flush()
        sys.stdin.flush()
        proc.stdin.close()
        proc.stdout.close()
        proc.stderr.close()
        
        logger.debug(
            'Command %s \nOutput is\n%s \nError is\n%s',
            " ".join(cmd_args_list), stdout, stderr
        )
        return stdout, stderr
    else:
        try:
            change_dir_cmd = "cd " + cmd_exec_dir
            cmd_str = change_dir_cmd + "; " + " ".join(cmd_args_list)
            
            if background:
                cmd_str += " &"

            t = paramiko.Transport((remote_host, remote_ssh_port))
            t.connect(username=remote_ssh_user, password=remote_ssh_pass)
            chan = t.open_session()
            chan.get_pty()
            chan.settimeout(None)
            chan.exec_command(cmd_str)
          
            stdout_str = ""
            stderr_str = ""
            
            while not chan.exit_status_ready() or chan.recv_ready() or \
                chan.recv_stderr_ready():

                if chan.recv_ready():
                    logger.debug('Writing to stdout stream...')
                    stdout_line = chan.recv(1024).decode('utf-8')
                    if verbose > 1:
                        print(stdout_line, end="")
                    stdout_str += stdout_line

                if chan.recv_stderr_ready():
                    logger.debug('Writing to stderr stream...')
                    stderr_line = chan.recv_stderr(1024).decode('utf-8')
                    if verbose > 1:
                        print(stderr_line, end="")
                    stderr_str += stderr_line
            
            t.close() 
            chan.close()
            return stdout_str, stderr_str

        except Exception as e:
            raise

def wget_ftp_download(
    host,
    username,
    password,
    srcdir,
    destdir,
    remote_host="localhost",
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0
):
    url_str = 'ftp://' + username + ':' + password + '@' + host + '/' + srcdir 
    wget_cmd = ['wget', '-r', url_str, '--no-host-directories']

    if not is_path_exists(
        destdir, remote_host, remote_ssh_port, remote_ssh_user, remote_ssh_pass
    ):
        mkdirs(destdir, remote_host, remote_ssh_port, remote_ssh_user,
            remote_ssh_pass, failsafe=False)

    stdout, stderr = run_command(
        wget_cmd, destdir,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    )
    if stderr != "":
        logger.error('Error in downloading ftp file %s', stderr)
        return False
    else:
        logger.info('FTP download was successful.')

    return True

def apply_patch(
    patch_file,
    dest_dir,
    remote_host="localhost",
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0
):
    logger.info("Applying patch %s from directory %s", patch_file, dest_dir)

    if not is_path_exists(
        patch_file, remote_host, remote_ssh_port, remote_ssh_user,
        remote_ssh_pass
    ):
        raise Exception('patch file %s does not exists', patch_file)

    cmd = ["patch", "-p1", "--input=" + patch_file]
    stdout, stderr = run_command(
        cmd, dest_dir,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    )

    if stderr != "":
        raise Exception(
            'patch %s execution failed from %s directory',
            patch_file, dest_dir
        )

def is_path_exists(
    file_path,
    remote_host="localhost",
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0,
    failsafe=True
):
    if remote_host == "localhost" or remote_host == "127.0.0.1":
        return os.path.exists(file_path)
    else:
        try:
            t = paramiko.Transport((remote_host, remote_ssh_port))
            t.connect(username=remote_ssh_user, password=remote_ssh_pass)
            sftp = paramiko.SFTPClient.from_transport(t)
            sftp.stat(file_path)
            sftp.close()
            return True
        except OSError:
            if failsafe:
                logger.info('Path does not exists %s', file_path)
                return False
            else:
                raise Exception('Path does not exists {}'.format(file_path))

def mkdirs(
    dir_path,
    mode=0o755,
    remote_host="localhost",
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0,
    failsafe=False
):
    try:
        if remote_host == "localhost" or remote_host == "127.0.0.1":
            os.makedirs(dir_path, mode=mode)
        else:
            t = paramiko.Transport((remote_host, remote_ssh_port))
            t.connect(username=remote_ssh_user, password=remote_ssh_pass)
            sftp = paramiko.SFTPClient.from_transport(t)
    
            path_list = dir_path.split('/')
            curr_path = "/"
            for each_dir in path_list:
                if not each_dir:
                    continue
                sftp.chdir(curr_path)
                curr_path = os.path.join(curr_path, each_dir)
                logger.debug('Creating directory %s', curr_path)
                try:
                    sftp.stat(curr_path)
                except OSError:
                    sftp.mkdir(each_dir, mode=mode)
            sftp.close()
    except Exception as e:
        if failsafe:
            logger.error('Error in creating directory %s on host %s, '
                'excpetion is %s', dir_path, remote_host, e)
            return False
        else:
            raise RuntimeError(
                'Error in creating directory {} on host {}, exception is {}'
                .format(dir_path, remote_host, e)
            )

    return True

def create_file(
    file_path,
    file_data,
    remote_host="localhost",
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0,
    failsafe=False
):
    try:
        if remote_host == "localhost" or remote_host == "127.0.0.1":
            with open(file_path, mode='w+') as f:
                f.write(file_data)
                f.close()
                pass
        else:
            t = paramiko.Transport((remote_host, remote_ssh_port))
            t.connect(username=remote_ssh_user, password=remote_ssh_pass)
            sftp = paramiko.SFTPClient.from_transport(t)
            fd = sftp.open(file_path, mode='w+')
            fd.write(file_data)
            sftp.close()
    except Exception as e:
        if failsafe:
            logger.error('File Creation Failed %s', e)
            return False
        else:
            raise Exception('File creation failed {}'.format(e))

    return True
    
def remove_file(
    file_path,
    remote_host="localhost",
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0,
    failsafe=False
):
    try:
        if remote_host == "localhost" or remote_host == "127.0.0.1":
            os.remove(file_path)
        else:
            t = paramiko.Transport((remote_host, remote_ssh_port))
            t.connect(username=remote_ssh_user, password=remote_ssh_pass)
            sftp = paramiko.SFTPClient.from_transport(t)
            sftp.remove(file_path)
            sftp.close()
    except Exception as e:
        if failsafe:
            logger.error('Removing file %s on host %s operation failed %s',
                file_path, remote_host, e)
            return False
        else:
            raise Exception('Removing file {} on host {} operation failed {}'
                .format(file_path, remote_host, e)
            )

    return True

def remove_dir(
    dir_path,
    remote_host="localhost",
    remote_ssh_port=22,
    remote_ssh_user=None,
    remote_ssh_pass=None,
    verbose=0,
    failsafe=False
):
    def _remove_dirs_remotehost(dir_path, sftp_obj):
        names = sftp_obj.listdir(path=dir_path)
        for name in names:
            fullname = os.path.join(dir_path, name)
            try:
                mode = sftp_obj.lstat(fullname).st_mode
            except:
                mode = 0
            if stat.S_ISDIR(mode):
                _remove_dirs_remotehost(fullname, sftp_obj)
            else:
                sftp_obj.remove(fullname)
        sftp_obj.rmdir(dir_path)

    try:
        if remote_host == "localhost" or remote_host == "127.0.0.1":
            shutil.rmtree(dir_path)
        else:
            t = paramiko.Transport((remote_host, remote_ssh_port))
            t.connect(username=remote_ssh_user, password=remote_ssh_pass)
            sftp = paramiko.SFTPClient.from_transport(t)
            _remove_dirs_remotehost(dir_path, sftp)
            sftp.close()
    except Exception as e:
        if failsafe:
            logger.error('Removing dir %s on host %s operation failed %s',
                dir_path, remote_host, e)
            return False
        else:
            raise Exception('Removing dir {} on host {} operation failed {}'
                .format(dir_path, remote_host, e)
            )

    return True

from timeit import default_timer

class Timer:
    def __init__(self, verbose=0):
        self.verbose = verbose
        self.timer = default_timer

    def start(self):
        self.start = self.timer()
        return self

    def stop(self):
        end = self.timer()
        self.elapsed_secs = end - self.start
        self.elapsed = self.elapsed_secs * 1000  # millisecs
        if self.verbose > 0:
            print('Elapsed Time: {} secs'.format(self.elapsed_secs))

