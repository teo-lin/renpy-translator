# PowerShell Module for handling user selections in a standardized way.

# This script provides functions to prompt users for choices from a list,
# with automatic selection if only one option is available.


function Select-Item {
    param(
        [string]$Title,
        [string]$ItemTypeName,
        [array]$Items,
        [scriptblock]$DisplayItem
    )

    if ($Items.Count -eq 0) {
        Write-Host ""
        Write-Host "ERROR: No ${ItemTypeName}s available to select!" -ForegroundColor Red
        throw "No ${ItemTypeName}s available."
    }

    if ($Items.Count -eq 1) {
        $selectedItem = $Items[0]
        Write-Host ""
        Write-Host "Auto-selecting the only available $ItemTypeName`: $($selectedItem.Name)" -ForegroundColor Cyan
        return $selectedItem
    }

    # Show menu for multiple items
    Write-Host ""
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host "       $Title" -ForegroundColor Cyan
    Write-Host "=================================================================" -ForegroundColor Cyan
    Write-Host ""

    for ($i = 0; $i -lt $Items.Count; $i++) {
        $num = $i + 1
        & $DisplayItem $Items[$i] $num
    }

    Write-Host "  [Q] Quit" -ForegroundColor Red
    Write-Host ""

    while ($true) {
        $selection = Read-Host "Select a $ItemTypeName (1-$($Items.Count) or Q)"

        if ($selection -eq "Q" -or $selection -eq "q") {
            Write-Host "Cancelled by user." -ForegroundColor Yellow
            throw "User cancelled selection."
        }

        try {
            $index = [int]$selection - 1
            if ($index -ge 0 -and $index -lt $Items.Count) {
                return $Items[$index]
            }
            else {
                Write-Host "Invalid selection. Please enter a number between 1 and $($Items.Count)." -ForegroundColor Red
            }
        }
        catch {
            Write-Host "Invalid input. Please enter a number or Q to quit." -ForegroundColor Red
        }
    }
}
