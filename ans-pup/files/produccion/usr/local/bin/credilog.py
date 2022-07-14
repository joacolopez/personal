#!/usr/bin/python
#
# Para usar desde los scripts en bash asi queda con el mismo formato
# que el Crediconn
#

import logging
import sys

logger = logging.getLogger('crediconn')
hdlr = logging.FileHandler('/var/log/credi.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

logger.info(" ".join(sys.argv[1:]))
