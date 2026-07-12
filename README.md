# Somfy RTS Bridge (ESPHome)

Local, cloud-free control of Somfy RTS covers from Home Assistant - no TaHoma/Connexoon box required.

> [!IMPORTANT]
> Everything already paired to a motor keeps working exactly as before. This bridge just adds itself as one more virtual remote alongside whatever's already there - existing physical remotes, wall switches, sensors, and TaHoma/Connexoon all keep working unchanged; nothing is removed or replaced. This matters in practice because a motor's memory for how many controllers it can remember is small and finite: RTS motors can remember up to **12 "controllers"** total - a broader category than just remotes. Wall switches, timers, group memberships, and sensors (e.g. light/sun or rain sensors) all consume a slot too, same as a remote does - **and TaHoma/Connexoon itself takes one too**, it's just another paired controller from the motor's point of view. Adding this bridge's virtual remote uses up one more of those 12 slots.

> [!CAUTION]
> Personal use only, on devices you own. Interacting with RTS devices that aren't yours may be illegal in your jurisdiction. Provided as-is, with no guarantees of any kind - see the licenses of the upstream projects this is built on.

Drives the board's onboard SX1276 radio directly in raw OOK mode. No extra hardware required.

Somfy RTS is a one-way (no acknowledgment), rolling-code protocol - distinct from Somfy IO (io-homecontrol), which is a different protocol on a different frequency. If your motor/remote actually speaks IO instead, see [`somfy-io-bridge`](https://github.com/danielpetrovic/somfy-io-bridge) - check your motor/remote's own documentation (or the frequency printed on it) to know which protocol it actually speaks.

### Cover device classes

Every cover takes a standard ESPHome/Home Assistant `device_class`, set per-cover in YAML to match whatever's physically installed (the motor/protocol has no way to know this itself):

| `device_class` | Home Assistant meaning |
|---|---|
| `awning` | Awning |
| `blind` | Blind (slats that tilt, e.g. venetian) |
| `curtain` | Curtain |
| `damper` | Damper (HVAC airflow) |
| `door` | Generic door |
| `garage` | Garage door |
| `gate` | Gate |
| `shade` | Shade / roller shade (no tilt) |
| `shutter` | Shutter |
| `window` | Window |

The examples below use `curtain`/`shade` - substitute whichever matches your own devices.

---

## Before you start

This is an **ESPHome** project, driven from Home Assistant's own **ESPHome app** (called an "add-on" before Home Assistant 2026.2 renamed these to "apps" - you'll still see the older name in older screenshots/guides), not a separate program you install on your PC. ESPHome itself is maintained by Nabu Casa, the same company behind Home Assistant, which is why it integrates this smoothly (auto-discovery, native API, OTA updates from within Home Assistant).

Install it in Home Assistant first: Settings → Apps → search "ESPHome" → Install → Start (turning on "Show in sidebar" is convenient). This app is what compiles the `.yaml` files described in Setup below into firmware and flashes it onto the board - no PlatformIO, Arduino IDE, or separate `esphome` command-line install needed on your own computer.

---

## Setup

