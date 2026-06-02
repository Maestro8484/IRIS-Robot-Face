# sysmap.json Patch — Apply Manually or via Claude Code

## Session: 2026-05-27
## Reason: PAJ7620U2 replaces dead APDS-9960 (S66). DS3218MG servo installed.

The following fields in docs/sysmap.json teensy40 node are stale and must be updated.
Claude Code: apply these changes to sysmap.json as part of the PAJ7620U2 handoff session.

---

### 1. teensy40.role
OLD:
  "role": "Base mount controller. Pan servo driver, Person Sensor face tracking, APDS-9960 gesture sensor. USB-CDC serial to Pi4.",

NEW:
  "role": "Base mount controller. Pan servo driver, Person Sensor face tracking, PAJ7620U2 gesture sensor (replaces dead APDS-9960, S66). USB-CDC serial to Pi4.",

---

### 2. teensy40.gpio pins 18 and 19 — device field
OLD:
  { "pin": 18, "signal": "SDA", "device": "Person Sensor 0x62 + APDS-9960 0x39", "notes": "Shared I2C bus, Wire default" },
  { "pin": 19, "signal": "SCL", "device": "Person Sensor 0x62 + APDS-9960 0x39", "notes": "Shared I2C bus, Wire default" }

NEW:
  { "pin": 18, "signal": "SDA", "device": "Person Sensor 0x62 + PAJ7620U2 0x73", "notes": "Shared I2C bus, Wire default. APDS-9960 dead S66, replaced with PAJ7620U2." },
  { "pin": 19, "signal": "SCL", "device": "Person Sensor 0x62 + PAJ7620U2 0x73", "notes": "Shared I2C bus, Wire default." }

---

### 3. teensy40.tunable_constants — DS3218MG starting values
OLD:
  "PAN_SPEED":         0.04,
  "PAN_DEAD_ZONE_DEG": 2.0,
  "FACE_RETURN_MS":    8000,

NEW:
  "PAN_SPEED":         0.02,
  "PAN_DEAD_ZONE_DEG": 5.0,
  "FACE_RETURN_MS":    6000,

---

### 4. teensy40 — add servo field
Add after "tombstoned_predecessor":
  "servo": "Miuzei DS3218MG Digital Servo, 25kg, 0.16s/60deg, metal gear. Pin 2. External 5V rail.",

---

### 5. _meta.last_updated
OLD: "2026-05-25"
NEW: "2026-05-27"

### 6. _meta.authority — remove stale reference to servo_pico .ino
OLD: "Source files: IRIS_ARCH.md, IRIS_CONFIG_MAP.md, servo_pico/IRIS-BaseServoControlViaPerson_Sensor/IRIS-BaseServoControlViaPerson_Sensor.ino"
NEW: "Source files: IRIS_ARCH.md, IRIS_CONFIG_MAP.md, servo_teensy40/teensy40_base_mount/teensy40_base_mount.ino"
