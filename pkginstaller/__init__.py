import os
import sys
import logging

from pkginstaller.internal.setup_package import SetupPackage
from pkginstaller.internal.setup_packages import SetupPackages

__author__ = "Gaurav Goel"
__license__ = "None"
__version__ = "0.1.0"

PACKAGE_CACHE_DEFAULT_DIR = os.path.join(os.getcwd(), "externals/src_repo")
PACKAGE_EXTRACT_DEFAULT_ROOT = os.path.join(os.getcwd(), "externals/src")
PACKAGE_BUILD_DEFAULT_ROOT = os.path.join(os.getcwd(), "externals/build")
PACKAGE_INSTALL_DEFAULT_ROOT = os.path.join(os.getcwd(), "externals/install")

logger = logging.getLogger('pkginstaller.__init__')


def install_package(
    package_name,
    package_file_name,
    package_build_type,
    package_remote_urls,
    package_install_check_files,
    package_install_check_cmds,
    
    package_cache_directory = PACKAGE_CACHE_DEFAULT_DIR,
    package_extract_root_directory = PACKAGE_EXTRACT_DEFAULT_ROOT,
    package_build_root_directory = PACKAGE_BUILD_DEFAULT_ROOT,
    package_install_root_directory = PACKAGE_INSTALL_DEFAULT_ROOT,
    
    package_configure_args = [],
    package_patches = [],
    package_pre_install_scripts = [],
    package_post_install_scripts = [],
    package_configuration_files = {},
    package_configure_cmd = "$PACKAGE_SOURCE_DIR/config",

    remote_host = "localhost",
    remote_ssh_port = 22,
    remote_ssh_user = None,
    remote_ssh_pass = None,
    verbose = 0
):   
    # constructing configuration dictionary    
    pkg_config_dict = {
        "name" : package_name,
        "file_name" : package_file_name,
        "build_type" :  package_build_type,
        "urls" : package_remote_urls,
        "cache_directory" : package_cache_directory,
        "extract_root" : package_extract_root_directory,
        "build_root" : package_build_root_directory,
        "install_root" : package_install_root_directory,
        "configure_args" : package_configure_args,
        "patches" : package_patches, 
        "pre_install_scripts" : package_pre_install_scripts,
        "post_install_scripts" : package_post_install_scripts,
        "install_check_cmds" : package_install_check_cmds,
        "install_check_files" : package_install_check_files,
        "config_files" : package_configuration_files,
        "configure_cmd" : package_configure_cmd
    }

    pkgs_config_list = [pkg_config_dict]    

    setup_packages = SetupPackages(
        pkgs_config_list,
        package_cache_directory,
        package_extract_root_directory,
        package_build_root_directory,
        package_install_root_directory,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    )

    setup_packages.download()
    setup_packages.extract()
    setup_packages.install()

    return True

def install_packages(
    packages_configuration_list,
    packages_cache_default_dir = PACKAGE_CACHE_DEFAULT_DIR,
    packages_extract_default_root = PACKAGE_EXTRACT_DEFAULT_ROOT,
    packages_build_default_root = PACKAGE_BUILD_DEFAULT_ROOT,
    packages_install_default_root = PACKAGE_INSTALL_DEFAULT_ROOT,
    remote_host="localhost",
    remote_ssh_port = 22,
    remote_ssh_user = None,
    remote_ssh_pass = None,
    verbose = 0
):
    setup_packages = SetupPackages(
        packages_configuration_list,
        packages_cache_default_dir,
        packages_extract_default_root,
        packages_build_default_root,
        packages_install_default_root,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    )

    setup_packages.download()
    setup_packages.extract()
    setup_packages.install()

    return True
