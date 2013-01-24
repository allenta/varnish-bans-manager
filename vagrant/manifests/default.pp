class phase1 {
  exec {'apt-get-update':
    command => '/usr/bin/apt-get update'
  }

  package {['python', 'python-pip', 'mysql-server', 'mysql-client', 'rubygems', 'python-dev', 'libmysqlclient-dev', 'libjpeg8', 'libjpeg62-dev', 'libfreetype6', 'libfreetype6-dev', 'zlib1g-dev', 'yui-compressor', 'gettext', 'varnish', 'postfix', 'mailutils']:
    ensure => present,
    require => Exec['apt-get-update'],
  }

  file {'/usr/lib/libjpeg.so':
    ensure => link,
    mode => 0644,
    owner => 'root',
    group => 'root',
    target => '/usr/lib/x86_64-linux-gnu/libjpeg.so',
  }

  file {'/usr/lib/libfreetype.so':
    ensure => link,
    mode => 0644,
    owner => 'root',
    group => 'root',
    target => '/usr/lib/x86_64-linux-gnu/libfreetype.so',
  }

  file {'/usr/lib/libz.so':
    ensure => link,
    mode => 0644,
    owner => 'root',
    group => 'root',
    target => '/usr/lib/x86_64-linux-gnu/libz.so',
  }
}

class phase2 {
  Class['phase1'] -> Class['phase2']

  package {['sass', 'compass']:
    ensure   => 'installed',
    provider => 'gem',
  }

  package {['virtualenv']:
    ensure   => 'installed',
    provider => 'pip',
  }

  service {['mysql', 'varnish', 'postfix']:
    enable => true,
    ensure => running,
  }

  file {'/etc/mailname':
    ensure => present,
    mode => 0644,
    owner => 'root',
    group => 'root',
    source => '/vagrant/vagrant/files/mailname',
    notify => Service['postfix'],
  }

  file {'/etc/postfix/main.cf':
    ensure => present,
    mode => 0644,
    owner => 'root',
    group => 'root',
    source => '/vagrant/vagrant/files/postfix-main.cf',
    notify => Service['postfix'],
  }

  $mysql_user = "bob"
  $mysql_password = "s3cr3t"
  $mysql_db = "varnish_bans_manager"

  exec {'set-mysql-root-password':
    unless => "mysqladmin -uroot -p$mysql_password status",
    path => ['/bin', '/usr/bin'],
    command => "mysqladmin -uroot password $mysql_password",
    require => Service['mysql'],
  }

  exec {'create-mysql-db':
    unless => "/usr/bin/mysql -u${mysql_user} -p${mysql_password} ${mysql_db}",
    path => ['/bin', '/usr/bin'],
    command => "mysql -uroot -p$mysql_password -e \"CREATE DATABASE ${mysql_db}; CREATE USER '${mysql_user}'@'localhost' IDENTIFIED BY '${mysql_password}'; GRANT ALL PRIVILEGES ON ${mysql_db}.* TO '${mysql_user}'@'localhost';\"",
    require => Exec['set-mysql-root-password'],
  }

  exec {'create-virtualenv':
    creates => '/home/vagrant/.virtualenvs/varnish-bans-manager/',
    user => 'vagrant',
    path => ['/bin', '/usr/bin', '/usr/local/bin'],
    command => 'mkdir -p /home/vagrant/.virtualenvs; virtualenv /home/vagrant/.virtualenvs/varnish-bans-manager',
    require => Package['virtualenv'],
  }

  exec {'install-virtualenv-dependencies':
    path => ['/bin', '/usr/bin'],
    user => 'vagrant',
    provider => 'shell',
    command => '. /home/vagrant/varnish-bans-manager/bin/activate; pip install "MySQL-python" "django >= 1.4.3" "django-celery >= 3.0.11" "django-mediagenerator >= 1.11" "django-templated-email >= 0.4.7" "gunicorn >= 0.14.6" "eventlet >= 0.9.17" "simplejson >= 2.1.6" "path.py >= 2.4.1" "ordereddict >= 1.1" "pytz" "pil" "south >= 0.7.6"',
    require => Exec['create-virtualenv'],
  }

  file {'/home/vagrant/.profile':
    ensure => present,
    mode => 0644,
    owner => 'vagrant',
    group => 'vagrant',
    source => '/vagrant/vagrant/files/profile',
  }

  file {'/home/vagrant/source':
    ensure => link,
    mode => 0644,
    owner => 'vagrant',
    group => 'vagrant',
    target => '/vagrant',
  }

  file {['/vagrant/files']:
    ensure => directory,
    mode => 0644,
    owner => 'vagrant',
    group => 'vagrant',
  }
}

include phase1
include phase2
