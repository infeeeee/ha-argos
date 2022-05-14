# ha-argos

Put Home Asstisant in your top bar! An [Argos](https://github.com/p-e-w/argos)/[Kargos](https://github.com/lipido/kargos)~~/[Xbar](https://github.com/matryer/xbar)~~ script.

Mac (Xbar) is not working yet. For a WIP state check the `xbar` branch. PRs are welcomed if you want to help with that.

## Screenshots

Gnome/Argos:

![](images/Screenshot%20from%202022-05-09%2023-54-36.png)

## Comparison with other top bar clients

None of the existing top bar clients were suitable for me, so I wrote this one.

| Name                                                                                              | Platforms               | Features | Configuration |
| ------------------------------------------------------------------------------------------------- | ----------------------- | -------- | ------------- |
| ha-argos                                                                                          | Linux (Gnome, Kde), ~~Mac~~ | Lot      | yaml file     |
| [ha-menu](https://github.com/addyire/ha-menu)                                                     | Mac, Windows            | Lot      | json file     |
| [Home Assistant Extension](https://extensions.gnome.org/extension/4170/home-assistant-extension/) | Linux (Gnome)           | Limited  | Gui           |

## Install

1. Install Argos, Kargos or Xbar
2. Clone the repo or download as zip
3. Install python and dependencies
4. Make sure `ha-argos.py` is executable
5. Symlink `ha-argos.py` to the config dir
6. Set up configuration.yaml

### Example on a Debian based linux with pip:

After installing Argos or Kargos:

```shell
sudo apt install python3 python3-pip
git clone https://github.com/infeeeee/ha-argos
cd ha-argos
pip install -r requirements.txt
chmod +x ha-argos.py
ln -s `readlink -f .`/ha-argos.py ~/.config/argos/
cp configuration.yaml.example configuration.yaml
```

### Example on Arch:

After installing Argos or Kargos:

```shell
pacman -S python python-yaml python-requests python-lxml python-cairosvg
git clone https://github.com/infeeeee/ha-argos
cd ha-argos
chmod +x ha-argos.py
ln -s `readlink -f .`/ha-argos.py ~/.config/argos/
cp configuration.yaml.example configuration.yaml
```

### Manual install on a mac

After installing xbar and homebrew

```shell
brew install git py3cairo 
git clone https://github.com/infeeeee/ha-argos
cd ha-argos
$(brew --prefix)/opt/python/libexec/bin/pip install -r requirements.txt
chmod +x ha-argos.py
ln -s $PWD/ha-argos.py "$HOME/Library/Application Support/xbar/plugins/"
cp configuration.yaml.example configuration.yaml
```

## Configuration

Everything is set up in the `configuration.yaml`. Just place it next to the script. you can start from `configuration.yaml.example`, just copy and edit it. 

The variable names are based on Home Assistant's Lovelace yaml config.

To reload the changed config use the reload button.

### Basic configuration

```yaml
settings:
  url: https://myserver.url
  token: my-secret-token
lines:
  - entity: sensor.livingroom_temperature
    attribute:
      - state
      - unit_of_measurement
    icon: mdi:home-assistant
  - separator
  - entity: light.livingroom
    service: light.toggle
    data: 
      brightness: 255
  - name: Garage
    icon: mdi:garage
    entities:
    - entity: cover.garage
      service: cover.open_cover
      name: Open garage door
    - entity: cover.garage
      service: cover.close_cover
      name: Close garage door
```

## All config options

### Settings

```yaml
settings:
  url: https://myserver.url
  token: my-secret-token
  icon_color: ffffff
  icon_size: 22
```

`url`: [required] The full url of your Home Assistace instance. Include http(s) at the beginning and port umber at the end.

`token`: [required] Your long-lived access token. You can generate this on your profile. [Official help.](https://www.home-assistant.io/docs/authentication/#your-account-profile)

Create token on your instance: [![Open your Home Assistant instance and show your Home Assistant user's profile.](https://my.home-assistant.io/badges/profile.svg)](https://my.home-assistant.io/redirect/profile/)

`icon_color`: [optional] [Argos only] The color of the icon. Defaults to black. Add an RGB hex code, without the `#` sign

`icon_size`: [optional] [Argos only] The width of the image in pixels, it's the `imageWidth` Argos parameter: [Argos help](https://github.com/p-e-w/argos#line-attributes)

### Lines

In this section just put the lines on the same order as they will show up on the dropdown. Possible lines:
- `separator`
- `entity`
- `entities`

#### Separator

It's the same as an [argos separator](https://github.com/p-e-w/argos#rendering), and it behaves the same way: `entity` lines above the first separator display on the bar. If multiple `entity` lines are above the first `separator` they will cycle, and each will be displayed for 3 seconds.

After the first `separator` latter ones will display as a horizontal line.

#### Entity

```yaml
lines:
  - entity: sensor.livingroom_temperature
    attribute:
      - state
      - unit_of_measurement
    icon: mdi:home-assistant
  # Another example:
  - entity: light.livingroom
    service: light.toggle
    icon: mdi:ceiling-light
    name: Livingroom ceiling light
    data:
        brightness: 255
```

`entity`: [required] A entity id from Home Assistant. If the `service` is a Home Assistant script, it can be omitted.

`name`: [optional] The name how it should appear. If omitted, it will display the attribute selected. If attribute omitted, it will display the `friendly_name` attribute of the entity.

`attribute`: [optional] An attribute or a list of attributes to get from Home Assistant.

`service`: [optional] A service to run when this line is clicked.

`data`: [optional] Data for the service

`icon:` [optional] An icon for that line. It depends on the prefix of this line, where it will get the icon:

- `gtk:` [argos only] A gtk icon will be displayed. See possible values on [freedesktop.org icon naming specification](https://specifications.freedesktop.org/icon-naming-spec/icon-naming-spec-latest.html)
- `mdi:` Material Design Icon, as on Home Assistant ui
- Without prefix a base64 encoded image can be added

#### Entities

A dropdown list of other entities.

```yaml
lines:
  - name: A list of entities
    icon: gtk:view-list
    entities:
    - entity: sensor.mysensor
      attribute: 
    - entity: light.livingroom
      service: light.toggle
```

`entities`: [required] A list of entities. Separator is also possible. All options available for them as normal `entity` lines.

`name`: [optional] The title of the dropdown. 

`icon`: [optional] Same as for `entity` lines

## Troubleshooting

Open an issue if something isn't working!

### Running the script in terminal

The script is an executable, so if you just simply run it in the terminal you should see some sane output. You can check the exact error message, while it's hidden on the gui. It's also possible to hide the long base64 image strings with the argument `--noimage`, so it's easier to read the code:

```shell
cd ha-argos
./ha-argos.py --noimage
```

#### All script arguments:

`--noimage`: Do not add images
`--nocache`: Do not cache images

### Cache

The script caches the icons and `friendly_name`s of the entities to a `cache.json` file. If some icons or names are not updating, just simply delete this file, it will be recreated during next call to Home Assistant.


## License

MIT
