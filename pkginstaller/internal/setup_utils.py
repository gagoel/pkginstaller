import os
import sys
import json
import re
import subprocess
import tarfile
import urllib.request
import logging

from fcntl import fcntl, F_GETFL, F_SETFL
from os import O_NONBLOCK, read

logger = logging.getLogger('pkginstaller.setup_utils')


def download_file(file_name, from_location, to_location, verbose=False):
    """Download file and save it to destination

    Args:
        file_name (str): File name which will download.
        from_location (str): URL to download file.
        to_location (str): Directory path where file will be save.

    Returns:
        bool: True if file was successfully downloaded otherwise False
        
    """
  
    logger.debug(
        'Downloading file %s from location %s to location %s',
        file_name, from_location, to_location
    )
    
    def download_file_report(bytes_so_far, chunk_size, total_size):
        downloaded_size = float(bytes_so_far) / total_size
        downloaded_percentage = round(downloaded_size*100, 2)
        sys.stdout.write("Downloaded {} of {} bytes {}%\r".format(
            bytes_so_far, total_size, downloaded_percentage)
        )
        sys.stdout.flush()
        if bytes_so_far >= total_size:
            print('\n')

    def download_file_read(
        write_file_path, response, chunk_size=8192, report_hook=None
    ):
        total_size = response.headers['Content-Length'].strip()
        total_size = int(total_size)
        bytes_so_far = 0

        logger.debug('Total file size is %s', total_size)
        write_file_handler = open(write_file_path, "wb")
        while True:
            chunk = response.read(chunk_size)
            if not chunk:
                break
            
            bytes_so_far += len(chunk)
            write_file_handler.write(chunk)
            write_file_handler.flush()

            if report_hook:
                download_file_report(bytes_so_far, chunk_size, total_size)

        write_file_handler.close()
        logger.debug('Total bytes written to file is %s', bytes_so_far)
        return bytes_so_far
    
    from_file_path = os.path.join(from_location, file_name)
    to_file_path = os.path.join(to_location, file_name)
    if not os.path.exists(to_location):
        os.makedirs(to_location)

    # git cloning. 
    if re.match('.*\.git$', file_name):
        if os.path.exists(to_file_path):
            print('Git repository exists at {}'.format(to_file_path))
            return True
        else:
            print('Git repository does not exist at {}'.format(to_file_path))
            print(
                'Cloning git repository {} to location {}'.format(
                from_file_path, to_file_path)
            )
         
        cloning_cmd = ["git", "clone", from_file_path, file_name]
        stdout, stderr = run_command(cloning_cmd, to_location)
        
        print('Git Cloning output {}'.format(stdout))
        if stderr != "":
            print('Git cloning error {}'.format(stderr))
            return False
        
        print('Git repository cloned successfully.')    
        return True

    # zip, tar.gz, tar.bz2, tar.xz files downloading.
    response = urllib.request.urlopen(from_file_path)
    
    # Checking file exists or not.
    if os.path.exists(to_file_path):
        print('File exists at {}, checking file size'.format(to_file_path))
        remote_file_size = response.headers['Content-Length'].strip()
        statinfo = os.stat(to_file_path)
        if int(remote_file_size) == statinfo.st_size:
            print('File size {} matches at remote location, '\
                'skipping download'.format(remote_file_size)
            )
            response.close()
            return True
        else:
            print(
                'Remote file size {} does not match with local file size {}'. \
                format(remote_file_size, str(statinfo.st_size))
            )
    
    download_file_read(
        to_file_path, response, report_hook=download_file_report
    )

    response.close()
    print('{} file downloaded successfully.'.format(from_file_path))
    return True

