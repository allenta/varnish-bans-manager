Exec {
  path => ['/bin/', '/sbin/' , '/usr/bin/', '/usr/sbin/', '/usr/local/bin']
}

class configuration {
  $mysql_db_name = 'varnish_bans_manager'
  $mysql_user = 'bob'
  $mysql_password = 's3cr3t'
}

class system-update {
  Class['configuration'] -> Class['system-update']

  exec {'apt-get-update':
    user => 'root',
    command => 'apt-get update',
  }

  package {['python', 'python-pip', 'curl', 'mysql-server', 'mysql-client', 'python-dev', 'libmysqlclient-dev', 'libjpeg8', 'libjpeg62-dev', 'libfreetype6', 'libfreetype6-dev', 'zlib1g-dev', 'yui-compressor', 'gettext', 'postfix', 'mailutils', 'ruby1.9.1-dev']:
    ensure => present,
    require => Exec['apt-get-update'],
  }

  file {'/usr/lib/libjpeg.so':
    ensure => link,
    mode => 0644,
    owner => 'root',
    group => 'root',
    target => $architecture ? {
      'i386' => '/usr/lib/i386-linux-gnu/libjpeg.so',
      default => '/usr/lib/x86_64-linux-gnu/libjpeg.so',
    },
  }

  file {'/usr/lib/libfreetype.so':
    ensure => link,
    mode => 0644,
    owner => 'root',
    group => 'root',
    target => $architecture ? {
      'i386' => '/usr/lib/i386-linux-gnu/libfreetype.so',
      default => '/usr/lib/x86_64-linux-gnu/libfreetype.so',
    },
  }

  file {'/usr/lib/libz.so':
    ensure => link,
    mode => 0644,
    owner => 'root',
    group => 'root',
    target => $architecture ? {
      'i386' => '/usr/lib/i386-linux-gnu/libz.so',
      default => '/usr/lib/x86_64-linux-gnu/libz.so',
    },
  }
}

class virtualenv {
  Class['system-update'] -> Class['virtualenv']

  package {['virtualenv']:
    ensure   => 'installed',
    provider => 'pip',
  }

  exec {'create-virtualenv':
    creates => '/home/vagrant/virtualenv/',
    user => 'vagrant',
    command => 'virtualenv /home/vagrant/virtualenv',
    require => Package['virtualenv'],
  }

  exec {'install-virtualenv-dependencies':
    creates => '/home/vagrant/.vagrant.install-virtualenv-dependencies',
    user => 'vagrant',
    provider => 'shell',
    command => '. /home/vagrant/virtualenv/bin/activate && pip install MySQL-python -r /vagrant/requirements.txt && touch /home/vagrant/.vagrant.install-virtualenv-dependencies',
    require => Exec['create-virtualenv'],
    timeout => 0,
  }
}

class mysql {
  Class['system-update'] -> Class['mysql']

  service {['mysql']:
    enable => true,
    ensure => running,
  }

  exec {'set-mysql-root-password':
    user => 'vagrant',
    unless => "mysqladmin -uroot -p${configuration::mysql_password} status",
    command => "mysqladmin -uroot password ${configuration::mysql_password}",
    require => Service['mysql'],
  }

  exec {'create-mysql-db':
    user => 'vagrant',
    unless => "mysql -u${configuration::mysql_user} -p${configuration::mysql_password} ${configuration::mysql_db_name}",
    command => "mysql -uroot -p${configuration::mysql_password} -e \"CREATE DATABASE ${configuration::mysql_db_name}; CREATE USER '${configuration::mysql_user}'@'localhost' IDENTIFIED BY '${configuration::mysql_password}'; GRANT ALL PRIVILEGES ON ${configuration::mysql_db_name}.* TO '${configuration::mysql_user}'@'localhost';\"",
    require => Exec['set-mysql-root-password'],
  }
}

class varnish {
  Class['system-update'] -> Class['varnish']

  exec {'add-varnish-apt-key':
    user => 'root',
    creates => '/home/vagrant/.vagrant.add-varnish-apt-key',
    command => 'curl http://repo.varnish-cache.org/debian/GPG-key.txt | apt-key add - && touch /home/vagrant/.vagrant.add-varnish-apt-key',
  }

  file {'/etc/apt/sources.list.d/varnish.list':
    ensure => present,
    mode => 0644,
    owner => 'root',
    group => 'root',
    source => '/vagrant/extras/envs/dev/puppet/files/apt/varnish.list',
    require => Exec['add-varnish-apt-key'],
  }

  exec {'apt-get-update-varnish':
    user => 'root',
    creates => '/usr/sbin/varnishd',
    command => 'apt-get update',
    require => File['/etc/apt/sources.list.d/varnish.list'],
  }

  package {'varnish':
    ensure => present,
    require => Exec['apt-get-update-varnish'],
  }

  service {'varnish':
    enable => true,
    ensure => running,
    require => Package['varnish'],
  }
}

class postfix {
  Class['system-update'] -> Class['postfix']

  service {['postfix']:
    enable => true,
    ensure => running,
  }

  file {'/etc/mailname':
    ensure => present,
    mode => 0644,
    owner => 'root',
    group => 'root',
    source => '/vagrant/extras/envs/dev/puppet/files/postfix/mailname',
    notify => Service['postfix'],
  }

  file {'/etc/postfix/main.cf':
    ensure => present,
    mode => 0644,
    owner => 'root',
    group => 'root',
    source => '/vagrant/extras/envs/dev/puppet/files/postfix/main.cf',
    notify => Service['postfix'],
  }
}

class user {
  Class['system-update'] -> Class['user']

  package {['sass', 'compass']:
    ensure   => 'installed',
    provider => 'gem',
  }

  file {'/home/vagrant/.profile':
    ensure => present,
    mode => 0644,
    owner => 'vagrant',
    group => 'vagrant',
    source => '/vagrant/extras/envs/dev/puppet/files/profile',
  }

  file {'/home/vagrant/source':
    ensure => link,
    mode => 0644,
    target => '/vagrant',
  }

  file {['/vagrant/files']:
    ensure => directory,
    mode => 0644,
  }
}

include configuration
include system-update
include virtualenv
include mysql
include varnish
include postfix
include user
