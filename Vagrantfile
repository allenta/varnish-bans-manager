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

  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = 'extras/envs/dev/puppet/manifests'
  end

  # /etc/hosts
  # 192.168.100.102 vbm.allenta.dev
  config.vm.network :forwarded_port, guest: 9000, host: 9000
  config.vm.network :private_network, ip: '192.168.100.102'
  config.vm.network :public_network

  config.vm.synced_folder '.', '/vagrant', :nfs => false
end
