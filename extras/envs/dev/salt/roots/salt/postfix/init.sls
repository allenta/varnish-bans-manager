postfix.service:
  service.running:
    - name: postfix
    - require:
      - sls: global
    - watch:
      - file: /etc/mailname
      - file: /etc/postfix/main.cf

/etc/mailname:
  file.managed:
    - source: salt://postfix/mailname.tmpl
    - template: jinja
    - defaults:
      host: {{ pillar['host'] }}
    - user: root
    - group: root
    - mode: 644

/etc/postfix/main.cf:
  file.managed:
    - source: salt://postfix/main.cf
    - user: root
    - group: root
    - mode: 644
