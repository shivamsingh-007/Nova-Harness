# Example Skill

Generates Python code from structured specifications.

## Usage

Provide a specification string as input. The skill produces source code that
meets the declared acceptance criteria.

## Inputs

- `specification` (string, required): Natural language or structured spec.
- `language_version` (string, optional, default: "3.11"): Python version.

## Outputs

- `source_code` (string, required): Generated Python source code.

## Permissions

- Tools: read, write, execute
- No network access
- No deletion

## Dependencies

- python3 >= 3.10
