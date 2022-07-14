#!/usr/bin/python
#
# 20180823 - Agrega inventario.
#
# - 201306101452: Mod. Limpieza ssl puppet

from dialog import Dialog, DialogError
from credilib import *
from ConfigParser import NoOptionError
from subprocess import Popen, PIPE
from glob import glob
from copy import copy
from formencode.validators import IPAddress, Invalid
from StringIO import StringIO
import sys
import os
import re
import shutil
import ipcalc

enlaces_cfg = MyConfigParser('/etc/crediconn/enlaces.conf')
enlaces_cur = MyConfigParser('/etc/crediconn/currentconf/enlaces.conf')
filcfg = MyConfigParser('/etc/crediconn/filial.conf')
filcfg_cur = MyConfigParser('/etc/crediconn/currentconf/filial.conf')
LAN_DEV = filcfg.get(NETWORK, INTERFACE)
TEMPLATES_DIR = "/etc/crediconn/templates"

d = Dialog()

def menu(title, choices):
    """
    choices: ("Menu option", callback)
    """
    title = title
    items = []
    callbacks = {}
    callbacks_args = {}
    i = 1
    for choice in choices:
        items.append((str(i), choice[0]))
        callbacks[str(i)] = None
        callbacks_args[str(i)] = None
        if len(choice) > 1:
            callbacks[str(i)] = choice[1]
            if len(choice) > 2:
                callbacks_args[str(i)] = choice[2]
        i += 1

    opt = d.menu(title, choices=items, height=16, menu_height=14)
    if opt[0] == 0:
        callback = callbacks[opt[1]]
        callback_args = callbacks_args[opt[1]]
        if callback and callback_args:
            callback(callback_args)
        elif callback:
            callback()

        return int(opt[1])

    return 0

def dform(title, fields, cur_values = {}):
    # Original form_cmd = "dialog --form TITLE 20 70 18 "
    # Cambiado a 0 0 0 ya que en algunos casos fallaba
    form_cmd = "dialog --form TITLE 0 0 0"
    pos_y = 1
    for field in fields:
        if cur_values.has_key(field):
            form_cmd += " %s %d 1 %s %d 40 20 20" % \
                            (field, pos_y, cur_values[field], pos_y)
        else:
            form_cmd += " %s %d 1 SP %d 40 20 20" % (field, pos_y, pos_y)
            form_cmd_bak = form_cmd
        pos_y += 1

    form_args = []
    for arg in form_cmd.split():
        if arg == 'TITLE':
            arg = title
        elif arg == 'SP':
            arg = ''
        #Busco lo mensajes de texto en la seccion mensajes de la config
        #para hacer mas amigable el formulario.
        #No es muy elegante ponerlo aca, pero funciona.
        try:
            arg = enlaces_cfg.get(MENSAJES, arg)
        except NoOptionError:
            pass
        form_args.append(arg)

    d_form = Popen(form_args, stderr=PIPE)

    #No se porque pero readline() no me anduvo aca y lo hice asi
    values = re.split('\s+', d_form.stderr.read())
    values.remove('')

    ret_values = {}
    for field in fields:
        try:
            ret_values[field] = values.pop(0)
        except IndexError:
            ret_values[field] = False

    if d_form.wait() not in [ 0, 1 ]:
        die("Fallo la ejecucion de dialog --form: \"" + str(form_cmd_bak) + "\"")

    if d_form.returncode == 1:
        return False

    return ret_values

def die(msg):
    print msg
    sys.exit(-1)

