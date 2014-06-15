import os
import json
import re
import subprocess

from pkginstaller.internal.setup_package import SetupPackage
from pkginstaller.internal.setup_packages_utils import *
from pkginstaller.internal.setup_utils import *

logger = logging.getLogger('pkginstaller.setup_packages')


class SetupPackages:

    def __init__(
        self,
        packages_config_list,
        packages_cache_default_dir,
        packages_extract_default_root,
        packages_build_default_root,
        packages_install_default_root,
        remote_host="localhost",
        remote_ssh_port=22,
        remote_ssh_user=None,
        remote_ssh_pass=None,
        verbose=0
    ):
        self._packages_config_list = packages_config_list
        self._packages_cache_default_dir = packages_cache_default_dir
        self._packages_extract_default_root = packages_extract_default_root
        self._packages_build_default_root = packages_build_default_root
        self._packages_install_default_root = packages_install_default_root
        self._remote_host = remote_host
        self._remote_ssh_port = remote_ssh_port
        self._remote_ssh_user = remote_ssh_user
        self._remote_ssh_pass = remote_ssh_pass
        self._verbose = verbose

    def download(self):
        if self._verbose > 0:
            print('\nDOWNLOADING PACKAGES...')
        
        logger.debug(
            'Packages configuration dict is %s',
            self._packages_config_list
        )

        for package_dict in self._packages_config_list:
            # Starting timer.
            timer_obj = Timer(verbose=self._verbose)
            timer_obj.start()

            package_obj = SetupPackage(
                package_dict,
                self._packages_cache_default_dir,
                self._packages_extract_default_root,
                self._packages_build_default_root,
                self._packages_install_default_root,
                remote_host=self._remote_host,
                remote_ssh_port=self._remote_ssh_port,
                remote_ssh_user=self._remote_ssh_user,
                remote_ssh_pass=self._remote_ssh_pass,
                verbose=self._verbose
            )
            if self._verbose > 0:
                print('[FILE] ' + package_obj.package_source_repo, end='')
            
            if package_obj.is_package_exists():
                if self._verbose > 0:
                    print('  [FOUND]')
                continue

            file_downloaded_success = False
            if self._verbose > 0:
                print('  [NOT FOUND] [DOWNLOADING...]\n')    
            for package_download_url in package_obj.package_download_urls:
                file_downloaded_success = download_file(
                    package_obj.package_file_name,
                    package_download_url,
                    package_obj.source_repo,
                    remote_host=self._remote_host,
                    remote_ssh_port=self._remote_ssh_port,
                    remote_ssh_user=self._remote_ssh_user,
                    remote_ssh_pass=self._remote_ssh_pass,
                    verbose=self._verbose
                )
                if file_downloaded_success:
                    break

            if not file_downloaded_success:
                raise Exception(
                    'Error in downloading package ' + package_obj.package_name
                )

            # printing elapsed time if verbose
            timer_obj.stop()

    def extract(self):
        if self._verbose > 0:
            print('\nEXTRACTING PACKAGES...')

        for package_dict in self._packages_config_list:
            # Starting timer.
            timer_obj = Timer(verbose=self._verbose)
            timer_obj.start()

            package_obj = SetupPackage(
                package_dict,
                self._packages_cache_default_dir,
                self._packages_extract_default_root,
                self._packages_build_default_root,
                self._packages_install_default_root,
                remote_host=self._remote_host,
                remote_ssh_port=self._remote_ssh_port,
                remote_ssh_user=self._remote_ssh_user,
                remote_ssh_pass=self._remote_ssh_pass,
                verbose=self._verbose
            )
            if self._verbose > 0:
                print(
                    '[EXTRACTION] ' + package_obj.package_source_path,
                    end=''
                )

            if is_path_exists(
                package_obj.package_source_path,
                remote_host=self._remote_host,
                remote_ssh_port=self._remote_ssh_port,
                remote_ssh_user=self._remote_ssh_user,
                remote_ssh_pass=self._remote_ssh_pass,
                verbose=self._verbose  
            ):
                if self._verbose > 0:
                    print('  [CACHED]')
                    continue

            extract_file(
                package_obj.package_file_name,
                package_obj.source_repo,
                package_obj.source_path,
                remote_host=self._remote_host,
                remote_ssh_port=self._remote_ssh_port,
                remote_ssh_user=self._remote_ssh_user,
                remote_ssh_pass=self._remote_ssh_pass,
                verbose=self._verbose
            )
            if self._verbose > 0:
                print('  [EXTRACTED]')
            # printing elapsed time if verbose
            timer_obj.stop()

        return True

    def install(self):
        if self._verbose > 0:
            print('\nINSTALLING PACKAGES...')

        for package_dict in self._packages_config_list:
            # Starting timer.
            timer_obj = Timer(verbose=self._verbose)
            timer_obj.start()

            package_obj = SetupPackage(
                package_dict,
                self._packages_cache_default_dir,
                self._packages_extract_default_root,
                self._packages_build_default_root,
                self._packages_install_default_root,
                remote_host=self._remote_host,
                remote_ssh_port=self._remote_ssh_port,
                remote_ssh_user=self._remote_ssh_user,
                remote_ssh_pass=self._remote_ssh_pass,
                verbose=self._verbose
            )

            if package_obj.is_package_installed():
                if self._verbose > 0:
                    print(
                        'Checking ' + package_obj.package_name + \
                        ' package installation  [INSTALLED]'
                    )
                    continue
            else:
                if self._verbose > 0:
                    print(
                        '\nChecking ' + package_obj.package_name + \
                        ' package installation  [NOT INSTALLED]'
                    )

            if self._verbose > 0:
                print('Installing package ' + package_obj.package_name + '...')   
            
            status = package_obj.run_pre_install_scripts()
            if status == False:
                raise Exception('Pre Install Script execution failed.') 

            if package_obj.package_build_type == "make" or \
                package_obj.package_build_type == "imake":
                
                if not is_path_exists(
                    package_obj.package_build_path,
                    remote_host=self._remote_host,
                    remote_ssh_port=self._remote_ssh_port,
                    remote_ssh_user=self._remote_ssh_user,
                    remote_ssh_pass=self._remote_ssh_pass,
                    verbose=self._verbose
                ):
                    mkdirs(
                        package_obj.package_build_path,
                        remote_host=self._remote_host,
                        remote_ssh_port=self._remote_ssh_port,
                        remote_ssh_user=self._remote_ssh_user,
                        remote_ssh_pass=self._remote_ssh_pass,
                        verbose=self._verbose
                    )

                status = run_make_build(
                    package_obj.package_source_path,
                    package_obj.package_build_path,
                    package_obj.package_install_path,
                    package_obj.package_configure_args,
                    package_obj.package_configure_cmd,
                    package_patches=package_obj.package_patches,
                    remote_host=self._remote_host,
                    remote_ssh_port=self._remote_ssh_port,
                    remote_ssh_user=self._remote_ssh_user,
                    remote_ssh_pass=self._remote_ssh_pass,
                    verbose=self._verbose
                )
            elif package_obj.package_build_type == "cmake":
                if not is_path_exists(
                    package_obj.package_build_path,
                    remote_host=self._remote_host,
                    remote_ssh_port=self._remote_ssh_port,
                    remote_ssh_user=self._remote_ssh_user,
                    remote_ssh_pass=self._remote_ssh_pass,
                    verbose=self._verbose
                ):
                    mkdirs(
                        package_obj.package_build_path,
                        remote_host=self._remote_host,
                        remote_ssh_port=self._remote_ssh_port,
                        remote_ssh_user=self._remote_ssh_user,
                        remote_ssh_pass=self._remote_ssh_pass,
                        verbose=self._verbose
                    )
                
                status = run_make_build(
                    package_obj.package_source_path,
                    package_obj.package_build_path,
                    package_obj.package_install_path,
                    package_obj.package_configure_args,
                    package_patches=package_obj.package_patches,
                    is_cmake=True,
                    remote_host=self._remote_host,
                    remote_ssh_port=self._remote_ssh_port,
                    remote_ssh_user=self._remote_ssh_user,
                    remote_ssh_pass=self._remote_ssh_pass,
                    verbose=self._verbose
                )
            elif package_obj.package_build_type == "distutils":
                status = run_distutils_build(
                    package_obj.package_source_path,
                    package_patches=package_obj.package_patches,
                    remote_host=self._remote_host,
                    remote_ssh_port=self._remote_ssh_port,
                    remote_ssh_user=self._remote_ssh_user,
                    remote_ssh_pass=self._remote_ssh_pass,
                    verbose=self._verbose
                )
            else:
                raise Exception(
                    'Build type ' + package_obj.package_build_type + 
                    ' is not supported.'
                )

            if status == False:
                raise Exception('Package Installation failed.')

            if package_obj.setup_config_files() == False:
                raise Exception('Setting up configuration file failed.')

            if package_obj.run_post_install_scripts() == False:
                raise Exception('Post install scripts execution failed.')

            if package_obj.is_package_installed():
                if self._verbose > 0:
                    print(
                        '[PACKAGE ' + package_obj.package_name + \
                        ' INSTALLED SUCCESSFULLY]'
                    )
            else:
                if self._verbose > 0:
                    print(
                        '[PACKAGE ' + package_obj.package_name + \
                        ' INSTALLATION FAILED]'
                    )
            # printing elapsed time if verbose
            timer_obj.stop()

        return True
