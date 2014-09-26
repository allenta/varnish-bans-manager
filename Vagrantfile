# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure('2') do |config|
  config.vm.box = 'ubuntu/trusty64'
  config.vm.box_version = '=14.04'
  config.vm.box_check_update = true
  config.vm.hostname = 'dev'

  config.vm.provider :virtualbox do |vb|
    vb.customize [
      'modifyvm', :id,
      '--memory', '512',
      '--name', 'Varnish Bans Manager',
      '--natdnshostresolver1', 'on',
      '--accelerate3d', 'off',
    ]
  end

  config.vm.provision :salt do |salt|
    salt.pillar({
      'host' => 'allenta.com',
      'mysql' => {
        'name' => 'varnish_bans_manager',
        'user' => 'bob',
        'password' => 's3cr3t',
      },
    })

    salt.minion_config = 'extras/envs/dev/salt/minion'
    salt.run_highstate = true
    salt.verbose = true
    salt.log_level = 'info'
    salt.colorize = true
  end

  # /etc/hosts
  # 192.168.100.102 vbm.allenta.dev
  config.vm.network :forwarded_port, guest: 9000, host: 9000
  config.vm.network :private_network, ip: '192.168.100.102'
  config.vm.network :public_network

  config.vm.synced_folder '.', '/vagrant', :nfs => false

  config.vm.synced_folder 'extras/envs/dev/salt/roots', '/srv', :nfs => false
end
