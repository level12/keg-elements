import os.path as osp
from setuptools import setup, find_packages

cdir = osp.abspath(osp.dirname(__file__))
README = open(osp.join(cdir, 'readme.rst')).read()
CHANGELOG = open(osp.join(cdir, 'changelog.rst')).read()

version_fpath = osp.join(cdir, 'keg_elements', 'version.py')
version_globals = {}
with open(version_fpath) as fo:
    exec(fo.read(), version_globals)

setup(
    name="KegElements",
    version=version_globals['VERSION'],
    description=("A testing ground for Keg related code and ideas."),
    long_description='\n\n'.join((README, CHANGELOG)),
    author="Randy Syring",
    author_email="randy.syring@level12.io",
    url='https://github.com/level12/keg-elements',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
    ],
    license='BSD',
    packages=find_packages(),
    zip_safe=False,
    include_package_data=True,
    install_requires=[
        'arrow',
        'Keg',
        'WTForms-Alchemy',
        'Flask-WTF',

    ]
)
