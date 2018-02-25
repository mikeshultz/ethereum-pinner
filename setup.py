import setuptools

setuptools.setup(name='pinner',
    version='0.0.1b1',
    description='Ethereum ipfs pinner',
    long_description=open('README.md').read().strip(),
    author='Mike Shultz',
    author_email='mike@mikeshultz.com',
    url='http://github.com/mikeshultz/ethereum-pinner',
    py_modules=['pinner'],
    install_requires=['eth-abi>=0.5.0', 'eth-utils>=0.7.4', 'jsonrpc-requests>=0.4.0'],
    license='GPLv3',
    zip_safe=False,
    keywords='ethereum ipfs',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.6',
        'Topic :: System :: Distributed Computing',
    ],
    entry_points = {
        'console_scripts': ['pinner=pinner:main'],
    }
)