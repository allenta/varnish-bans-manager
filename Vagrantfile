# -*- mode: ruby -*-
# vi: set ft=ruby :

Vagrant::Config.run do |config|
  config.vm.box = 'precise64'

  config.vm.box_url = 'http://files.vagrantup.com/precise64.box'

  config.vm.provision :puppet do |puppet|
    puppet.manifests_path = 'vagrant/manifests'
  end

  config.vm.customize [
    'modifyvm', :id,
    '--memory', '512',
    '--name', 'Varnish Bans Manager',
  ]

  config.vm.forward_port 9000, 9000
end
