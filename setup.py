from distutils.core import setup

setup(
    name='JumpScale9RSAL',
    version='9.0.0a1',
    description='Automation framework for cloud workloads remote sal, sal= system abstraction layer',
    url='https://github.com/Jumpscaler/rsal9',
    author='GreenItGlobe',
    author_email='info@gig.tech',
    license='Apache',
    packages=['JumpScale9RSAL'],
    install_requires=[
        'redis',
        'colorlog',
        'pytoml',
        'ipython',
        'colored_traceback',
        'pystache',
        'libtmux',
        'httplib2',
        'netaddr',
        'paramiko'
    ]
)