1. **Hardware**: LilyGO TTGO T3 LoRa32 **433MHz** V1.6.1 - nothing else needed, the onboard radio and its pin wiring (DIO2→GPIO32) are already correct for this exact board revision.
2. **Place this bridge's files** - `somfy-rts-bridge.yaml` and `somfy-rts-cover.yaml` - under `/config/esphome/` on your Home Assistant instance. Any app that lets you browse/edit files under `/config` works for this - Studio Code Server, File Editor, or a Samba/SSH share to your PC are all fine.
3. **Secrets**: add `wifi_ssid`, `wifi_password`, `rts_bridge_api_key`, and `rts_bridge_ota_password` to `secrets.yaml` under `/config/esphome/`. Two ways to get the values:

   #### Normal flow (recommended)

   Entirely inside the ESPHome app, no terminal needed:
   - Open the ESPHome app → the "⋮" (three-dot) menu, top right → **Secrets**. Edits `secrets.yaml` directly inside the app, creating it if it doesn't exist yet.
   - For `rts_bridge_api_key` (a base64-encoded 32-byte value): ESPHome's own site has a generator built into its docs, entirely client-side (nothing sent anywhere) - open [esphome.io/components/api](https://esphome.io/components/api/#configuration-variables), find the encryption key generator, and use its **Copy** button.
   - For `rts_bridge_ota_password`: no format requirement, just needs to exist - any password works, typed directly into the Secrets editor. For a random one instead of hand-picked, click **Regenerate** then **Copy** on that same generator page a second time.

   #### Advanced flow

   A terminal instead - useful if you'd rather script it. Home Assistant's own "Terminal & SSH" or "Studio Code Server" app always has `openssl` available regardless of your own computer's OS (on Windows, `openssl` usually isn't available unless you have Git for Windows - use its "Git Bash"). No terminal at all? Your browser's own Developer Tools (`F12` → Console) works too: `Array.from(crypto.getRandomValues(new Uint8Array(32)), b => b.toString(16).padStart(2, '0')).join('')` prints hex, which works fine as the base64 field's value too - it's raw random bytes either way.

   ```yaml
   wifi_ssid: "your_wifi_name"
   wifi_password: "your_wifi_password"
   rts_bridge_api_key: "base64-encoded-32-byte-key"      # openssl rand -base64 32
   rts_bridge_ota_password: "some-password"              # openssl rand -hex 16
   ```
