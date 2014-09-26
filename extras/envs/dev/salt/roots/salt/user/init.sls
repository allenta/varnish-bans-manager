user.timezone:
  timezone.system:
    - name: Europe/Madrid
    - utc: True

{% for package, version in [('sass', '3.2.13'), ('compass', '0.12.2')] %}
user.{{ package }}:
  gem.installed:
    - user: root
    - name: {{ package }}
    - version: {{ version }}
    - require:
      - sls: global
{% endfor %}

/home/vagrant/.profile:
  file.managed:
    - source: salt://user/profile
    - user: vagrant
    - group: vagrant
    - mode: 644

/vagrant/files:
  file.directory:
    - user: vagrant
    - makedirs: True
