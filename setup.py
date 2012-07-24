from setuptools import setup, find_packages
import sys, os

version = '0.1'

setup(name='pygeoif',
      version=version,
      description="A basic implementation of the __geo_interface__",
            long_description=open(
              "README.rst").read() + "\n" +
              open(os.path.join("docs", "HISTORY.txt")).read(),
      classifiers=[
        "Topic :: Scientific/Engineering :: GIS",
        "Programming Language :: Python",
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Development Status :: 3 - Alpha',
        'Operating System :: OS Independent',
      ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='GIS Spatial',
      author='Christian Ledermann',
      author_email='christian.ledermann@gmail.com',
      url='',
      license='',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          # -*- Extra requirements: -*-
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )