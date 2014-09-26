mysql.service:
  service.running:
    - name: mysql
    - require:
      - sls: global

mysql.set-root-password:
  cmd.run:
    - user: vagrant
    - unless: mysqladmin -uroot -p{{ pillar['mysql']['password'] }} status
    - name: mysqladmin -uroot password {{ pillar['mysql']['password'] }}
    - require:
      - service: mysql.service

mysql.create-db:
  cmd.run:
    - user: vagrant
    - unless: mysql -u{{ pillar['mysql']['user'] }} -p{{ pillar['mysql']['password'] }} {{ pillar['mysql']['name'] }}
    - name: mysql -uroot -p{{ pillar['mysql']['password'] }} -e "CREATE DATABASE {{ pillar['mysql']['name'] }}; CREATE USER '{{ pillar['mysql']['user'] }}'@'localhost' IDENTIFIED BY '{{ pillar['mysql']['password'] }}'; GRANT ALL PRIVILEGES ON {{ pillar['mysql']['name'] }}.* TO '{{ pillar['mysql']['user'] }}'@'localhost';"
    - require:
      - cmd: mysql.set-root-password
