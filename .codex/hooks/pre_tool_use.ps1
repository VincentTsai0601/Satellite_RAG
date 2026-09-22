$inputText = [Console]::In.ReadToEnd()
$event = $inputText | ConvertFrom-Json
$command = [string]$event.tool_input.command

$dangerousPatterns = @(
    '\.env',
    'Remove-Item',
    '\brm\b',
    'git\s+reset\s+--hard',
    'git\s+clean\s+-fd',
    'satellite\.ingest.*--embed'
)

foreach ($pattern in $dangerousPatterns) {
    if ($command -match $pattern) {
        @{
            hookSpecificOutput = @{
                hookEventName = "PreToolUse"
                permissionDecision = "deny"
                permissionDecisionReason = "Blocked by Satellite RAG safety hook: $pattern"
            }
        } | ConvertTo-Json -Depth 5
        exit 0
    }
}

@{} | ConvertTo-Json