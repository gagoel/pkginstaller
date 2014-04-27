import os
import sys

from pkginstaller.internal.setup_package import SetupPackage
from pkginstaller.internal.setup_packages import SetupPackages

PROJECT_ROOT = os.getenv('PROJECT_ROOT')
if PROJECT_ROOT == None:
    raise Exception('PROJECT_ROOT environment variable is not set.')
PACKAGE_CACHE_DEFAULT_DIR = os.path.join(PROJECT_ROOT, "externals/src_repo")
PACKAGE_EXTRACT_DEFAULT_ROOT = os.path.join(PROJECT_ROOT, "externals/src")
PACKAGE_BUILD_DEFAULT_ROOT = os.path.join(PROJECT_ROOT, "externals/build")
PACKAGE_INSTALL_DEFAULT_ROOT = os.path.join(PROJECT_ROOT, "externals/install")

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
    package_configure_cmd = "$PACKAGE_SOURCE_DIR/config"
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

    pkgs_config_dict = {
        package_name : pkg_config_dict
    }    

    setup_packages = SetupPackages(
        pkgs_config_dict,
        package_cache_directory,
        package_extract_root_directory,
        package_build_root_directory,
        package_install_root_directory
    )

    setup_packages.download()
    setup_packages.extract()
    setup_packages.install()

    return True

def install_packages(
    packages_configuration_dict,
    packages_cache_default_dir = PACKAGE_CACHE_DEFAULT_DIR,
    packages_extract_default_root = PACKAGE_EXTRACT_DEFAULT_ROOT,
    packages_build_default_root = PACKAGE_BUILD_DEFAULT_ROOT,
    packages_install_default_root = PACKAGE_INSTALL_DEFAULT_ROOT,
):
    setup_packages = SetupPackages(
        packages_configuration_dict,
        packages_cache_default_dir,
        packages_extract_default_root,
        packages_build_default_root,
        packages_install_default_root
    )

    setup_packages.download()
    setup_packages.extract()
    setup_packages.install()

    return True
