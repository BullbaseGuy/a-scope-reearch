param(
    [Parameter(Mandatory = $true)]
    [string]$SecurityMaster,
    [Parameter(Mandatory = $true)]
    [string]$FinancialExports,
    [Parameter(Mandatory = $true)]
    [string]$MarketData,
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d{4}-\d{2}-\d{2}$')]
    [string]$AsOfDate,
    [string]$OutputRoot = ".\09_OUTPUTS\live-bundle"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $ProjectRoot
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    throw "Missing virtual environment. Run: py -3.12 -m venv .venv"
}

$BundleDir = Join-Path $OutputRoot $AsOfDate
$MergedDir = Join-Path $BundleDir "merged-financials"
New-Item -ItemType Directory -Path $BundleDir -Force | Out-Null

& $Python -m ascope merge-financials `
    --input-dir $FinancialExports `
    --output-dir $MergedDir

Copy-Item $SecurityMaster (Join-Path $BundleDir "security_master.csv") -Force
Copy-Item $MarketData (Join-Path $BundleDir "market_data.csv") -Force
Copy-Item (Join-Path $MergedDir "financial_annual.csv") (Join-Path $BundleDir "financial_annual.csv") -Force
Copy-Item (Join-Path $MergedDir "financial_quarterly.csv") (Join-Path $BundleDir "financial_quarterly.csv") -Force

& $Python -m ascope validate-bundle `
    --input-dir $BundleDir `
    --as-of-date $AsOfDate `
    --minimum-securities 5000 `
    --minimum-market-days 120

$Zip = Join-Path $OutputRoot "ascope-live-bundle-$AsOfDate.zip"
& $Python -m ascope package-bundle `
    --input-dir $BundleDir `
    --output-zip $Zip `
    --as-of-date $AsOfDate `
    --minimum-securities 5000 `
    --minimum-market-days 120

Write-Host "Validated bundle: $BundleDir"
Write-Host "Release asset:    $Zip"
