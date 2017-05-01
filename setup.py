from distutils.core import setup

setup(
    name='JumpScale9Joystick',
    version='9.0.0a1',
    description='Automation framework for cloud workloads remote sal, sal= system abstraction layer',
    url='https://github.com/Jumpscaler/joystick9',
    author='GreenItGlobe',
    author_email='info@gig.tech',
    license='Apache',
    packages=['JumpScale9Joystick'],
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
