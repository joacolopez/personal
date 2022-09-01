@echo off
:index
rem ---------- INICIO DE SCRIPT -------------
rem - Configuración automática de Nueva TAS -
rem -----------------------------------------

rem ---------- pre set ----------
rem formateo fecha para log
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /format:list') do set datetime=%%I
set datetime=%datetime:~0,8%-%datetime:~8,6%
if exist c:\configurador (
    set logpath=C:\configurador
) else (
    mkdir C:\configurador
    set logpath=C:\configurador
)
goto inputfil


rem ---------- INPUTS ----------
:inputfil
set /P "filial=Ingrese numero de filial: "
echo %filial%| findstr /r "^[0-9][0-9][0-9]*$">nul
if %errorlevel% equ 0 (
    goto inputtas
) else (
    echo Solo se permiten numeros
    goto inputfil
)

:inputtas
set /p "tasid=Ingrese numero de TAS (41, 81, 91, etc): "
echo %tasid%| findstr /r "^[0-9][0-9][0-9]*$">nul
if %errorlevel% equ 0 (
    goto inputiptas
) else (
    echo Solo se permiten numeros
    goto inputtas
)

:inputiptas
set /p "iptas=Ingrese ultimo octeto de la ip (209, 210, 211, etc): "
echo %iptas%| findstr /r "^[0-9][0-9][0-9]*$">nul
if %errorlevel% equ 0 (
    goto calcip
) else (
    echo Solo se permiten numeros
    goto inputiptas
)


rem ---------- CALCULA IP SERVER ----------
:calcip
for /f "tokens=* delims=0" %%A in ("%filial%") do set "a=%%A" 

set /A octeto= %a%
set /A OctetoA=10

if /I %a% LEQ 254  GOTO variables
set /A octeto=octeto-254
set /A OctetoA=11

if /I %octeto% LEQ 254  GOTO variables
set /A octeto=octeto-254
set /A OctetoA=12

if /I %octeto% LEQ 254  GOTO variables
set /A octeto=octeto-254
set /A OctetoA=13

:variables
rem HOSTNAME DE LA TAS
set host=tas0%tasid%f0%filial%
rem IP DE FILIAL
set ipfil=10.%OctetoA%.%octeto%


rem ---------- CONSULTA USUARIO ----------
:quser
echo Los datos ingresados son los siguientes:
echo Numero de filial ingresado: %filial%
echo ID TAS: %tasid%
echo IP TAS: %iptas%
echo.

rem ---------- CONFIGURO IP ----------
:setip
netsh interface ip set address name="eth0" static %ipfil%.%iptas% 255.255.255.0 %ipfil%.254 > %logpath%\logconfig.log
if %errorlevel% equ 0 (
    echo IP Configurada...
) else (
    echo ERROR. Ver log en %logpath%
    pause
    cls
    goto index
)
netsh interface ip set dns name="eth0" static %ipfil%.254 >> %logpath%\logconfig.log
if %errorlevel% equ 0 (
    echo DNS Configurado...
) else (
    echo ERROR. Ver log en %logpath%
    pause
    cls
    goto index
)


rem ---------- CONFIGURO HOSTNAME ----------
:hostname
wmic computersystem where caption='%ComputerName%' rename %host% >> %logpath%\logconfig.log
if %errorlevel% equ 0 (
    echo Hostname Configurado...
) else (
    echo ERROR. Ver log en %logpath%
    pause
    cls
    goto index
)

rem ---------- CONFIGURO ARCHIVO HOST ----------
:hosts

set hostspath=%windir%\System32\drivers\etc\hosts
if exist %hostpath%.bkp (
    rm %hostpath%
    copy %hostpath%.bkp %hostpath%
    echo 127.0.0.1 %host%.filiales.bancocredicoop.coop >> %hostspath% 
) else (
    copy  %hostspath% %hostspath%.bkp
    echo 127.0.0.1 %host%.filiales.bancocredicoop.coop >> %hostspath% 
)

if %errorlevel% equ 0 (
    echo Hosts file editada...
) else (
    echo ERROR. Ver log en %logpath%
    pause
    cls
    goto index
)

rem ---------- CIERRO LOG ----------
if exist %logpath%\logconfig.log (
    copy %logpath%\logconfig.log %logpath%\logconfig-%datetime%.log
    del %logpath%\logconfig.log
) else (
    copy %logpath%\logconfig.log %logpath%\logconfig-%datetime%.log
)

rem ---------- CIERRO SCRIPT Y REINICIO ----------
:fin
echo TAS CONFIGURADA OK. REINICIANDO EQUIPO
shutdown /r /t 5
exit
