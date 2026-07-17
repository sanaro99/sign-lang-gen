# run_asllrp_full.ps1
# Finish the ASLLRP four-condition evaluation locally, on your own terminal.
# Thermal-safe: caps Ollama to 8/16 cores + BelowNormal priority the whole time.
#
# Usage (from the repo root, D:\gitgit\sign_language_gen):
#   powershell -ExecutionPolicy Bypass -File scripts\run_asllrp_full.ps1
#
# Re-runnable: it skips any condition that already has a result folder.
# To force a clean re-run of everything, delete results\asllrp_* first.

$ErrorActionPreference = "Stop"
$ollama = "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe"
$affinity = [IntPtr]0x00FF   # cores 0-7 (8 of 16). Use 0x000F for 4 cores if it still runs hot.

function Cap-Ollama {
    Get-Process ollama* -ErrorAction SilentlyContinue | ForEach-Object {
        try { $_.ProcessorAffinity = $affinity; $_.PriorityClass = 'BelowNormal' } catch {}
    }
}

# 1. Make sure Ollama is up
$up = $false
try { Invoke-WebRequest "http://localhost:11434/api/tags" -UseBasicParsing -TimeoutSec 3 | Out-Null; $up = $true } catch {}
if (-not $up) {
    Write-Host "Starting Ollama..."
    Start-Process $ollama serve -WindowStyle Hidden
    Start-Sleep -Seconds 6
}

# 2. Keep capping Ollama in the background (the model worker respawns on load, so re-cap on a timer)
$capper = Start-Job {
    $aff = [IntPtr]0x00FF
    while ($true) {
        Get-Process ollama* -ErrorAction SilentlyContinue | ForEach-Object {
            try { $_.ProcessorAffinity = $aff; $_.PriorityClass = 'BelowNormal' } catch {}
        }
        Start-Sleep -Seconds 10
    }
}
Cap-Ollama

try {
    # 3. Run each condition that isn't already done. --no-nmm = gloss only (NMM isn't scored w/o gold labels).
    $conditions = @("asllrp_baseline", "asllrp_rag", "asllrp_context", "asllrp_context_rag")
    foreach ($c in $conditions) {
        $exists = Get-ChildItem -Path "results" -Directory -Filter "$c`_*" -ErrorAction SilentlyContinue
        if ($exists) { Write-Host "[skip] $c already has a result folder"; continue }
        Write-Host "`n[run ] $c ..."
        python scripts/run_experiment.py --config "configs/$c.yaml" --no-nmm
        Cap-Ollama
    }

    # 4. Aggregate everything into results\summary.csv
    Write-Host "`n[eval] aggregating -> results\summary.csv"
    python scripts/evaluate.py
    Write-Host "`nDONE. See results\summary.csv"
}
finally {
    Stop-Job $capper -ErrorAction SilentlyContinue
    Remove-Job $capper -Force -ErrorAction SilentlyContinue
}