def select_device(device, cur_values):
    device_activas = []
    for section in enlaces_cur.sections():
        try:
            device_activas.append(enlaces_cur.get(section, device))
        except NoOptionError:
            continue

    try:
        device_choices = [ (cur_values[device],) ]
    except KeyError:
        device_choices = []
    if device == 'interface':
        pattern = '/sys/class/net/*'
    else:
        pattern = '/sys/class/tty/tty*'
    for path in glob(pattern):
        dev = os.path.basename(path)
        if dev not in device_activas and dev != LAN_DEV and dev != LOOP_DEV:
            device_choices.append((dev,))

    if len(device_choices) == 0:
        d.msgbox("No hay mas %ss disponibles." % (device))
        return False

    msg = 'Seleccione la %s.' % device
    if len(cur_values) > 0:
        msg += '(La primer interfaces es la que esta actualmente configurada)' 
    device = menu(msg, device_choices)
    if device == 0:
        return False

    return device_choices[device-1][0]

def get_template(template):
    template_fd = open(TEMPLATES_DIR + "/" + template)
    template_path = template_fd.readline()
    if not template_path.startswith('PATH'):
        die("Error en el template, falta el PATH. " + template)

    template_path = re.sub("PATH:\s*", "", template_path)
    template_str = template_fd.read()

    return template_path, template_str

def conf_enlace(args):
    """
    Configura un enlace. 
    
    * Revisa la variables de la config, de los templates.
    * Le pregunta al usuario las variables que estan en los templates. Siempre
        y cuando no esten definidas en los .conf.
    * guarda la info en /etc/crediconn/currentconf.
    """

    enlace = args[0]
    tipo = args[1]
    if len(args) > 2:
        cur_values = args[2]
    else:
        cur_values = {}

    templates = []
    for i in [ enlace, DEFAULT ]:
        if enlaces_cfg.has_option(i, TEMPLATES):
            templates_opt = enlaces_cfg.get(i, TEMPLATES, raw=True)
            for template in templates_opt.split(','):
                templates.append(template.strip())
            break

    if len(templates) == 0:
        die('Error fatal, no hay template definido para proveedor ' + enlace)

    #Busco las variables que aparecen en el template, para preguntarselas
    #al usuario. Excepto que esas variables esten definidas en la config.
    vars = []
    for template in templates:
        template = get_template(template)[1]
        vars += re.findall(r"%\(([^)]*)\)s|.", template)
        #Lo convierto a set() para eliminar repeticiones

    vars = set(vars)
    try:
        vars.remove('')
    except ValueError:
        pass

    net_parms = {}
    #Asigno los valores de la section default al enlace
    net_parms.update(enlaces_cfg.options_d(DEFAULT))
    net_parms.update(enlaces_cfg.options_d(enlace))

    for attr, value in net_parms.iteritems():
        if value == ASK:
            vars.add(attr)

    if INTERFACE in vars:
        vars.remove(INTERFACE)
        iface = select_device(INTERFACE, cur_values)
        if not iface:
            return
        net_parms[INTERFACE] = iface
    elif TTY in vars:
        vars.remove(TTY)
        tty = select_device(TTY, cur_values)
        if not tty:
            return
        net_parms[TTY] = tty

    #Las variables del template que estan definidas como option en el 
    #.conf no se preguntan en el formulario.
    vars2 = copy(vars)
    for var in vars2:
        if var == SECTION:
            net_parms[var] = enlace
        if var in enlaces_cfg.options(enlace):
            net_parms[var] = enlaces_cfg.get(enlace, var)
        if var not in [ IP, NETMASK, GATEWAY, BANDWIDTH_UP, BANDWIDTH_DOWN,
            PROVIDER_NAME ]:
            vars.remove(var)
           
    if len(vars) > 0:
        form_ok = False
        while len(vars) > 0 and not form_ok:
            form_values = dform("Ingrese los datos del enlace", vars, 
                                cur_values)
            if not form_values:
                return

            form_ok = True
            for attr, value in form_values.iteritems():
                if attr in [ IP, NETMASK, GATEWAY ]:
                    if not value or not check_ip(value):
                        form_ok = False
                        d.msgbox(attr + " invalido: " + str(value))
        net_parms.update(form_values)

    net_parms["tipo"] = tipo

    msg = "Los datos son correctos? \n\n\n"
    msg += "Enlace: " + enlace + "\n"
    net_parms_keys = net_parms.keys()
    net_parms_keys.sort()
    for key in net_parms_keys:
        if key not in [ TEMPLATES, SECTION ]:
            msg += "%s: %s\n" % (key, net_parms[key])

    d.yesno(msg, 24, 60)

    if not enlaces_cur.has_section(enlace):
        enlaces_cur.add_section(enlace)
    for attr, value in net_parms.iteritems():
        enlaces_cur.set(enlace, attr, value)

    enlaces_cur.write_file()

    cmd = "/etc/crediconn/scripts/new_enlace " + enlace
    ret = os.system(cmd)

