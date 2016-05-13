# -*- coding: utf-8 -*-

# Author: Hans-Peter Jansen <hpj@urpla.net>
# License: GNU GPL 2 - see http://www.gnu.org/licenses/gpl2.txt for details
# vim:set et ts=8 sw=4:

import os
import sys

from distutils import log
import distutils.command.install_scripts as orig
from pkg_resources import Distribution, PathMetadata, ensure_directory


class install_symlinked_scripts(orig.install_scripts):
    """
    setuptools.command.install_scripts replacement

    given a console_scripts definition
    entry_points = {
        'console_scripts': [
            'progname = package.module',
        ],
    },
    it creates a relative symlink from 'progname' to 'module' in 'package'.
    Note, that any given attribute is ignored.

    Integration:
    from install_symlinked_scripts import install_symlinked_scripts
    cmdclass = {
        'install_scripts': install_symlinked_scripts,
    }
    setup(
        ...,
        cmdclass = cmdclass,
    )

    Usage:
    python3 setup.py install --prefix=/usr [--install-scripts=/usr/sbin]
    """
    def initialize_options(self):
        orig.install_scripts.initialize_options(self)
        self.no_ep = False
        self.dest_dir = None

    def finalize_options(self):
        orig.install_scripts.finalize_options(self)
        self.set_undefined_options('install_lib', ('install_dir', 'dest_dir'))

    def run(self):
        if sys.platform == 'win32':
            raise Exception("Symlinking scripts doesn't work with Windows")

        self.run_command("egg_info")
        if self.distribution.scripts:
            # run first to set up self.outfiles
            orig.install_scripts.run(self)
        else:
            self.outfiles = []
        if self.no_ep:
            # don't install entry point scripts into .egg file!
            return

        # build distribution object
        ei_cmd = self.get_finalized_command("egg_info")
        dist = Distribution(
            ei_cmd.egg_base, PathMetadata(ei_cmd.egg_base, ei_cmd.egg_info),
            ei_cmd.egg_name, ei_cmd.egg_version,
        )

        # fetch entry points and create symlinks to the targets
        for type_ in 'console', 'gui':
            group = type_ + '_scripts'
            for name, ep in dist.get_entry_map(group).items():
                log.info('install_symlinked_scripts: %s: %s', group, ep)
                if os.sep in name:
                    raise ValueError("Path separators not allowed in script names")
                self.symlink_script(name, ep)

    def symlink_script(self, scriptname, ep):
        """Symlink script from scripts directory to entry point module"""
        from setuptools.command.easy_install import chmod, current_umask
        # build dest module path
        dest = os.path.join(self.dest_dir, *ep.module_name.split('.')) + '.py'
        if not os.path.exists(dest):
            raise ValueError("Module %s not found (entry_point: %s)" % (dest, ep))
        # ep.attrs ignored!
        target = os.path.join(self.install_dir, scriptname)
        dest = os.path.relpath(dest, os.path.dirname(target))
        log.info('symlink_script: %s -> %s', target, dest)
        self.outfiles.append(target)
        mask = current_umask()
        if not self.dry_run:
            ensure_directory(target)
            if os.path.exists(target):
                log.info('symlink_script: target exists: %s: replace', target)
                os.unlink(target)
            os.symlink(dest, target)
            # make dest module executable through target
            chmod(target, 0o777 - mask)
