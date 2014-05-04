import os
import subprocess
import re
import logging

from pkginstaller.internal.setup_utils import *

logger = logging.getLogger('pkginstaller.setup_package')


class SetupPackage:

    """
    Package configuration dictionary keys:
    name                   - Package name string.
    file_name              - Package file name string.
    urls                   - Package download urls array.
    build_type             - Package build type such as make, distutils.
    
    cache_directory        - Package cache location, save after download.
    extract_root           - Package extract directory.
    build_root             - Package build directory.
    install_root           - Package install directory.
    
    configure_args         - Package configuration arguments array.
    patches                - Package patches files array.
    pre_install_scripts    - Package pre install scripts array.
    post_install_scripts   - Package post install scripts array.
    install_check_files    - Package installed files array to verify package 
                             installation
    install_check_cmds     - Array of command and its expected output, to check
                             that package has installed correctly or not.
    config_files           - Package configuration files source and 
                             destination dict array. 
    configure_cmd          - package configure command string, if default 
                             package configure command is not right as per
                             package build type.
    """
    
    def __init__(
        self,
        package_config_dict,
        package_cache_default_dir,
        package_extract_default_root,
        package_build_default_root,
        package_install_default_root
    ):
        logger.debug(
            'Package configuration dictionary is %s',
            package_config_dict
        )
        
        if not 'name' in package_config_dict.keys():
            raise ValueError(
                'Package configuration dictionary missing "name" key which ' \
                'is required.'
            )
        else:
            self.package_name = package_config_dict['name']

        if not 'file_name' in package_config_dict.keys():
            raise ValueError(
                'Package configuration dictionary missing "file_name" key ' \
                'which is required.'
            )
        else:
            self.package_file_name = package_config_dict['file_name']
        
        if not 'urls' in package_config_dict.keys():
            raise ValueError(
                'Package configuration dictionary missing "urls" key ' \
                'which is required.'
            )
        else:
            self.package_download_urls = package_config_dict['urls']
        
        if not 'build_type' in package_config_dict.keys():
            raise ValueError(
                'Package configuration dictionary missing "build_type" key ' \
                'which is required.'
            )
        else:
            self.package_build_type = package_config_dict['build_type']
       
        # Getting package name without extension.
        package_extension_re_pattern = \
            '(\.git|\.zip|\.tar|\.tar\.bz2|\.tar\.gz|\.tar\.xz)$'
        package_file_name_without_extension = re_replace(
            package_extension_re_pattern, '', self.package_file_name)
        
        # Source repository where package will be download.
        self.source_repo = package_config_dict.get(
            'cache_directory', package_cache_default_dir
        )
        self.package_source_repo = os.path.join(
            self.source_repo, self.package_file_name
        )
 
        # Source directory where package will be extracted.
        self.source_path = package_config_dict.get(
            'extract_root', package_extract_default_root
        )
        self.package_source_path = os.path.join(
            self.source_path, package_file_name_without_extension
        )
        
        # Build directory where package will build, it also depends on package
        # build type.
        self.build_path = package_config_dict.get(
            'build_root', package_build_default_root
        )
        self.package_build_path = os.path.join(
            self.build_path, package_file_name_without_extension
        )
        if self.package_build_type == "imake":
            self.package_build_path = self.package_source_path
 
        # Install directory where package will install, it also depends on 
        # package build type.
        self.install_path = package_config_dict.get(
            'install_root', package_install_default_root
        )
        self.package_install_path = os.path.join(
            self.install_path, self.package_name
        )
        if self.package_build_type == "distutils":
            get_sitepackage_cmd = \
                ['python', '-c', 'import site; site.getsitepackages()[0]']
            stdout, stderr = run_command(get_sitepackage_cmd)
            if stderr != "":
                raise Exception('ERROR - {}'.format(stderr)) 
            self.package_install_path = stdout

        if 'install_check_files' in package_config_dict.keys(): 
            temp = package_config_dict['install_check_files']
            temp = self.replace_package_env_vars(temp)
            temp = replace_env_vars(temp)
            self.package_installation_verify_files = temp
        else:
            self.package_installation_verify_files = []

        if 'install_check_cmds' in package_config_dict.keys(): 
            temp = package_config_dict['install_check_cmds']
            temp = self.replace_package_env_vars(temp)
            temp = replace_env_vars(temp)
            self.package_installation_verify_cmds = temp
        else:
            self.package_installation_verify_cmds = []

        if self.package_installation_verify_files == [] and \
            self.package_installation_verify_cmds == []:
            raise ValueError(
                'package "install_check_files" and "install_check_cmds" '
                'option can not be empty, you need to provide at least one '
                'condition to check package installation'
            )

        self.package_configuration_files = \
            package_config_dict.get('config_files', {})
        self.package_pre_install_scripts = \
            package_config_dict.get('pre_install_scripts', [])
        self.package_post_install_scripts = \
            package_config_dict.get('post_install_scripts', [])
        self.package_patches = \
            package_config_dict.get('patches', [])
 

        # Replacing environment variables in configuration options.
        self.package_configure_args = \
            package_config_dict.get('configure_args', [])
        self.package_configure_args = self.replace_package_env_vars(
            self.package_configure_args
        )
        self.package_configure_args = replace_env_vars(
            self.package_configure_args
        )
     
        # If package configure does not match with build type default command.
        if 'configure_cmd' in package_config_dict.keys():
            self.package_configure_cmd = package_config_dict['configure_cmd']
            self.package_configure_cmd = self.replace_package_env_vars(
                self.package_configure_cmd
            )
            self.package_configure_cmd = replace_env_vars(
                self.package_configure_cmd
            )
        else:
            self.package_configure_cmd = ""
      
        # Create required directories if does not exists.
        self._create_dirs(self.source_repo)
        self._create_dirs(self.source_path)
        self._create_dirs(self.build_path)
        self._create_dirs(self.install_path)
        
        # Adding debug logs to show package properties. 
        class_properties = []
        for prop, value in vars(self).items():
            class_properties.append(prop + " : " + str(value))
        logger.debug(
            'Package %s properties are %s\n',
            self.package_name, "\n".join(class_properties)
        )

    def replace_package_env_vars(self, replacing_data):
        package_env_dict = {
            'INSTALL_ROOT_DIR' : self.install_path,
            'SOURCE_ROOT_DIR' : self.source_path,
            'BUILD_ROOT_DIR' : self.build_path,
            'PACKAGE_INSTALL_DIR' : self.package_install_path,
            'PACKAGE_SOURCE_DIR' : self.package_source_path,
            'PACKAGE_BUILD_DIR' : self.package_build_path
        } 

        def _replace_env_vars(replaced_data):
            for pkg_env_key, pkg_env_value in package_env_dict.items():
                re_pattern = "\$" + pkg_env_key
                replaced_data = re_replace(
                    re_pattern, pkg_env_value, replaced_data
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
                    'Object type is not supported {}'.format(
                    type(replaced_data)
                ))
        
        replaced_data = replacing_data
        logger.debug('Replacing package environment variables')
        replaced_data = _recursive_replace_env_vars(replaced_data)
         
        logger.debug(
            'Replaced package environment variables \n Before replacement ' \
            'string \n%s \nAfter replacement string \n%s',
            replacing_data, replaced_data
        ) 
        
        return replaced_data
    
    def is_package_exists(self):
        logger.info('Verifying package exists or not %s', self.package_name)
        if os.path.exists(self.package_source_repo):
            return True
        else:
            return False

    def is_package_installed(self):
        # Verifying installation files.
        logger.info('Verifying package installed or not %s', self.package_name)
        for installation_file in self.package_installation_verify_files:
            file_path = os.path.join(
                self.install_path, installation_file
            )
            if not os.path.exists(file_path):
                logger.info('Installation file ' + file_path + ' not found')
                return False
            else:
                logger.info('Installation file ' + file_path + ' found')
        
        # Verifying installation commands.
        for cmd_array in self.package_installation_verify_cmds:
            stdout, stderr = run_command(cmd_array[0])

            if stderr != "":
                logger.info('Command execution failed. Error is %s', stderr)
                return False
            if stdout.strip() != cmd_array[1].strip():
                logger.info(
                    'Command output did not match with expected output. ' + \
                    '\nCommand output\n%s\nExpected output\n%s',
                    stdout.strip(), cmd_array[1].strip()
                )
                return False
            
            logger.info('Command %s executed successfully', cmd_array[0])

        return True

    def run_pre_install_scripts(self):
        for script in self.package_pre_install_scripts:
            logger.info('Executing pre install script %s', script)
            if self._run_script(script, self.package_source_path) == False:
                raise Exception('Error occured in %s script execution', script)
            logger.info('Script %s executed successfully.', script)

        return True

    def run_post_install_scripts(self):
        # If package build type is distutils then install directory will not
        # exists, so using project root
        script_execution_dir = self.package_install_path
        if not os.path.exists(script_execution_dir):
            script_execution_dir = os.getcwd()
        
        for script in self.package_post_install_scripts:
            logger.info('Executing post install script %s', script)
            if self._run_script(script, script_execution_dir) == False:
                raise Exception('Error occured in %s script execution', script)
            logger.info('Script %s executed successfully.', script)

        return True

    def setup_config_files(self):
        
        # Source file and destination file both should be absolute path.
        for source_file, dest_file in self.package_configuration_files.items():
            source_file_path = source_file
            dest_file_path = dest_file

            print(
                '[COPY] ' + source_file_path + ' to ' + dest_file_path, end=''
            )

            if not os.path.exists(source_file_path):
                print('  [FAILED]')
                return False

            if not os.path.exists(os.path.dirname(dest_file_path)):
                os.makedirs(os.path.dirname(dest_file_path))

            with open(source_file_path, 'r') as source_fd:
                with open(dest_file_path, 'w+') as dest_fd:
                    source_file_data = source_fd.read()
                    source_file_data = self.replace_package_env_vars(
                        source_file_data
                    )
                    source_file_data = replace_env_vars(source_file_data)
                    dest_fd.write(source_file_data)
            print('  [PASSED]')

        return True
    
    def _create_dirs(self, dir_path):
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)

    def _run_script(self, script_file, script_execution_dir):
        print('[SCRIPT] ' + script_file, end='')

        if not os.path.exists(script_file):
            print('  [NOT FOUND]')
            return True

        # Read script file, replace environment variables and write it to temp 
        # file.
        script_temp_file = script_file + '-temp.sh'
        with open(script_file, 'r') as read_file:
            with open(script_temp_file, 'w+') as write_file:
                read_file_data = read_file.read()
                logger.info(
                    'Script file - \n%s', read_file_data
                )
                read_file_data = self.replace_package_env_vars(read_file_data)
                read_file_data = replace_env_vars(read_file_data)
                logger.info(
                    'Script file after replacing environment variables \n%s',
                    read_file_data
                )
                write_file.write(read_file_data)

        script_bash_cmd = ['bash', script_temp_file]
        stdout, stderr = run_command(script_bash_cmd, script_execution_dir)
        os.remove(script_temp_file)
        
        if stderr == "":
            print('  [EXECUTION PASSED]')
            return True
        else:
            print('  [EXECUTION FAILED] Error is {}'.format(stderr))
            return False
