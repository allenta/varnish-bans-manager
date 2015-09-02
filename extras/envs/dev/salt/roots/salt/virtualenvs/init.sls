virtualenvs.install-virtualenv:
  pip.installed:
    - name: virtualenv==1.11.5
    - user: root
    - require:
      - sls: global

virtualenvs.default:
  virtualenv.managed:
    - name: /home/vagrant/.virtualenvs/default
    - user: vagrant
    - requirements: /vagrant/requirements.txt
    - require:
      - pip: virtualenvs.install-virtualenv

{% for package in ['ipython', 'MySQL-python', 'pyinotify'] %}
virtualenvs.default.{{ package }}:
  pip.installed:
    - name: {{ package }}
    - user: vagrant
    - bin_env: /home/vagrant/.virtualenvs/default
    - require:
      - pip: virtualenvs.install-virtualenv
{% endfor %}
