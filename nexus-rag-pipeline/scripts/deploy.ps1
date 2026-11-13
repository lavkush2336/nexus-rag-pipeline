# Nexus RAG Pipeline - PowerShell Deployment Helper
# Usage: .\deploy.ps1 -Action [validate|docker|health|monitor]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("validate", "docker", "health", "monitor", "test")]
    [string]$Action,
    
    [string]$ServiceUrl = "http://localhost:8000",
    [int]$CheckInterval = 30
)

# Colors for output
$Success = "Green"
$Error = "Red"
$Warning = "Yellow"
$Info = "Cyan"

function Write-Status {
    param([string]$Message, [string]$Status = "Info")
    $color = @{
        "Success" = $Success
        "Error" = $Error
        "Warning" = $Warning
        "Info" = $Info
    }[$Status]
    Write-Host $Message -ForegroundColor $color
}

function Test-EnvironmentVariables {
    Write-Status "Checking environment variables..." "Info"
    
    $required = @("GEMINI_API_KEY", "ELASTICSEARCH_URL", "ELASTICSEARCH_API_KEY")
    $missing = @()
    
    foreach ($var in $required) {
        $value = [Environment]::GetEnvironmentVariable($var)
        if ([string]::IsNullOrEmpty($value)) {
            Write-Status "  ✗ Missing: $var" "Error"
            $missing += $var
        } else {
            Write-Status "  ✓ $var is set" "Success"
        }
    }
    
    return $missing.Count -eq 0
}

function Test-ApiKeyLength {
    Write-Status "Checking API key lengths..." "Info"
    
    $geminiKey = [Environment]::GetEnvironmentVariable("GEMINI_API_KEY")
    $esKey = [Environment]::GetEnvironmentVariable("ELASTICSEARCH_API_KEY")
    
    $valid = $true
    
    if ($geminiKey.Length -lt 30) {
        Write-Status "  ✗ GEMINI_API_KEY too short ($($geminiKey.Length) chars, min 30)" "Error"
        $valid = $false
    } else {
        Write-Status "  ✓ GEMINI_API_KEY length valid" "Success"
    }
    
    if ($esKey.Length -lt 30) {
        Write-Status "  ✗ ELASTICSEARCH_API_KEY too short ($($esKey.Length) chars, min 30)" "Error"
        $valid = $false
    } else {
        Write-Status "  ✓ ELASTICSEARCH_API_KEY length valid" "Success"
    }
    
    return $valid
}

function Test-Urls {
    Write-Status "Checking URL formats..." "Info"
    
    $esUrl = [Environment]::GetEnvironmentVariable("ELASTICSEARCH_URL")
    
    if (-not $esUrl.StartsWith("https://")) {
        Write-Status "  ✗ ELASTICSEARCH_URL must use HTTPS" "Error"
        return $false
    } else {
        Write-Status "  ✓ ELASTICSEARCH_URL uses HTTPS" "Success"
    }
    
    return $true
}

function Invoke-DeploymentValidation {
    Write-Status "`n╔$('=' * 58)╗" "Info"
    Write-Status "║  Nexus RAG Pipeline - Deployment Validation          ║" "Info"
    Write-Status "╚$('=' * 58)╝`n" "Info"
    
    $results = @()
    
    $results += Test-EnvironmentVariables
    $results += Test-ApiKeyLength
    $results += Test-Urls
    
    # Summary
    Write-Status "`n$('=' * 60)" "Info"
    Write-Status "VALIDATION SUMMARY" "Info"
    Write-Status "$('=' * 60)" "Info"
    
    if ($results -contains $false) {
        Write-Status "`n❌ VALIDATION FAILED - Fix errors above before deploying" "Error"
        exit 1
    } else {
        Write-Status "`n✅ ALL VALIDATION CHECKS PASSED - Ready to deploy!" "Success"
    }
}

function Invoke-DockerBuild {
    Write-Status "`nBuilding Docker image..." "Info"
    
    docker build -t nexus-rag-pipeline:latest .
    
    if ($LASTEXITCODE -eq 0) {
        Write-Status "✅ Docker image built successfully" "Success"
    } else {
        Write-Status "❌ Docker build failed" "Error"
        exit 1
    }
}

