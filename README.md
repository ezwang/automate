# Automate

Simple utility to automate interacting with GUI applications using VNC and computer vision.

## Usage

Ensure that Docker is installed. Run `pipenv install`, `pipenv shell`, `./run.py <script name>`.

## Script Format

See the example scripts for more detailed information.

```json
{
    "name": "Script Name",
    "image_path": "./images/",
    "code": [
        {
            "action": "...",
            "arguments": {
                "name": "..."
            },
            "success_callback": [
                {
                    "action": "...",
                    "arguments": {
                        "...": "..."
                    }
                }
            ],
            "failure_callback": [
                {
                    "action": "...",
                    "arguments": {
                        "...": "..."
                    }
                }
            ]
        },
        {
            "action": "...",
            "arguments": {
                "...": "..."
            }
        }
    ]
}
```
