varnish.repository:
  pkgrepo.managed:
    - name: deb http://repo.varnish-cache.org/ubuntu/ trusty varnish-3.0
    - key_url: http://repo.varnish-cache.org/debian/GPG-key.txt
    - file: /etc/apt/sources.list.d/varnish.list
    - require_in:
      - pkg: varnish.packages
    - require:
      - sls: global

varnish.packages:
  pkg.installed:
    - refresh: True
    - names:
      - varnish

varnish.service:
  service.running:
    - name: varnish
    - require:
      - pkg: varnish.packages
