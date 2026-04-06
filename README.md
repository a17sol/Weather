# ☼ Weather
A simple and customizable weather plugin for Sublime Text.

*Get concise weather reports in one keystroke!*

## Features
- Parallel fetching for multiple locations
- Pluggable weather providers
- Flexible output formats
- Independent unit configuration

## Installation
Package Control support is coming. For now, clone or copy this repository into the Sublime Text Packages directory:
```
# macOS
~/Library/Application Support/Sublime Text/Packages/

# Linux
~/.config/sublime-text/Packages/

# Windows
%APPDATA%\Sublime Text\Packages\
```
Then restart Sublime Text.

## Usage
Run `Weather: Show Current Weather` from the Command Palette (Ctrl+Shift+P / Cmd+Shift+P).
The plugin will open a dedicated tab and display the current weather for all locations specified in the settings.

We recommend adding a keybinding for the command to your settings. For example, open the Command Palette and run `Preferences: Key Bindings` (or go to **Preferences → Key Bindings**), and add the following line:
```
{ "keys": ["ctrl+alt+w"], "command": "weather" }
```

## Configuration
Open the settings via **Preferences → Package Settings → Weather → Settings** or `Preferences: Weather Settings` in the Command Palette.

The settings have detailed comments to help you configure them. They are divided into four sections:
- **Places** - a list of locations to display. To help you unambiguously specify them, four entry formats are supported (see comments in the settings file).
- **Provider-specific settings** 
	- `provider` allows you to choose a weather service you prefer. So far, two providers are included: `wttr` (https://wttr.in) does not require an API key, but may be unreliable, `openweather` (https://openweathermap.org/) requires an API key, but is faster and more reliable. You can get an API key quickly and for free - just register on the website. Custom providers can be added easily in `custom_providers.py`.
	- `key` - API key or token for the selected weather service.
	- `lang` - The language code to pass to the provider.

- **Units** of measurement for different quantities, such as temperature and wind speed, can be configured independently.

- **Formatting** - a set of strings to define the output format (see comments in the settings file).

## Requirements
- Sublime Text 4050 or newer

The plugin does not require any third-party Python packages.
