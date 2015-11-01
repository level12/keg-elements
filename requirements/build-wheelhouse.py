import argparse
import subprocess
import os.path as osp

cdir = osp.dirname(__file__)
wheeldir_dpath = osp.join(cdir, 'wheelhouse')

pip_args = ['wheel', '--wheel-dir', wheeldir_dpath, '--use-wheel', '--find-links',
            wheeldir_dpath]


def build_file(req_fpath):
    subprocess.check_call(['pip'] + pip_args + ['-r', req_fpath])
    subprocess.check_call(['pip3.4'] + pip_args + ['-r', req_fpath])


def build_packages(packages):
    subprocess.check_call(['pip'] + pip_args + packages)
    subprocess.check_call(['pip3.4'] + pip_args + packages)

parser = argparse.ArgumentParser()
parser.add_argument('packages', nargs='*', default=[])

if __name__ == '__main__':
    args = parser.parse_args()
    if not args.packages:
        build_file(osp.join(cdir, 'runtime.txt'))
        build_file(osp.join(cdir, 'testing.txt'))
    else:
        build_packages(args.packages)