function Invoke-HealthCheck {
    Write-Status "`nPerforming health check..." "Info"
    
    try {
        $response = Invoke-WebRequest -Uri "$ServiceUrl/health" -ErrorAction Stop
        $health = $response.Content | ConvertFrom-Json
        
        Write-Status "✅ Service is reachable" "Success"
        Write-Status "  Status: $($health.status)" "Info"
        
        if ($health.checks.gemini_api_available) {
            Write-Status "  ✓ Gemini API available" "Success"
        } else {
            Write-Status "  ✗ Gemini API not available" "Error"
        }
        
        if ($health.checks.elasticsearch_reachable) {
            Write-Status "  ✓ Elasticsearch reachable" "Success"
            if ($health.checks.elasticsearch_latency_ms) {
                Write-Status "  ES Latency: $($health.checks.elasticsearch_latency_ms)ms" "Info"
            }
        } else {
            Write-Status "  ✗ Elasticsearch not reachable" "Error"
        }
        
    } catch {
        Write-Status "❌ Health check failed: $_" "Error"
        exit 1
    }
}

function Invoke-HealthMonitoring {
    Write-Status "`n╔$('=' * 58)╗" "Info"
    Write-Status "║  Nexus RAG Pipeline - Health Monitor                 ║" "Info"
    Write-Status "║  Service: $ServiceUrl $(' ' * (20 - $ServiceUrl.Length))║" "Info"
    Write-Status "║  Check Interval: $CheckInterval seconds" + (' ' * (33 - $CheckInterval.ToString().Length)) + "║" "Info"
    Write-Status "║  Press Ctrl+C to stop monitoring                     ║" "Info"
    Write-Status "╚$('=' * 58)╝`n" "Info"
    
    $checkCount = 0
    $successCount = 0
    $failureCount = 0
    
    try {
        while ($true) {
            $checkCount++
            $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
            
            Write-Status "`n[$timestamp] Health Check #$checkCount" "Info"
            
            try {
                $response = Invoke-WebRequest -Uri "$ServiceUrl/health" -ErrorAction Stop
                $health = $response.Content | ConvertFrom-Json
                
                Write-Status "✅ Status: $($health.status)" "Success"
                $successCount++
                
                if ($health.checks.elasticsearch_reachable) {
                    Write-Status "  Elasticsearch: ✓" "Success"
                } else {
                    Write-Status "  Elasticsearch: ✗" "Error"
                }
                
                if ($health.checks.gemini_api_available) {
                    Write-Status "  Gemini API: ✓" "Success"
                } else {
                    Write-Status "  Gemini API: ✗" "Error"
                }
                
            } catch {
                Write-Status "❌ Health check failed: $_" "Error"
                $failureCount++
            }
            
            Write-Status "Stats: $successCount successful, $failureCount failed" "Info"
            Start-Sleep -Seconds $CheckInterval
        }
    } catch [System.Management.Automation.PipelineStoppedException] {
        Write-Status "`n`n$('=' * 60)" "Info"
        Write-Status "MONITORING STOPPED" "Info"
        Write-Status "$('=' * 60)" "Info"
        Write-Status "Total Checks: $checkCount" "Info"
        Write-Status "Successful: $successCount" "Success"
        Write-Status "Failed: $failureCount" "Error"
        Write-Status "$('=' * 60)" "Info"
    }
}

function Invoke-EndpointTest {
    Write-Status "`nTesting API endpoints..." "Info"
    
    $endpoints = @(
        @{Name = "Status"; Method = "GET"; Path = "/" },
        @{Name = "Health"; Method = "GET"; Path = "/health" },
        @{Name = "Metrics"; Method = "GET"; Path = "/metrics" },
        @{Name = "Docs"; Method = "GET"; Path = "/docs" }
    )
    
    foreach ($endpoint in $endpoints) {
        try {
            $response = Invoke-WebRequest -Uri "$ServiceUrl$($endpoint.Path)" -Method $endpoint.Method -ErrorAction Stop
            Write-Status "  ✓ $($endpoint.Name) [$($response.StatusCode)]" "Success"
        } catch {
            Write-Status "  ✗ $($endpoint.Name) failed" "Error"
        }
    }
}

# Main script
Write-Status "`n$('=' * 60)" "Info"
Write-Status "Nexus RAG Pipeline - Deployment Helper" "Info"
Write-Status "$('=' * 60)" "Info"

switch ($Action) {
    "validate" {
        Invoke-DeploymentValidation
    }
    "docker" {
        Invoke-DockerBuild
    }
    "health" {
        Invoke-HealthCheck
    }
    "monitor" {
        Invoke-HealthMonitoring
    }
    "test" {
        Invoke-EndpointTest
    }
}

Write-Status "`n$('=' * 60)`n" "Info"
