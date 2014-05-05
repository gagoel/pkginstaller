import os
import json
import re
import subprocess
import logging

from pkginstaller.internal.setup_utils import *

logger = logging.getLogger('pkginstaller.setup_packages_utils')


def run_make_configure_cmd(
    src_dir, build_dir, install_dir, configure_args, configure_cmd
):
    optional_argument = configure_args
    configure_file = configure_cmd
    if configure_file == "":
        configure_file = os.path.join(src_dir, 'configure')

    configure_cmd = [configure_file, '--prefix=' + install_dir]
    configure_cmd.extend(optional_argument)

    print('[MAKE] Configuration package...')
    stdout, stderr = run_command(configure_cmd, build_dir)
    if stderr == "":
        print('[MAKE] Configuration was successed.')
        logger.debug('Configuration output %s', stdout)
        return True
    else:
        print('[MAKE] Configuration was failed.')
        print('Error {}'.format(stderr))
        return False

def run_cmake_configure_cmd(src_dir, build_dir, install_dir, configure_args):
    optional_argument = configure_args

    configure_cmd = ['cmake', src_dir, '-DCMAKE_INSTALL_PREFIX=' + \
        install_dir]
    configure_cmd.extend(optional_argument)

    print('[CMAKE] Configuration package...')
    stdout, stderr = run_command(configure_cmd, build_dir)
    if stderr == "":
        print('[CMAKE] Configuration was successed.')
        logger.debug('Configuration output %s', stdout)
        return True
    else:
        print('[CMAKE] Configuration was failed.')
        print('Error {}'.format(stderr))
        return False

def run_make_build_cmd(build_dir):
    build_cmd = ['make']
    print('[MAKE] Building package...')
    stdout, stderr = run_command(build_cmd, build_dir)
    if stderr == "":
        print('[MAKE] Build was successed.')
        return True
    else:
        print('[MAKE] Build was failed.')
        print('Error {}'.format(stderr))
        return False

def run_make_install_cmd(build_dir):
    install_cmd = ['make', 'install']
    print('[MAKE] Installing package...')
    stdout, stderr = run_command(install_cmd, build_dir)
    if stderr == "":
        print('[MAKE] Installation was successed.')
        return True
    else:
        print('[MAKE] Installation was failed.')
        print('Error {}'.format(stderr))
        return False

def run_make_build(
    pkg_src_dir, pkg_build_dir, pkg_install_dir, pkg_config_args,
    pkg_config_cmd, pkg_patches, is_cmake=False
):

    logger.debug(
        'Executing make build \nSource Dir - %s \nBuild Dir - %s\n' \
        'Install Dir - %s\n Configure Args - %s\n Configure cmd - %s',
        pkg_src_dir, pkg_build_dir, pkg_install_dir,
        pkg_config_args, pkg_config_cmd
    )
    
    # Applying patches
    for patch in pkg_patches:
        apply_patch(patch, pkg_src_dir)
    
    # Configuring package.
    status = False
    if is_cmake:
        status = run_cmake_configure_cmd(
            pkg_src_dir,
            pkg_build_dir,
            pkg_install_dir,
            pkg_config_args
        )
    else:
        status = run_make_configure_cmd(
            pkg_src_dir,
            pkg_build_dir,
            pkg_install_dir,
            pkg_config_args,
            pkg_config_cmd
        )

    if status == False:
        print('Package configuration failed.')
        return False 

    # Building package.
    if run_make_build_cmd(pkg_build_dir) == False:
        print('Building package failed.')
        return False

    # Installing package.
    if run_make_install_cmd(pkg_build_dir) == False:
        print('Installing package failed.')
        return False

    return True

def run_distutils_build(pkg_source_path, pkg_patches):
    # Applying patches
    for patch in pkg_patches:
        apply_patch(patch, pkg_source_path)

    # distutils installation.
    install_cmd = ['python', 'setup.py', 'install']

    print('[DISTUTILS] Installing package...')
    stdout, stderr = run_command(install_cmd, pkg_source_path)
    if stderr == "":
        print('[DISTUTILS] Installation was successed.')
        return True
    else:
        print('[DISTUTILS] Installation was failed.')
        print('Error {}'.format(stderr))
        return False