4. **Add an area + device entry** for each physical cover under `esphome:` in `somfy-rts-bridge.yaml` - this is what makes the cover show up as its own HA device (matching Overkiz's per-shade/curtain granularity) instead of bunched onto the hub:
   ```yaml
   esphome:
     areas:
       - id: my_room_area
         name: "My Room" # must match an existing HA area name exactly, or HA creates a new one
     devices:
       - id: my_new_cover_device
         name: "My Room Curtain" # include the room name here - HA's own Area-prefix-to-entity_id feature isn't reliable enough to depend on for display naming
         area_id: my_room_area
   ```
5. **Add a cover entry** for each physical cover under `packages:` in `somfy-rts-bridge.yaml` (`cover_id` + `_device` must match the device `id` above):
   ```yaml
   packages:
     my_new_cover: !include
       file: somfy-rts-cover.yaml
       vars:
         cover_id: my_new_cover
         cover_name: "My New Cover"
         remote_address: "0x<fresh random 24-bit hex, never reused across covers>"
         device_class: curtain # or shade, awning, blind, window, etc. - see "Cover device classes" above
   ```
6. **Flash** `somfy-rts-bridge.yaml` via the ESPHome app - open the app, find this file's card, and click **Install**:
   - **First flash**: choose "Plug into this computer", connect the board via USB, and pick the serial port when your browser prompts for it (only works from a browser tab open on the machine physically connected to the board).
   - **Every flash after that** (updates): choose "Wirelessly" instead - no USB needed, once the board is already on your Wi-Fi.
   - After a successful first flash, the board announces itself to Home Assistant automatically - go to Settings → Devices & Services, an "ESPHome" discovery card should appear; click **Configure** and enter the `rts_bridge_api_key` value from `secrets.yaml` the one time it's needed.
7. **Pair each cover to its motor** (see below).
8. **Test**: Open/Close/Stop from the cover's card in Home Assistant.

## Pairing (and unpairing) a cover to its motor

Single `Program` button. RTS has only one PROG command (`SOMFY_PROG`, no separate "remove" value exists in the protocol at all) - per Somfy's own official instructions for adding/removing a remote, the motor decides add vs. remove based on the **order** two PROG presses arrive in, not on any command distinction. **Getting the order backwards removes the wrong control** - this is Somfy's documented procedure, not something this bridge invented or can paper over.

**To add** (pair a new cover to a motor that already has at least one working control):
1. If the already-paired remote you're using to open programming mode has multiple channels (e.g. a Telis 16), select the correct channel on it first.
2. Press and hold that remote's PROG button until the motor jogs. The motor then stays in programming mode for about **2 minutes**.
3. Within that window, press the new cover's `<Cover Name> Program` button in Home Assistant. The motor jogs again, confirming the new remote is now paired, in addition to (not instead of) any existing remote.

**To remove** (e.g. decommissioning a cover) - the two presses must happen in this exact order:
1. **First**, press and hold PROG on the control you want to **keep** (a physical remote or TaHoma - not the one being removed; select the correct channel first if it's multi-channel). Hold until the motor jogs.
2. **Then**, within the same programming window, press the `<Cover Name> Program` button in Home Assistant for the cover you want to **remove**. The motor jogs again, confirming removal.

Reversing this order removes the keeper instead of the target - always press the control you're keeping first.

> [!WARNING]
> Per Somfy's own instructions: a control can only be removed if **another** control is available to open the motor's programming window first. If this board's Program button is the *only* paired control for a motor and you remove it, you lose the ability to open that motor's programming window at all - you'd need the motor manufacturer's own hard-reset procedure to recover, see [Factory-resetting a motor](#factory-resetting-a-motor-double-power-cut) below. Always keep at least one other working control paired before removing this board's identity.

RTS has no acknowledgment channel at all. There's no way to confirm a Program press actually took beyond watching the motor jog; if it doesn't respond as expected, it likely wasn't in its programming window at the right moment, just try again.

## Factory-resetting a motor (Double Power Cut)

Documented in Somfy's own motor manuals as one option in the motor's troubleshooting flow - this section covers the mechanics of the reset itself, once you've decided it's needed, not when to reach for it over a lighter remedy. Both paths below start with the same Double Power Cut; only the second half differs depending on whether you already have a working paired remote.

**Step 1 (both paths) - Double Power Cut:**
1. Motor powered.
2. Cut power - **2-3 seconds**.
3. Restore power - **8 seconds**.
4. Cut power again - **2-3 seconds**.
5. Restore power - the motor moves for ~5 seconds (or a short up/down movement if it was sitting at an end-limit), confirming the cut registered.

> [!WARNING]
> Only power the specific motor being reset - anything else sharing the same circuit gets reset too. Avoid using TaHoma or another remote/box to control this motor during the procedure.

Timing by hand is error-prone - a smart plug driven by a short HA script gets it exact:
```yaml
script:
  reset_shutter_motor_dpc:
    alias: "Reset Shutter Motor (Double Power Cut)"
    sequence:
      - service: switch.turn_off
        target: {entity_id: switch.YOUR_SMART_PLUG}
      - delay: "00:00:02"
      - service: switch.turn_on
        target: {entity_id: switch.YOUR_SMART_PLUG}
      - delay: "00:00:08"
      - service: switch.turn_off
        target: {entity_id: switch.YOUR_SMART_PLUG}
      - delay: "00:00:02"
      - service: switch.turn_on
        target: {entity_id: switch.YOUR_SMART_PLUG}
```

**Step 2 depends on your situation:**
- **You have a working, currently-paired remote**: hold its PROG button for **more than 7 seconds**, until the motor does **2 short movements → OK**. This erases every *other* control, but the remote you used stays paired - you can go straight into calibration with it afterward without pressing PROG again.
- **You have no working remote** (lost or defective): using the **new** replacement remote you intend to pair, press PROG **briefly - under 1 second** - until the motor does **1 short movement → OK**. This erases every *other* control, and pairs the new remote immediately as part of the same step.

**What gets reset either way**: all settings (except the retraction/back-impulse function) return to factory defaults.

**After either path, before the motor is usable with this bridge**:
1. Make sure you have one working physical remote paired (per whichever path above applied) and use it to program travel limits - this bridge has no travel-limit/calibration feature of its own.
2. Check rotation direction while in calibration mode: long-press UP and DOWN together to enter it, then press and hold UP or DOWN to see which way the motor actually turns. If reversed, press **MY for 2 seconds** to flip it.
3. Only after travel limits are calibrated, add this bridge as an additional control via its own Program button (see [Pairing](#pairing-and-unpairing-a-cover-to-its-motor) above).
4. If TaHoma or another box was previously used to control this motor, re-add it through its normal app flow (same PROG-press ceremony as pairing any other remote).

## Modes

Each cover has a `select:` entity to switch between:
- **`My`** (default) - three fixed states, no time-based estimation, no drift:
  - **0%** → `DOWN` (fully closed)
  - **50%** → `MY` (the motor's own favorite/preset position, whatever that's set to)
  - **100%** → `UP` (fully open)
  - Stop always sends `MY` too, matching how a real Somfy remote's MY button behaves (stops in place if moving, jumps to the preset if idle).
- **`Timed`** - local travel-time-based position estimate (`Travel Time Open`/`Travel Time Close` number entities, per-cover, default 25s each, adjustable live from Home Assistant - no reflash needed). Approximate; can drift on repeated partial moves since RTS is one-way and the motor never reports real position back. Requesting an intermediate position sends `UP`/`DOWN` and auto-stops (`MY`) once the estimate reaches the target.

## Retrying weak-signal commands

Each cover has a **`Retry Weak Signal Commands`** switch (off by default, per cover) for shutters with marginal RTS reception - RTS is one-way with no acknowledgment, so a command can silently get dropped with no way to detect it happened. When enabled, an Open or Close command automatically resends itself once, `retry_delay` (default 3s) later - unless another command (Stop, My, a repeat Open/Close, or a partial-position move) was issued in the meantime, in which case the pending retry is cancelled instead of firing. Entirely on-device (an ESPHome `script:`, `mode: restart` handles the cancel-on-any-other-command behavior); enabling the switch just arms it, no Home Assistant automation involved. When it does fire, it logs clearly (`tag: retry`, `INFO` level, e.g. `"Hallway Shade: resending Close (retry, no other command in 3s)"`) so it's unambiguous in the logs rather than something you have to infer from timing.

Opt-in rather than a blanket default since it doubles a cover's RF traffic on every Open/Close - only worth enabling for shutters that actually show the problem (motor doesn't respond to every command).

## How it works

- `sx127x` (ESPHome core) puts the SX1276 into raw OOK mode at 433.42MHz (Somfy's exact carrier, not the 433.92MHz ISM default).
- `remote_transmitter`/`remote_receiver` (ESPHome core) bit-bang the OOK data through the shared GPIO32/DIO2 pin.
- [`swoboda1337/somfy-esphome`](https://github.com/swoboda1337/somfy-esphome) (external component) implements the actual Somfy RTS protocol (rolling codes, frame encoding) on top of that radio. Ported from [`Legion2/Somfy_Remote_Lib`](https://github.com/Legion2/Somfy_Remote_Lib).
- Each cover is a `template` cover - see [Modes](#modes) above for the two position models it can switch between.

## Files

- `somfy-rts-bridge.yaml`: the device config (radio setup, Wi-Fi/API/OTA, the OLED display, `bluetooth_proxy`, diagnostic entities (WiFi Signal, Uptime, Loop Time, Restart Reason, Restart), configuration entities (Display, Display Brightness, Display Page Interval), a Debug Logging control switch, and one `packages:` entry per physical cover).
- `somfy-rts-cover.yaml`: reusable package template (virtual remote, Program button, My button, Mode select, Travel Time Open/Close numbers, Retry Weak Signal Commands switch, and the cover logic above), instantiated per cover via substitution variables (`cover_id`, `cover_name`, `remote_address`, `device_class`, `travel_time_open`, `travel_time_close`, `retry_delay` - see [Retrying weak-signal commands](#retrying-weak-signal-commands)).

## OLED display

The onboard SSD1306 cycles through a page per physical cover (name + current position) plus a shared status page (device IP, Bluetooth proxy state), switching automatically every 3 seconds.

## Board-specific notes

Tested and working on the LilyGO TTGO T3 LoRa32 **433MHz** V1.6.1 specifically. Pin numbers throughout (`spi:`, `sx127x:`, `i2c:`) are for that exact board revision, check your board's pinout before reusing this on anything else.

---

## Credits & Attribution

Not a from-scratch reimplementation - built on other people's protocol reverse-engineering and radio-level work, adapted into an ESPHome component.

- [`swoboda1337/somfy-esphome`](https://github.com/swoboda1337/somfy-esphome) (external component) implements the actual Somfy RTS protocol (rolling codes, frame encoding) on top of ESPHome's own core `sx127x`/`remote_transmitter`/`remote_receiver` components.
- That component is itself ported from [`Legion2/Somfy_Remote_Lib`](https://github.com/Legion2/Somfy_Remote_Lib).

## License

Apache License 2.0 - see [LICENSE](LICENSE).
