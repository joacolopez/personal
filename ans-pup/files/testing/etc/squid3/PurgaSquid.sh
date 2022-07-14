#!/bin/bash
### BEGIN INIT INFO
# Provides:          Purga de URLs
# Required-Start:    
# Required-Stop:     
# Default-Start:     
# Default-Stop:      
# Short-Description: 
# Description:       
### END INIT INFO

for URL in $( cat /usr/local/bin/PurgaSquid.txt )  ; do squidclient -h 127.0.0.1 -m PURGE $URL ;  done
