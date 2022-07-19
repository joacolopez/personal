[TAS - Documentación]

Usuario administrador:

    usr: administrador
    clave: Gercom123

Archivos para instalar en: 

    a. C:\PARA INSTALAR

#Sistema Operativo

    1. Instalar drivers
        a. Reiner
                Copiar carpeta XFS al C:\ y ejecutar el archivo XFS310SDKInstall.exe
                Importar registros \xfs\registry\UserDefaultIpmReiner.reg y \xfs\registry\LocalMachineIpmReiner64.reg
        b. Ticketera
    2. Instalar Framework 3.0 y 4.0
    3. Instalar Redistributable x86

#Multivendor

    1. Copiar carpetas MV y SysAsap al C:\
    2. Instalar sql ejecutando \MV\Soft\ SqlLocalDB-2014-x64.msi
    3. Importar registro \MV\MV-HTML5.reg

#Monitoreo

    1. Instalar servicio de monitoreo
        a. Asegurarse de que las carpetas MV y SysAsap se encuentren en el C:\
        b. Ejecutar \SysASAP\EJSASERV\RegistrarEJ.bat
        
    Nota: configuración del servicio se encuentra en EJSASERV.exe.config

    2. Instalar servicio de monitoreo de publicidad
        a. Asegurarse de que las carpetas MV y SysAsap se encuentren en el C:\
        b. Ejecutar \SysASAP\PUBLICSERV\RegistrarPublicity.bat
        
    Nota: configuración del servicio se encuentra en PublicityATMService.exe.config

    3. Controlar que los servicios queden levantados y en Automático
        a. En ejecutar escribir services.msc
        b. Buscar los servicios NETCONTROLLER-PUBLICSERV y NETCONTROLLER-EJSASERV
        c. Si no estan en automático y activos, configurarlos correctamente

##Reiniciar TAS


// para agregar 
Compartir C:\MV para darle acceso al usuario autoservicio:
    
    

Cambiar hostname a wstXXXf0YYY y editar archivo host
127.0.1.1   wstXXXf0YYY.filiales.bancocredicoop.coop wstXXXf0YYY