def add_enlace():
    """
    Agrega un enlace.
    """

    tipos_activos = []
    for section in enlaces_cur.sections():
        tipos_activos.append(enlaces_cur.get(section, ENLACE_TIPO))

    if len(tipos_activos) == 3:
        d.msgbox("Ya estan configurados todos los enlaces.")
        return

    tipo_enlace = []
    #Esta tuplas tienen que estar asi porque es la forma en que se las
    #paso al dialog.
    for i in [ (PRIMARIO,), (SECUNDARIO,), (CONTINGENCIA,) ]:
        if i[0] not in tipos_activos:
            tipo_enlace.append(i)

    opt = menu("Seleccione el tipo de enlace", tipo_enlace)
    if not opt:
        return
    tipo_enlace = tipo_enlace[opt-1][0]
    
    choices = []
    for section in enlaces_cfg.sections():
        if section in [ DEFAULT, MENSAJES ]:
            continue

        if enlaces_cur.has_section(section):
            continue

        if enlaces_cfg.has_option(section, MSG):
            msg = enlaces_cfg.get(section, MSG)
        else:
            msg = section
        choices.append((msg, conf_enlace, [section, tipo_enlace]))

        # Ordenamos alfabeticamente los enlaces
        choices.sort()

    if len(choices) == 0:
        d.msgbox("No hay enlaces disponibles.")
        return

    menu("Seleccione el tipo de enlace", choices)

def menu_enlaces(title):
    """
    Lista los enlaces configurados en un menu y devuelve el nombre del 
    enlace seleccionado.
    """
    choices = []
    for section in enlaces_cur.sections():
        enlace_info = '%s - %s' % \
                    (section, enlaces_cur.get(section, ENLACE_TIPO))
        choices.append((enlace_info,))

    if len(choices) == 0:
        d.msgbox("No hay enlaces configurados.")
        return False

    enlace = menu(title, choices)
    if not enlace:
        return False
    enlace = choices[enlace-1][0]
    enlace = enlace.split()[0]

    return enlace

def del_enlace():
    enlace = menu_enlaces("Seleccione el enlace que desea eliminar")
    if not enlace:
        return

    ret = d.yesno("Esta seguro que quiere borrar %s?" % (enlace))
    if ret != 0:
        return

    enlaces_cur.remove_section(enlace)
    enlaces_cur.write_file()

def mod_enlace():
    enlace = menu_enlaces("Seleccione el enlace que desea modificar")
    if not enlace:
        return

    options = enlaces_cur.options_d(enlace)
    conf_enlace([enlace, options[ENLACE_TIPO], options])


def ver_enlaces():
    enlace = menu_enlaces("Seleccione el enlace para ver mas informacion")
    if not enlace:
        return

    msg = "Enlace: " + enlace + "\n"
    for item in enlaces_cur.items(enlace, raw=True):
        msg += "%s: %s\n" % item

    d.msgbox(msg, 15, 60)

def salir():
    ret = d.yesno("Desea aplicar la configuracion antes de salir?")
    if ret == 0:
        apply_conf()
    sys.exit(0)