def extract_file(file_name, file_source_path, file_dest_path):
    """ Extract file and returns the path where it was extracted.
    
    Args:
        file_name (str): File name which will be extracted.
        file_source_path (str): Source directory path where file exist.
        file_dest_path (str): Destination directory path where file will be
            extracted. 

    Returns:
        str: Directory path where file has extracted.
          
    """ 
   
    logger.info(
        'Extracting file %s from location %s to location %s',
        file_name, file_source_path, file_dest_path
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
        if not os.path.exists(file_dest_path_without_ext):
            os.makedirs(file_dest_path_without_ext)
        
        copy_cmd = ['bash', '-c', 'cp -rfv ' + file_abs_path + '/* ' + \
            file_dest_path_without_ext]
        
        stdout, stderr = run_command(copy_cmd)
        
        if stderr != "":
            raise Exception('Error in extracting git repo.')
            
        logger.info(
            'Copied git repository successfully to extraction location %s.',
            file_dest_path_without_ext
        ) 
        return file_dest_path_without_ext
    
    # If it is zip file, run the unzip command
    if re.match('.*\.zip$', file_name):
        unzip_cmd = ['unzip', file_abs_path]
        stdout, stderr = run_command(unzip_cmd, file_dest_path)
        if stderr != "":
            raise Exception('Error in unzip file.')
        logger.info('File unzipped successfully at %s', file_dest_path)
        return file_dest_path_without_ext

    try: 
        tar = tarfile.open(file_abs_path)
        tar.extractall(path=file_dest_path)
        tar.close()
    except Exception as e:
        print('Error in file extraction ' + file_name)
        raise e

    logger.info(
        'File has extracted successfully to %s', file_dest_path_without_ext
    )
    return file_dest_path_without_ext

def replace_env_vars(replacing_data):

    def _replace_env_vars(replaced_data):
        env_dict = os.environ
        for env_key, env_value in env_dict.items():
            re_pattern = "\$" + env_key
            replaced_data = re_replace(re_pattern, env_value, replaced_data)
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

def re_replace(pattern, replacement, string):
    p = re.compile(pattern)
    return p.sub(replacement, string)

def run_command(cmd_args_list, cmd_exec_dir=os.getcwd(), background=False, 
    shell=False):
    
    logger.debug(
        'Executing command - \n%s \nfrom location - %s\n',
        " ".join(cmd_args_list),
        cmd_exec_dir
    )

    if background == True:
        subprocess.Popen(
            cmd_args_list,
            stderr=subprocess.PIPE,
            cwd=cmd_exec_dir,
            shell=shell
        )
        return "", ""

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
                if logger.getEffectiveLevel() <= 10:
                    print(line.decode('utf-8'), end="")
                stdout += line.decode('utf-8')
            line = read(proc.stderr.fileno(), 1024)
            if line:
                if logger.getEffectiveLevel() <= 10:
                    print(line.decode('utf-8'), end="")
                stderr += line.decode('utf-8')
        except OSError:
            pass

    sys.stdout.flush()
    sys.stdin.flush()
    proc.stdin.close()
    proc.stdout.close()
    proc.stderr.close()
    #print(stderr)
    if re.match('.*(Error|ERROR|error)', stderr) == None:
        stderr = ""

    logger.debug(
        'Command %s \nOutput is\n%s \nError is\n%s',
        " ".join(cmd_args_list), stdout, stderr
    )
    return stdout, stderr

def wget_ftp_download(host, username, password, srcdir, destdir):
    
    url_str = 'ftp://' + username + ':' + password + '@' + host + '/' + srcdir 
    wget_cmd = ['wget', '-r', url_str, '--no-host-directories']

    if not os.path.exists(destdir):
        os.makedirs(destdir)

    stdout, stderr = run_command(wget_cmd, destdir)
    if stderr != "":
        logger.error('Error in downloading ftp file %s', stderr)
        return False
    else:
        logger.info('FTP download was successful.')

    return True

def apply_patch(patch_file, dest_dir):
    logger.info("Applying patch %s from directory %s", patch_file, dest_dir)

    if not os.path.exists(patch_file):
        raise Exception('patch file %s does not exists', patch_file)

    cmd = ["patch", "-p1", "--input=" + patch_file]
    stdout, stderr = run_command(cmd, dest_dir)

    if stderr != "":
        raise Exception(
            'patch %s execution failed from %s directory',
            patch_file, dest_dir
        )
