<#
 Forward to start.ps1
 Made by Lunarmist-byte
 GitHub:   https://github.com/Lunarmist-byte
 LinkedIn: https://www.linkedin.com/in/amal-s-kumar-ba69a1290/
#>
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $scriptDir "start.ps1") @args
