global.packages:
  pkg.installed:
    - refresh: True
    - names:
      - curl
      - gettext
      - libfreetype6
      - libfreetype6-dev
      - libjpeg62-dev
      - libjpeg8
      - libmysqlclient-dev
      - mailutils
      - mysql-client
      - mysql-server
      - postfix
      - python
      - python-dev
      - python-pip
      - ruby1.9.1-dev
      - yui-compressor
      - zlib1g-dev

/usr/lib/libjpeg.so:
  file.symlink:
    - user: root
    - group: root
    - mode: 644
    - target: /usr/lib/x86_64-linux-gnu/libjpeg.so

/usr/lib/libfreetype.so:
  file.symlink:
    - user: root
    - group: root
    - mode: 644
    - target: /usr/lib/x86_64-linux-gnu/libfreetype.so

/usr/lib/libz.so:
  file.symlink:
    - user: root
    - group: root
    - mode: 644
    - target: /usr/lib/x86_64-linux-gnu/libz.so
