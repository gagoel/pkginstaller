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
        packages_install_default_root
    ):
        self._packages_config_list = packages_config_list
        self._packages_cache_default_dir = packages_cache_default_dir
        self._packages_extract_default_root = packages_extract_default_root
        self._packages_build_default_root = packages_build_default_root
        self._packages_install_default_root = packages_install_default_root

    def download(self):
        print('\nDOWNLOADING PACKAGES...')
        
        logger.debug(
            'Packages configuration dict is %s',
            self._packages_config_list
        )

        for package_dict in self._packages_config_list:
            package_obj = SetupPackage(
                package_dict,
                self._packages_cache_default_dir,
                self._packages_extract_default_root,
                self._packages_build_default_root,
                self._packages_install_default_root
            )
            print('[FILE] ' + package_obj.package_source_repo, end='')
            
            if package_obj.is_package_exists():
                print('  [FOUND]')
                continue

            file_downloaded_success = False
            print('  [NOT FOUND] [DOWNLOADING...]\n')    
            for package_download_url in package_obj.package_download_urls:
                file_downloaded_success = download_file(
                    package_obj.package_file_name,
                    package_download_url,
                    package_obj.source_repo
                )
                if file_downloaded_success:
                    break

            if not file_downloaded_success:
                raise Exception(
                    'Error in downloading package ' + package_obj.package_name
                )

    def extract(self):
        print('\nEXTRACTING PACKAGES...')

        for package_dict in self._packages_config_list:
            package_obj = SetupPackage(
                package_dict,
                self._packages_cache_default_dir,
                self._packages_extract_default_root,
                self._packages_build_default_root,
                self._packages_install_default_root
            )
            print(
                '[EXTRACTION] ' + package_obj.package_source_path,
                end=''
            )

            if os.path.exists(package_obj.package_source_path):
                print('  [CACHED]')
                continue

            extract_file(
                package_obj.package_file_name,
                package_obj.source_repo,
                package_obj.source_path
            )
            print('  [EXTRACTED]')
        return True

    def install(self):
        print('\nINSTALLING PACKAGES...')

        for package_dict in self._packages_config_list:
            package_obj = SetupPackage(
                package_dict,
                self._packages_cache_default_dir,
                self._packages_extract_default_root,
                self._packages_build_default_root,
                self._packages_install_default_root
            )

            if package_obj.is_package_installed():
                print(
                    'Checking ' + package_obj.package_name + \
                    ' package installation  [INSTALLED]'
                )
                continue
            else:
                print(
                    '\nChecking ' + package_obj.package_name + \
                    ' package installation  [NOT INSTALLED]'
                )

            print('Installing package ' + package_obj.package_name + '...')   
            
            status = package_obj.run_pre_install_scripts()
            if status == False:
                raise Exception('Pre Install Script execution failed.') 

            if package_obj.package_build_type == "make" or \
                package_obj.package_build_type == "imake":
                
                if not os.path.exists(package_obj.package_build_path):
                    os.makedirs(package_obj.package_build_path)

                status = run_make_build(
                    package_obj.package_source_path,
                    package_obj.package_build_path,
                    package_obj.package_install_path,
                    package_obj.package_configure_args,
                    package_obj.package_configure_cmd,
                    package_patches=package_obj.package_patches
                )
            elif package_obj.package_build_type == "cmake":
                if not os.path.exists(package_obj.package_build_path):
                    os.makedirs(package_obj.package_build_path)
                
                status = run_make_build(
                    package_obj.package_source_path,
                    package_obj.package_build_path,
                    package_obj.package_install_path,
                    package_obj.package_configure_args,
                    package_patches=package_obj.package_patches,
                    is_cmake=True
                )
            elif package_obj.package_build_type == "distutils":
                status = run_distutils_build(
                    package_obj.package_source_path,
                    package_patches=pacakge_obj.package_patches
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
                print(
                    '[PACKAGE ' + package_obj.package_name + \
                    ' INSTALLED SUCCESSFULLY]'
                )
            else:
                print(
                    '[PACKAGE ' + package_obj.package_name + \
                    ' INSTALLATION FAILED]'
                )

        return True
