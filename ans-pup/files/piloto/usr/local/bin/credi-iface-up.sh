#!/bin/bash
#
# Script que configura las rutas y otras cosas para cada enlace
# Especifico para interfaces dinamicas con carga de gateway
# v1.3
#	Se cambia la extracción de gateway para nodos V5.1 desde el archivo de 
#	leases para DHCP-client.
#
# Proyectos Especiales
# Gerencia de tecnología.
# Banco Credicoop Coop Ltdo.

#set -x
#exec > /tmp/credi-iface.out 2>&1

ENLACE="$1"
CREDICFG="credicfg.py /etc/crediconn/currentconf/enlaces.conf"
# CONECTIVIDAD Puede ser "dsl" o "ip_fija" o "dhcp"
CONECTIVIDAD=$($CREDICFG $ENLACE conectividad)
# Indica las direcciones IP de los concentradores para ese
# servicios o tipo de conectividad.
CONCENTRADOR_DRAGO=$($CREDICFG $ENLACE concentrador_drago)
CONCENTRADOR_VERA=$($CREDICFG $ENLACE concentrador_vera)

# Esto da si es secundario o primario.
#TIPO=$($CREDICFG $ENLACE tipo)
# Indica la ethX que corresponda (fisicas).
INTERFACE=$($CREDICFG $ENLACE interface)
#CURR_CONF="/etc/crediconn/currentconf/enlaces.conf"
#FILCFG="credicfg.py /etc/crediconn/currentconf/filial.conf"
#LAN_IP_DRAGO1=$($FILCFG network lan_ip_drago1)
#RUTAS_ACTUALES=`/sbin/ip route`
#GW_ACTUALES=`/sbin/ip route | grep default`
GATEWAY=""

function DameGateway () {
	FILE="/var/lib/dhcp/dhclient.$INTERFACE.leases"
	if [ ! -e $FILE ] ; then
		echo "No existe archivo $FILE"
		exit 1
	fi
	cat $FILE | grep '^  option routers '  | tail  -n  1 | awk '{print $3}' | sed "s/;//g"
}

if [ $CONECTIVIDAD == "dsl" ]; then
	index=0
        maxindex=9
        /usr/local/bin/credilog.py "ADSL - Espero 15 segundos que levante la interfaz ppp"
        sleep 15
	# Se detecta el subíndice de interfaz PPP (ej. ppp0).
	while [[  $( ip r l | grep ppp$index | head -n 1 ) == "" ]]&&[[ $index -lt $[$maxindex+1] ]]
	do
		index=$[$index+1]
	done
	if [[ $index -lt $maxindex ]] ; then
		ip r r $CONCENTRADOR_DRAGO dev ppp$index 2>/dev/null
		ip r r $CONCENTRADOR_VERA dev ppp$index 2>/dev/null
		/usr/sbin/ipsec update >/dev/null 2>&1
		exit 0
	else
		/usr/local/bin/credilog.py "ADSL - No se detecta interfaz PPP, index llego a ppp$index"
		exit 0
	fi
elif [ $CONECTIVIDAD == "dhcp" ] ; then
        /usr/local/bin/credilog.py "DHCP - Espero 4 segundos que levante la interfaz DHCP"
        sleep 4
	# No funciona con debian v7 o superior.
	#GATEWAY=$( ip r l | grep -i default | grep -i $INTERFACE | awk '{print $3}' )
	GATEWAY=$(DameGateway)
	if [ -z "$GATEWAY" ]; then
		/usr/local/bin/credilog.py "DHCP - No se detecta GATEWAY en $INTERFACE"
		exit 0
	else
		if [[ -z  $(echo "$ENLACE" | grep -i -E "interna") ]]; then
		 	ip r r $CONCENTRADOR_DRAGO via $GATEWAY 2>/dev/null
		 	ip r r $CONCENTRADOR_VERA via $GATEWAY 2>/dev/null
		else
		 	ip r r $CONCENTRADOR_DRAGO via $CONCENTRADOR_DRAGO 2>/dev/null
		 	ip r r $CONCENTRADOR_VERA  via $CONCENTRADOR_VERA 2>/dev/null
		fi
		/usr/sbin/ipsec update >/dev/null 2>&1
	fi
else
	/usr/local/bin/credilog.py "$0 - Este script no aplica a $1. Es para DHCP o PPPoE. Revisar configuracion!"
fi

