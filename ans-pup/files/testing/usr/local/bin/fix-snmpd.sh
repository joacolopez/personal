#!/bin/bash
#
# Repara el usuario SNMP
#
# Proyectos Especiales.
# Gerencia de tecnologia.

PATH="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

/etc/init.d/snmpd stop
sed -i 's/#createUser/createUser/g' /etc/snmp/snmpd.conf
/etc/init.d/snmpd start
sleep 1
/etc/init.d/snmpd stop
sed -i 's/createUser/#createUser/g' /etc/snmp/snmpd.conf
/etc/init.d/snmpd start
