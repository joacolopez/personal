#!/bin/bash
# Luis Vinay - XTech

# Carga las reglas de iptables para que el trafico saliente por 
# el puerto 80 (http) sea redirigido al puerto 3301 (wanproxy)

# Este Script quedó caduco, reemplazado por el wanproxy-mon.sh
# 2013
# GerTec.

#SERVERS="10.1.1.40 10.1.1.43"
SERVERS=""
IPTABLES_BIN="/sbin/iptables"

updown(){
   # $1 = A o D
   # $2 = IP DEL SERVER
   RULE="PREROUTING -d ${2} -p tcp --dport 80 -j REDIRECT --to 3301"
   /sbin/iptables-save > /tmp/kk.$$
   if [ $1 == "A" ]; then
   	grep "$SERVER" -q /tmp/kk.$$ || $IPTABLES_BIN -t nat -${1} ${RULE} 2>/tmp/kk.$$
   else
   	grep "$SERVER" -q /tmp/kk.$$ && $IPTABLES_BIN -t nat -${1} ${RULE}
   fi
   rm /tmp/kk.$$ 2>/dev/null
}

case "$1" in
	up)  ACTION="A"
		for SERVER in $SERVERS
		do
		   updown ${ACTION} ${SERVER}
		done 
		exit 0
		;;
	down)  ACTION="D"
		for SERVER in $SERVERS
		do
		   updown ${ACTION} ${SERVER}
		done 
		exit 0
		;;
	*) echo -e "\nwanproxy-rules.sh: Carga las reglas de iptables para que el \n                   trafico saliente por el puerto 80 (http) \n                   sea redirigido al puerto 3301 (wanproxy)\n"
	   echo -e "USO: wanproxy-rules.sh [ up | down ]\n"
		exit 0
		;;
esac

exit 0
