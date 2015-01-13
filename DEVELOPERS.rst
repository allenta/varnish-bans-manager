General Tips
============

Next you can find some general Varnish Bans Manager (VBM) development
tips. These are only useful for developers when setting up their
development environment.

- Check out ``setup.py`` and install all required dependencies.

- Use ``VARNISH_BANS_MANAGER_CONF`` environment variable to point to
  your personal configuration file. Also remember to:

    - Set ``development`` to ``true`` in your personal configuration.

    - Disable ``http > daemon`` in your personal configuration if
      developing using Gunicorn::

        $ python varnish_bans_manager/runner.py start

    - Use ``--nothreading`` if using Django embedded HTTP server::

        $ python varnish_bans_manager/runner.py runserver 0.0.0.0:9000 --nothreading

    - Initialize database schema::

        $ python varnish_bans_manager/runner.py syncdb
        $ python varnish_bans_manager/runner.py migrate
        $ python varnish_bans_manager/runner.py createcachetable cache

    - Create the first VBM administrator. You'll be able to add extra
      users later using the web UI::

        $ python varnish_bans_manager/runner.py users --add --administrator --email "bob@domain.com" --password "s3cr3t" --firstname "Bob" --lastname "Brown"

- Install `Sass <http://sass-lang.com>`_ and `Compass <http://compass-style.org>`_
  in your development box (required by ``django-mediagenerator`` asset manager)::

    $ sudo apt-get install rubygems
    $ sudo gem install sass compass

- Don't forget to manually launch celeryd/celerybeat in some available
  term/screen while developing::

    $ python varnish_bans_manager/runner.py celery worker --beat -s ~/varnish-bans-manager-celerybeat-schedule --loglevel=info

- Remember to install the packages required by your relational database
  backend. For example, for MySQL::

    $ pip install MySQL-python

- While developing, press ``CTRL+ALT+A`` in your browser to display the
  VBM debug console.

- Remember .po files can be regenerated and compiled using the following
  commands::

    $ python runner.py makemessages -l es -e "html,txt,email,py"
    $ python varnish_bans_manager/runner.py compilemessages

Source Distribution Package
===========================

VBM sources require a build step previous to the generation of the Python
source distribution package. During this phase SASS sources are compiled
to CSS, some Javascript and CSS bundles are created, static contents are
versioned, translation files are compiled, etc.

In order to execute this site building phase and then generate the Python
source distribution package, simply run the following command in the root
folder of the VBM sources::

    $ make sdist

Note that the site building phase has some extra system requirements:

- `YUI Compressor <http://developer.yahoo.com/yui/compressor/>`_ and some
  Java Runtime Environment::

    $ export YUICOMPRESSOR_PATH="/path/to/yuicompressor.jar"
    $ sudo apt-get install openjdk-7-jre

- GNU internationalization utilities. In Ubuntu::

    $ sudo apt-get install gettext

TODO
====

- Ban templates.
- Refactor ``varnish_bans_manager.filesystem.models``.
- Locale-aware application level ordering.