def filial_net_prefix(filial):
    fil_num = int(filial)
    octeto2_drago = filcfg.getint(NETWORK, OCTETO2_DRAGO)
    octeto2_vera = filcfg.getint(NETWORK, OCTETO2_VERA)
    octeto3 = fil_num
    while octeto3 > 254:
        octeto3 -= 254
        octeto2_drago += 1
        octeto2_vera += 1

    net_prefix_drago = '10.%d.%d' % (octeto2_drago, octeto3)
    net_prefix_vera = '10.%d.%d' % (octeto2_vera, octeto3)

    return net_prefix_drago, net_prefix_vera

def gen_conf(filial):
    """
    Genera la config de la filial automatico en base al numero de fil.
    """
    fil_num = int(filial)
    inventario = pregunta_valida_inventario()
    net_prefix_drago, net_prefix_vera = filial_net_prefix(filial)
    filial_ip_drago1 = net_prefix_drago + OCTETO4_1
    filial_ip_drago2 = net_prefix_drago + OCTETO4_2
    filial_ip_vera1 = net_prefix_vera + OCTETO4_1
    filial_ip_vera2 = net_prefix_vera + OCTETO4_2
    filial_mask = NETMASK_FILIAL
    if not filcfg_cur.has_section(NETWORK):
        filcfg_cur.add_section(NETWORK)
    if not filcfg_cur.has_section(GLOBAL):
        filcfg_cur.add_section(GLOBAL)
    for section in filcfg.sections():
        for attr, value in filcfg.options_d(section).iteritems():
            filcfg_cur.set(section, attr, value)
    filcfg_cur.set(GLOBAL, INVENTARIO, inventario)
    filcfg_cur.set(GLOBAL, FILIAL, filial)
    filcfg_cur.set(GLOBAL, ZFILIAL, filial.zfill(3))
    filcfg_cur.set(NETWORK, LAN_IP_DRAGO1, filial_ip_drago1)
    filcfg_cur.set(NETWORK, LAN_IP_DRAGO2, filial_ip_drago2)
    filcfg_cur.set(NETWORK, LAN_IP_VERA1, filial_ip_vera1)
    filcfg_cur.set(NETWORK, LAN_IP_VERA2, filial_ip_vera2)
    filcfg_cur.set(NETWORK, MASK, filial_mask)
    filcfg_cur.set(NETWORK, INTERFACE, filcfg.get(NETWORK, INTERFACE))
    filcfg_cur.set(NETWORK, NET_PREFIX_DRAGO, net_prefix_drago)
    filcfg_cur.set(NETWORK, NET_PREFIX_VERA, net_prefix_vera)
    filcfg_cur.set(NETWORK, INTERFACE, filcfg.get(NETWORK, INTERFACE))
    filcfg_cur.set(NETWORK, INTERFACE, filcfg.get(NETWORK, INTERFACE))
    filcfg_cur.set(NETWORK, FILIAL_ZONE, 
                    'filial%03s.' % (filial) + filcfg.get(NETWORK, PARENT_ZONE))
    filcfg_cur.write_file()
    ###
    ### Borro los links simbolicos a los certificados viejos
    cmd = '/usr/bin/find /var/lib/puppet/ssl -name "*pem" -exec rm {} \+'
    ret = os.system(cmd)
    ###
    cmd = "/etc/crediconn/scripts/config_filial " + str(filial)
    ret = os.system(cmd)

def config_filial():
    while True:
        filial = d.inputbox("Ingrese el numero de filial")
        if filial[0] != 0:
            break
        if filial[1].isdigit():
            gen_conf(filial[1])
            break
        else:
            d.msgbox("El valor debe ser numerico.")

def pregunta_valida_inventario():
    while True:
        inventario = d.inputbox("Ingrese el numero de inventario del nodo sin la \"J\" ")
        if inventario[0] != 0:
            break
        if len(inventario[1]) == 8 and inventario[1].isdigit(): 
	    return "J" + inventario[1]
            break
        else:
            d.msgbox("El valor debe componerse de 8 numeros (sin la J):\n" + inventario[1] + " no cumple con la condicion." )

