# waybar-unicafe
waybar script for unicafe menu

# installation
download `unicafe.py` to a desired location (e.g. `.local/bin/scripts` or whatever)  
add an entry to your waybar config:  
```json
"custom/unicafe": {
    "format": "{}",
    "on-click": "firefox https://menu.unicafe.fi",
    "tooltip": true,
    "interval": 3600,
    "exec": "/path/to/unicafe.py 2> /dev/null",
    "return-type": "json"
},
```
i suggest setting the on-click action to open `menu.unicafe.fi` in a browser
