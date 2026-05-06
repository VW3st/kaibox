# test_voices.ps1
# Runs Chatterbox Turbo through 8 personality variations.
# Each call saves a numbered WAV to the current folder.
#
# Usage: powershell -ExecutionPolicy Bypass -File .\test_voices.ps1

# Load secrets from .env
. .\load_env.ps1

$URL = $env:MODAL_URL_TURBO
$KEY = $env:MODAL_KEY
$SECRET = $env:MODAL_SECRET

if (-not $URL -or -not $KEY -or -not $SECRET) {
    Write-Host "ERROR: Missing env vars. Make sure .env exists with MODAL_URL_TURBO, MODAL_KEY, MODAL_SECRET" -ForegroundColor Red
    exit 1
}

$headers = @{
    "Modal-Key"    = $KEY
    "Modal-Secret" = $SECRET
    "Content-Type" = "application/json"
}

$tests = @(
    @{
        Name = "01_neutral_baseline"
        Text = "Hey what's up everyone, welcome to the stream. Today we're going to be testing some new AI voice tech."
        Exag = 0.5
        Cfg  = 0.5
    },
    @{
        Name = "02_streamer_hyped"
        Text = "YO WHAT IS UP CHAT! That was INSANE bro, did you see that? [laugh] absolutely cooked them!"
        Exag = 0.9
        Cfg  = 0.3
    },
    @{
        Name = "03_streamer_chill"
        Text = "Yeah no for sure, I get what you mean. [chuckle] honestly that's exactly the vibe I was going for."
        Exag = 0.6
        Cfg  = 0.4
    },
    @{
        Name = "04_excited_reaction"
        Text = "[gasp] No way! That's actually crazy. [laugh] I can't believe that just happened on stream!"
        Exag = 1.0
        Cfg  = 0.3
    },
    @{
        Name = "05_storytelling"
        Text = "So here's the thing right, last week I was messing around with this new tool and [sigh] honestly, it changed everything for me."
        Exag = 0.7
        Cfg  = 0.5
    },
    @{
        Name = "06_thinking_aloud"
        Text = "Hmm, interesting question. [breathe] let me think about that for a sec. Yeah I think the answer is probably yes."
        Exag = 0.5
        Cfg  = 0.4
    },
    @{
        Name = "07_dramatic_low_cfg"
        Text = "Listen. What I'm about to tell you is going to BLOW your mind. Are you ready? Because once you hear this, you can't unhear it."
        Exag = 1.1
        Cfg  = 0.25
    },
    @{
        Name = "08_full_personality"
        Text = "[laugh] okay okay okay, hold on. So you're telling me, that THIS whole time, I could've been doing it the easy way? [sigh] bro I'm gonna lose my mind."
        Exag = 0.85
        Cfg  = 0.3
    }
)

Write-Host ""
Write-Host "Testing Chatterbox Turbo with 8 personality variations..." -ForegroundColor Cyan
Write-Host "First call will be slow (~60-120s cold start). Subsequent calls fast." -ForegroundColor Yellow
Write-Host ""

$total = $tests.Count
$i = 0
foreach ($t in $tests) {
    $i++
    $filename = "$($t.Name).wav"
    $body = @{
        text         = $t.Text
        exaggeration = $t.Exag
        cfg_weight   = $t.Cfg
    } | ConvertTo-Json -Compress

    Write-Host "[$i/$total] $($t.Name)" -ForegroundColor Green
    Write-Host "  exag=$($t.Exag), cfg=$($t.Cfg)" -ForegroundColor Gray
    Write-Host "  text: $($t.Text.Substring(0, [Math]::Min(80, $t.Text.Length)))..." -ForegroundColor Gray

    $start = Get-Date
    try {
        Invoke-WebRequest -Uri $URL -Method POST -Headers $headers -Body $body `
            -OutFile $filename -ErrorAction Stop | Out-Null
        $elapsed = ((Get-Date) - $start).TotalSeconds
        Write-Host ("  -> {0} ({1:N1}s)" -f $filename, $elapsed) -ForegroundColor White
    } catch {
        Write-Host "  ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }
    Write-Host ""
}

Write-Host "Done. Listen to the WAVs in order to pick your favorite settings for Kai." -ForegroundColor Cyan
