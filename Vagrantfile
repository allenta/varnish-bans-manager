# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box = 'precise64'
  config.vm.host_name = 'dev'
  config.vm.box_url = 'http://files.vagrantup.com/precise64.box'

  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = 'vagrant/manifests'
  end

  config.vm.customize [
    'modifyvm', :id,
    '--memory', '512',
    '--name', 'Varnish Bans Manager',
  ]

  # /etc/hosts
  # 192.168.100.102 vbm.d2c.dev
  config.vm.forward_port 9000, 9000
  config.vm.network :hostonly, '192.168.100.102'
  config.vm.network :bridged
end
