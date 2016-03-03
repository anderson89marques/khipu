import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.txt')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.txt')) as f:
    CHANGES = f.read()

requires = [
    'pyramid', 'pyramid_jinja2', 'pyramid_debugtoolbar',
    'pyramid_tm', 'SQLAlchemy', 'transaction',
    'zope.sqlalchemy', 'waitress', 'gunicorn',
    'alembic', 'psutil', 'passlib',
    'simple-crypt', 'oauthlib', 'psycopg2',
    'paginate'
    ]

setup(name='Khipu',
      version='0.1',
      description='Khipu',
      long_description=README + '\n\n' + CHANGES,
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
        ],
      author='',
      author_email='',
      url='',
      keywords='web wsgi bfg pylons pyramid',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      test_suite='khipu',
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = khipu:main
      [console_scripts]
      initialize_Khipu_db = khipu.scripts.initializedb:main
      """,
      )
