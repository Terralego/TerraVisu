===============
Troubleshooting
===============

--------------------------------------
Elastic search container doesn't start
--------------------------------------

If you have:

bootstrap check failure [1] of [1]:
max virtual memory areas vm.max_map_count [xxx] is too low, increase to at least [yyy]

Then you need to increase the vm.max_map_count on your host machine.


..  code-block:: bash

    sudo nano /etc/sysctl.conf
    vm.max_map_count=262144

Then reboot your machine.
