# Plan: Machine-readable output with -o flag (json|plain)

## Context

User wants to add a `-o` flag to the BlogWatcher CLI to control output format.
- `plain` — current colored human-readable output (default)
- `json` — machine-readable JSON for scripting/automation

## Files to modify

- `internal/cli/root.go` — add global `--output` / `-o` persistent flag to rootCmd
- `internal/cli/commands.go` — update output functions to respect format choice

## Implementation plan

### 1. Global flag in root.go

Add a package-level variable `outputFormat string` (accessible across commands) and register it as a persistent flag on rootCmd:

```go
var outputFormat string

func NewRootCommand() *cobra.Command {
    ...
    rootCmd.PersistentFlags().StringVarP(&outputFormat, "output", "o", "plain", "Output format: plain|json")
    ...
}
```

`outputFormat` is declared at package level in `root.go` so it is accessible in `commands.go` (same package `cli`).

### 2. JSON output helpers in commands.go

Add simple JSON-printing wrappers. Use `encoding/json`.

#### blogs command

When format is `json`, marshal slice of `model.Blog`:

```json
[{"id":1,"name":"...","url":"...","feed_url":"...","scrape_selector":"...","last_scanned":"..."}]
```

#### articles command

When format is `json`, marshal slice of article objects:

```json
[{"id":1,"blog":"...","title":"...","url":"...","published":"2024-01-01","is_read":false}]
```

#### scan command

When format is `json`, marshal slice of scan results:

```json
[{"blog":"...","source":"rss","total_found":10,"new_articles":3,"error":""}]
```

### 3. Modifications to command RunE functions

Each of the three commands (`blogs`, `articles`, `scan`) will check `outputFormat`:

```go
if outputFormat == "json" {
    printJSON(data)
} else {
    // existing colored output
}
```

Helper:
```go
func printJSON(v any) {
    enc := json.NewEncoder(os.Stdout)
    enc.SetIndent("", "  ")
    enc.Encode(v)
}
```

### 4. Validation

Add validation for invalid values:
```go
if outputFormat != "plain" && outputFormat != "json" {
    return fmt.Errorf("invalid output format %q: use json or plain", outputFormat)
}
```

## What stays unchanged

- `add`, `remove`, `read`, `read-all`, `import`, `unread` — these are mutation commands, no structured output to format; they keep their current success/error messages.

## Verification

```bash
# plain (default)
go run ./cmd/blogwatcher blogs
go run ./cmd/blogwatcher articles

# json
go run ./cmd/blogwatcher -o json blogs
go run ./cmd/blogwatcher -o json articles
go run ./cmd/blogwatcher -o json scan

# invalid format
go run ./cmd/blogwatcher -o csv blogs  # should error
```