def cargar_inventario():
    inventario = pregunta_valida_inventario()
    cmd = "/bin/sed -i '/inventario=/c\inventario=\"" + inventario + "\"'  /etc/credicoop_info_nodo.ini"
    ret = os.system(cmd)
    ### Hacer la magia.

def write_template(template, vars):
    """
    Escribe el template con las variables reemplazadas.
    @template: nombre del template
    @vars: diccionario con las variables a reemplazar
    """
    try:
        template_path, template_str = get_template(template)
        template_path = template_path.strip()
        template_path = template_path % vars
        template_fd = open(template_path, 'a')
        template_str = template_str % vars
        template_fd.write(template_str)
        template_fd.close()
    except Exception, e:
        die('Error generando template %s: %s' % (template, str(e)))

def write_templates(enlace, num):
    templates = enlaces_cur.get(enlace, TEMPLATES)
    templates = templates.split(',')
    vars = { 
            FILIAL : filcfg_cur.get(GLOBAL, FILIAL),
            NET_PREFIX_DRAGO : filcfg_cur.get(NETWORK, NET_PREFIX_DRAGO),
            NET_PREFIX_VERA : filcfg_cur.get(NETWORK, NET_PREFIX_VERA),
            OCTETO4_LAN : 254 - int(num)
            }

    vars.update(enlaces_cur.options_d(enlace))
    for template in templates:
        template = template.strip()
        write_template(template, vars)

def apply_conf(silent=False):
    cmd = "/etc/crediconn/scripts/pre_apply_conf"
    os.system(cmd)
    for xfile in glob(TEMPLATES_DIR + "/*"):
        template = os.path.basename(xfile)
        template_path, template_str = get_template(template)
        template_path = template_path.strip()
        ### Sacamos el backup de las versiones anteriores
        if os.path.exists(template_path):
           ### No hacemos mas backup de la conf anterior
           ### shutil.move(template_path, template_path + '.old')
           os.remove(template_path)

    fil_templates = filcfg.get(GLOBAL, TEMPLATES)
    vars = filcfg_cur.options_d(NETWORK)
    vars.update(filcfg_cur.options_d(GLOBAL))
    for template in fil_templates.split(','):
        write_template(template, vars)

    num = 0
    for enlace in enlaces_cur.sections():
        write_templates(enlace, num)
        num += 1

    for script in glob('/etc/crediconn/scripts/*'):
        os.chmod(script, 0755)

    for f in glob('/etc/crediconn/currentconf/*'):
        os.chmod(f, 0644)

    cmd = "/etc/crediconn/scripts/post_apply_conf"
    os.system(cmd)

    if not silent:
        d.msgbox('Configuracion aplicada')

    return

def gen_cert():
    openssl_cnf = filcfg.get(GLOBAL, OPENSSL_CNF)
    filial = filcfg_cur.get(GLOBAL, FILIAL)
    cmd = "/etc/crediconn/scripts/new_cert_req " + filial
    ret = os.system(cmd)
    if ret != 0:
        die("Error falta, no se pudo crear el certificado") 

def main_menu():
    choices = [ 
        ("Configurar filial", config_filial),
        ("Generar solicitud del certificado X.509", gen_cert),
        ("Agregar enlace", add_enlace),
        ("Borrar enlace", del_enlace),
        ("Modificar enlace", mod_enlace),
        ("Ver enlaces", ver_enlaces),
        ("Cargar Inventario (JXXXXXXX)", cargar_inventario),
        ("Aplicar configuracion", apply_conf),
        ("Salir", salir) ]
    option = menu("Seleccione la operacion", choices)

if len(sys.argv) > 1 and sys.argv[1] == 'apply':
    apply_conf(True)
    sys.exit(0)

while True:
    try:
        main_menu()
    except DialogError:
        print 'Error', os.environ["DIALOG_ERROR"]
        sys.exit(-1)

