# arkteos_reg3
"Arkteos REG3 heat pump" to MQTT

Arkteos (formely AJTech) is a French heat pump manufacturer.
Recent devices uses a connected "REG3" controller which can be remotely and locally managed through its 
[apps](https://espaceclientarkteos.arkteos.com/mes-applications/). 
AlpPAC also sells REG3 heat pumps.
With the help of a lot of sniffing, I was able to decode some important values and wrote a little python script to extract these values and push them to a MQTT server.

## Protocol overview
The protocol has a "serial-over-IP" style : the application simply connects to the controller and the receives (almost) all the data at regular intervals (seconds).
I identified 2 differents frames, with a size of 163 and 227 bytes.

## Excel sheet
I use the excel sheet to list known values, and the respective offset of the frame where they will be found. 
The formula "(byte1 \* weight1 + byte2 \* weight2) / divider" is applied to calculate the value.
The spreadsheet also generates the python dict used for the script, as well as the OpenHAB thing and items values.

## Caveats
Only a single (remote or local) connection can be simultaneously established, and there is no proper way to disconnect gracefully. Therefore :
 - the script will loop until a connection can be established
 - it will prevent any other connection before the controller timeouts (1 or 2 minutes actually)

Remote connection, through the Arkteos cloud service, has not been implemented. Network captures shows that it acts essentially as a proxy, adding some extra header to the raw data.

Produced energy history and counter are not implemented, work in progress. They need a special frame to be sent by the app.

Values are named in French, and copied from the official app. I don't think it was sold in other countries.
