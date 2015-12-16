from setuptools import setup, find_packages

setup(name='hydra',
      version='0.7.4',
      author='Max Korinets',
      author_email='mkorinets@gmail.com',
      license='MIT',
      description='Asset rendering for real estate showcase websites',
      install_requires=[
          'art3dutils',
          'fabric',
          'paste',
          'pyramid_mako',
          'pyramid',
          'transaction',
          'reportlab',
          'xlrd',
          'xlwt'
      ],
      include_package_data=True,
      packages=find_packages())