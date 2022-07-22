$filial = Read-Host "Ingrese numero de filial"
$tas = Read-Host "Ingrese numero de tas"
function CalcIPfilial ($filial) {
    if ($filial -le 254) {
        $ip = 10.10.$filial
        return $ip
    } 
    elseif ($filial - 254 -le 254) {
        $octfil = $filial - 254
        $ip = 10.11.$octfil
        return $ip
    }
    elseif ($filial - 254 -gt 254) {
        $octfil = $filial - 508
        $ip = 10.12.$octfil
        return $ip
    }


}
$ipfil = 10.10.$filial
Write-Host $ipfil