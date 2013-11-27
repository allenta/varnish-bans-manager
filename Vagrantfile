# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant.configure('2') do |config|
  config.vm.box = 'precise64'
  config.vm.hostname = 'dev'
  config.vm.box_url = 'http://files.vagrantup.com/precise64.box'

  config.vm.provider :virtualbox do |vb|
    vb.customize [
      'modifyvm', :id,
      '--memory', '512',
      '--name', 'Varnish Bans Manager',
    ]
  end

  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = 'extras/vagrant/manifests'
  end

  # /etc/hosts
  # 192.168.100.102 vbm.d2c.dev
  config.vm.network :forwarded_port, guest: 9000, host: 9000
  config.vm.network :private_network, ip: '192.168.100.102'
  config.vm.network :public_network

  config.vm.synced_folder '.', '/vagrant', :nfs => false
end
