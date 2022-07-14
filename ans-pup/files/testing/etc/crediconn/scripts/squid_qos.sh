#!/bin/bash
# Adecuación de QoS para Squid (Web-CACHE)
#
# Version 1.1 - 1-02-2017
#	Agrega soporte para Squid v3
#
# Version 1 - 8-05-2015
#	Original.
#
# Proyectos Especiales.
# Gerencia de tecnología.
# Banco Credicoop Coop. Ltdo.

PATH="/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin"
tipo="desconocida"

# Verifico si es Squid v3
squid3 -v 2> /dev/null 1>/dev/null
if [ $? -eq 0 ] ; then
	HomeSquid="/etc/squid3"
	CMD="/usr/sbin/squid3"
else
	HomeSquid="/etc/squid"
	CMD="/usr/sbin/squid"
	
fi

SquidConf="$HomeSquid/squid.conf"

function evaluar_conectividad () {
	STATUS=$(cat /tmp/crediconn.status )
	case "$STATUS" in
		0000-00)
			# Contingencia
			tipo="estatico"
			;;
		00??-?0|0?1?-00|?0?1-10)
			# Secundario
			tipo="secundario"
			;;
		??00-?0|1?0?-00|?1?0-10)
			# Primario
			tipo="primario"
			;;
		????-?1)
			# Balanceo
			tipo="dos_vinculos"
			;;
		*)
                	credilog.py "Squid - Qos - No se pudo determinar estado $STATUS"
			exit 1 
			;;
	esac
}

function TestPreliminar () {
ESTADOS=( '0000-00' '0001-10' '0010-00' '0011-00' '0100-10' '0100-10' '0110-10' '0110-11' '0110-00' '0110-01' '1000-00' '1001-01' '1000-00' '1001-10' '1100-00' '1001-11' '1100-00' '1001-01' )

for AUX in ${ESTADOS[@]} ; do
	echo "$AUX" > /tmp/crediconn.status
	evaluar_conectividad
        if [ -r $HomeSquid/squid_$tipo.conf ] ; then
                # si el archivo destino seleccionado existe y es legible, efectuamos el cambio.
		ArchivoSquid=$HomeSquid/squid_$tipo.conf
		echo "STATUS: $STATUS ----------------------------------------"
                echo "CREDILOG: Squid - Cambiando QoS a $ArchivoSquid"
                echo "ln -sf $ArchivoSquid $SquidConf"
		echo "--------------------------------------------------------"
        else
                echo "CREDILOG:Squid - No se puede aplicar cambios a Squid por QoS. $ArchivoSquid inusable. Revisar!!!!"
        fi
done
}

function TestAplicandoCambio () {
ESTADOS=( '0000-00' '0001-10' '0010-00' '0011-00' '0100-10' '0100-10' '0110-10' '0110-11' '0110-00' '0110-01' '1000-00' '1001-01' '1000-00' '1001-10' '1100-00' '1001-11' '1100-00' '1001-01' )

for AUX in ${ESTADOS[@]} ; do
	echo "$AUX" > /tmp/crediconn.status
	AplicarQOS
done
}

function AplicarQOS () {
	evaluar_conectividad
	if [ -h $HomeSquid/squid.conf ] ; then
		# Si es un link simbolico, entiendo que tengo que cambiar QoS.
		# Caso contrario, tiene la configuración legacy aún.

		if [ -r $HomeSquid/squid_$tipo.conf ] ; then
			# si el archivo destino seleccionado existe y es legible, efectuamos el cambio.
			ArchivoSquid=$HomeSquid/squid_$tipo.conf
			if [ "$(diff -q $SquidConf $ArchivoSquid)" ] ; then
				# Solo si son distintos, aplico cambio.
				credilog.py "Squid - Cambiando QoS a $ArchivoSquid"
				ln -sf $ArchivoSquid $SquidConf
				${CMD} -k reconfigure
			fi
		else
			credilog.py "Squid QoS - No se puede aplicar cambios a Squid por QoS (TIPO=$tipo). $ArchivoSquid inusable. Revisar!!!!"
		fi
	else
			credilog.py "Squid - Qos - No se aplican cambios por Squid con configuracion estatica."
	fi
}

function usage {
        echo -e "\n\n\n usage $0 [--test] [--QoS]\n"
        echo -e "	--test: Muestra en pantalla la evaluación de la conectividad, forzando el estado en los FLAGs. No aplica configuracion"
        echo -e "	--test-forced: impacta cambios en configuración a partir de lista de estados a evaluar."
       echo -e "	--QoS: Aplica los cambios necesarios según conectividad."
        echo -e "\n\n"
        exit 1

}

################### MAIN ######################################################
#  Tratamiendo del configuracion de squid en funcion del canal activo.
#
#
# -----------------------------------------------------------------------------

if [ $# -lt 1 ]; then
        usage
fi

while [ $# -gt 0 ] ;  do
        x=$1
        case $x in
	'--test')
		TestPreliminar
		;;
	'--QoS'|'--qos'|--'QOS'|--'qOs')
		AplicarQOS
		;;
	'--test-forced')
		TestAplicandoCambio
		;;
	*)
		usage
		;;
	esac
	shift
done

