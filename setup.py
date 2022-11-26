from distutils.core import setup

setup(name='hwiclient', version='1.0.0', packages=['hwiclient'],
      install_requires=['twisted==22.10.0',
                        'service_identity',
                        'incremental==22.10.0',
                        'constantly==15.1.0',
                        'pyyaml',
                        'attrs'])
