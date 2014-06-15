import os
import json
import re
import subprocess
import logging

from pkginstaller.internal.setup_utils import *

logger = logging.getLogger('pkginstaller.setup_packages_utils')


def run_make_configure_cmd(
    src_dir,
    build_dir,
    install_dir,
    configure_args,
    configure_cmd,
    remote_host = "localhost",
    remote_ssh_port = 22,
    remote_ssh_user = None,
    remote_ssh_pass = None,
    verbose = 0
):
    optional_argument = configure_args
    configure_file = configure_cmd
    if configure_file == "":
        configure_file = os.path.join(src_dir, 'configure')

    configure_cmd = [configure_file, '--prefix=' + install_dir]
    configure_cmd.extend(optional_argument)

    if verbose > 0:
        print('[MAKE] Configuration package...')
    stdout, stderr = run_command(
        configure_cmd,
        build_dir,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    )
    if "error " in stderr or "Error " in stderr or "ERROR " in stderr:
        if verbose > 0:
            print('[MAKE] Configuration was failed.')
        print('Error  {}'.format(stderr))
        return False
    else:
        if verbose > 0:
            print('[MAKE] Configuration was successed.')
        logger.debug('Configuration output %s', stdout)
        return True

def run_cmake_configure_cmd(
    src_dir,
    build_dir,
    install_dir,
    configure_args,
    remote_host = "localhost",
    remote_ssh_port = 22,
    remote_ssh_user = None,
    remote_ssh_pass = None,
    verbose = 0
):
    optional_argument = configure_args

    configure_cmd = ['cmake', src_dir, '-DCMAKE_INSTALL_PREFIX=' + \
        install_dir]
    configure_cmd.extend(optional_argument)

    if verbose > 0:
        print('[CMAKE] Configuration package...')
    stdout, stderr = run_command(
        configure_cmd,
        build_dir,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    )
    if "error " in stderr or "Error " in stderr or "ERROR " in stderr:
        if verbose > 0:
            print('[CMAKE] Configuration was failed.')
        print('Error  {}'.format(stderr))
        return False
    else:
        if verbose > 0:
            print('[CMAKE] Configuration was successed.')
        logger.debug('Configuration output %s', stdout)
        return True

def run_make_build_cmd(
    build_dir,
    remote_host = "localhost",
    remote_ssh_port = 22,
    remote_ssh_user = None,
    remote_ssh_pass = None,
    verbose = 0 
):
    build_cmd = ['make']
    if verbose > 0:
        print('[MAKE] Building package...')
    stdout, stderr = run_command(
        build_cmd,
        build_dir,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    )
    if "error " in stderr or "Error " in stderr or "ERROR " in stderr:
        if verbose > 0:
            print('[MAKE] Build was failed.')
        print('Error  {}'.format(stderr))
        return False
    else:
        if verbose > 0:
            print('[MAKE] Build was successed.')
        return True

def run_make_install_cmd(
    build_dir,
    remote_host = "localhost",
    remote_ssh_port = 22,
    remote_ssh_user = None,
    remote_ssh_pass = None,
    verbose = 0
):
    install_cmd = ['make', 'install']
    if verbose > 0:
        print('[MAKE] Installing package...')
    stdout, stderr = run_command(
        install_cmd,
        build_dir,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    )
    if "error " in stderr or "Error " in stderr or "ERROR " in stderr:
        if verbose > 0:
            print('[MAKE] Installation was failed.')
        print('Error  {}'.format(stderr))
        return False
    else:
        if verbose > 0:
            print('[MAKE] Installation was successed.')
        return True

def run_make_build(
    pkg_src_dir, 
    pkg_build_dir, 
    pkg_install_dir, 
    pkg_config_args,
    pkg_config_cmd="", 
    package_patches=[], 
    is_cmake=False,
    remote_host = "localhost",
    remote_ssh_port = 22,
    remote_ssh_user = None,
    remote_ssh_pass = None,
    verbose = 0
):

    logger.debug(
        'Executing make build \nSource Dir - %s \nBuild Dir - %s\n' \
        'Install Dir - %s\n Configure Args - %s\n Configure cmd - %s',
        pkg_src_dir, pkg_build_dir, pkg_install_dir,
        pkg_config_args, pkg_config_cmd
    )
    
    # Applying patches
    for patch in package_patches:
        apply_patch(
            patch,
            pkg_src_dir,
            remote_host=remote_host,
            remote_ssh_port=remote_ssh_port,
            remote_ssh_user=remote_ssh_user,
            remote_ssh_pass=remote_ssh_pass,
            verbose=verbose
        )
    
    # Configuring package.
    status = False
    if is_cmake:
        status = run_cmake_configure_cmd(
            pkg_src_dir,
            pkg_build_dir,
            pkg_install_dir,
            pkg_config_args,
            remote_host=remote_host,
            remote_ssh_port=remote_ssh_port,
            remote_ssh_user=remote_ssh_user,
            remote_ssh_pass=remote_ssh_pass,
            verbose=verbose
        )
    else:
        status = run_make_configure_cmd(
            pkg_src_dir,
            pkg_build_dir,
            pkg_install_dir,
            pkg_config_args,
            pkg_config_cmd,
            remote_host=remote_host,
            remote_ssh_port=remote_ssh_port,
            remote_ssh_user=remote_ssh_user,
            remote_ssh_pass=remote_ssh_pass,
            verbose=verbose
        )

    if status == False:
        if verbose > 0:
            print('Package configuration failed.')
        return False 

    # Building package.
    if run_make_build_cmd(
        pkg_build_dir,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    ) == False:
        if verbose > 0:
            print('Building package failed.')
        return False

    # Installing package.
    if run_make_install_cmd(
        pkg_build_dir,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    ) == False:
        if verbose > 0:
            print('Installing package failed.')
        return False

    return True

def run_distutils_build(
    pkg_source_path, 
    package_patches=[],
    remote_host = "localhost",
    remote_ssh_port = 22,
    remote_ssh_user = None,
    remote_ssh_pass = None,
    verbose = 0
):
    # Applying patches
    for patch in package_patches:
        apply_patch(
            patch,
            pkg_source_path,
            remote_host=remote_host,
            remote_ssh_port=remote_ssh_port,
            remote_ssh_user=remote_ssh_user,
            remote_ssh_pass=remote_ssh_pass,
            verbose=verbose
        )

    # distutils installation.
    install_cmd = ['python', 'setup.py', 'install']

    if verbose > 0:
        print('[DISTUTILS] Installing package...')
    stdout, stderr = run_command(
        install_cmd,
        pkg_source_path,
        remote_host=remote_host,
        remote_ssh_port=remote_ssh_port,
        remote_ssh_user=remote_ssh_user,
        remote_ssh_pass=remote_ssh_pass,
        verbose=verbose
    )
    if "error " in stderr or "Error " in stderr or "ERROR " in stderr:
        if verbose > 0:
            print('[DISTUTILS] Installation was failed.')
        print('Error  {}'.format(stderr))
        return False
    else:
        if verbose > 0:
            print('[DISTUTILS] Installation was successed.')
        return True
