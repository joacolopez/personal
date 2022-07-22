#Input de variables
$getfilial = Read-Host "Ingrese numero de filial" 
$getTas = Read-Host "Ingrese numero de tas"

function CalcIPfilial ($getfilial) {
    if ($getfilial -le 254) {
        $ip = 10.10.$getfilial
        return $ip
    } 
    elseif ($getfilial - 254 -le 254) {
        $octfil = $getfilial - 254
        $ip = 10.11.$octfil
        return $ip
    }
    elseif ($getfilial - 254 -gt 254) {
        $octfil = $getfilial - 508
        $ip = 10.12.$octfil
        return $ip
    }
  
    }

$ip = CalcIPfilial
Write-Host $ip

