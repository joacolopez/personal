# Consideraciones de diseño

Como parte del proceso de migracion los recursos Puppet fueron traducidos a tasks Ansible en playbooks correspondientes a las clases principales.
Se crearon roles para las operaciones mas utilizadas, como mecanismo de reutilizacion, para ofrecer mayo mantenibilidad.

## Repositorio de archivos

Se incorporo al proyecto un repositorio de archivos que reemplaza al fileserver de Puppet, este se encuentra separado por categorias ( piloto, testing y produccion ); Cada categoria representa el estado de archivos en los nodos replicando la estructura de su filesystem.

Esta nueva estructura se eligio para poder tener una vision general del estado del nodo, haciendo evidente cuando distintos playbooks afectan los mismos recursos.

Esta estructura esta pensada para ser utilizada junto con un sistema de versionado, sistema que sera requerido si se desea operar con AWX, en el cual la division de categorias puede pasar de estar definida por carpetas a estar definida por ramas de ciclo de vida.

## Inventario

El archivo site.pp describe como se categorizan a los nodos segun su identificador, y, que variables se atribuyen a cada categoria. Esta responsabilidad se traslada al inventario, que debera mantener una lista de los hosts a orquestar, su categorizacion y variables asociadas (como por ejemplo el TipoNodo o la oleada de despliegue)

## Site y targeting

El archivo site.pp consolida una serie de clases a ser impactadas en distintos tipos de nodos, en Ansible este comportamiento se puede lograr ejecutando multiples playbooks desde AWX o consolidadndo en playbooks para cada categoria, se proveen playbooks referentes a estos tipos de nodo (nodosTesting, nodosPilotp, nodosProduccion y todosNodos). Los playbooks se proveen con target a la totalidad de nodos del inventario, el targeting se puede realizar mediante el uso de distintos inventarios o utilizando la variable 'host_override' para seleccionar el host o grupo deseado

## Roles
### file-provision

El rol de provisionamiento de archivos permite el envio de archivos en lote, aprovechando el repositorio de archivos, y permitiendo aplicar el script crediconn (Un caso de uso comun al enviar archivos). A continuacion podemos observar un ejemplo de uso:

```yaml
  - name: Provisionar templates
    include_role:
      name: file-provision
    vars:
      applyConffilial: true
      owner: 'root'
      group: 'root'
      mode: '644'
      dirmode: '0755'
      path: '/etc/crediconn/templates'
      files: 
      - 'hostname'
      - 'hosts'
      - 'network-interfaces'
      - 'network-interfaces.filial.nodovpn'
      - 'network-interfaces.filial.snavirtual'
      - { name: 'network-interfaces.filial.is_virtual', when: ansible_facts.facter_is_virtual is defined and ansible_facts.facter_is_virtual == 'true'}
      - { name: 'ntpd.conf', when: ansible_facts.facter_is_virtual is defined and ansible_facts.facter_is_virtual == 'true'}
```

En el apartado de variables (`vars`) se colocan los parametros para la ejeccucion del rol

+ applyConffilial (Opcional - true | false): Decide si se aplica el script. De omitirse su valor se considera `false`
+ owner (Requerido): owner de los archivos
+ group (Requerido): grupo de los archivos
+ mode (Requerido): Modo de acceso a los archivos
+ dirmode (Requerido): Modo de acceso al directorio
+ path (Requerido): Directorio donde impactar los archivos. Igual al del repositorio
+ files (Requerido): Lista de nombres de archivos a enviar

Ademas de nombres, el parametro `files` acepta objetos que pueden definir casos especiales para archivos particulares. El parametro `name` es requerido y se pueden utilizar opcionalmente parametros `owner`, `mode`, `group` y `path` para sobrescribir estos valores para el caso particular. Se incorpora ademas un parametro `when` que permite enviar archivos condicionalmente.

Se agregan dos eventos `Post file provision handled` y `post conffilial apply` para la implementacion de handlers que reaccionen a eventos de envio de archivos y aplicacion del script conffilial, respectivamente

## Ejemplo de ejecucion
`ansible-playbook -i inventory.ini playbook.yml --extra-vars 'host_override=localhost'`
