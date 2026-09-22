$inputText = [Console]::In.ReadToEnd()
$event = $inputText | ConvertFrom-Json

if ($event.tool_name -eq "apply_patch") {
    @{
        systemMessage = "Files were changed. Before claiming completion, run the relevant tests from AGENTS.md and inspect the diff."
    } | ConvertTo-Json -Depth 5
}
else {
    @{} | ConvertTo-Json
}