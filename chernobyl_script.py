"""
Scripted event timeline for the automated Chernobyl replay.

Each entry fires when `chernobyl_elapsed` crosses its `time` (seconds).
Rod positions: 0.0 = fully withdrawn (minimum absorption),
               1.0 = fully inserted (maximum absorption / shutdown).
"""

EVENTS = [
    {
        "time": 0,
        "rods": [0.60] * 10,
        "title": "April 25, 1986 — 13:05",
        "lines": [
            "RBMK-1000 Unit 4 running at nominal power (~3,200 MWth).",
            "Night shift prepares for the turbine rundown safety test.",
            "Reactor stable. ORM: ~26 rods inserted. Everything nominal.",
        ],
    },
    {
        "time": 12,
        "rods": [0.75] * 10,
        "title": "23:10 — Power Reduction Begins",
        "lines": [
            "Power reduced for the turbine safety test.",
            "Target: 700–1,000 MWth (22–31% of rated power).",
            "Rods inserted further. Reactor going subcritical.",
        ],
    },
    {
        "time": 24,
        "rods": [0.88] * 10,
        "title": "01:00 — Xenon-135 Poisoning",
        "lines": [
            "Xenon-135 accumulates from hours of prior full-power operation.",
            "Power collapses to ~30 MWth — only 3% of the test target!",
            "Chief Engineer Dyatlov demands operators raise power immediately.",
            "The reactor is deep in the 'xenon pit'.",
        ],
    },
    {
        "time": 36,
        "rods": [0.20] * 10,
        "title": "01:03 — Desperate Rod Withdrawal",
        "lines": [
            "Operators pull almost all control rods to fight xenon poisoning.",
            "Operational Reactivity Margin (ORM) falls to 6–8 rods.",
            "Safety regulations require a minimum of 15 rods. Violated.",
            "The reactor is now critically dependent on its coolant.",
        ],
    },
    {
        "time": 54,
        "rods": [0.10] * 10,
        "title": "01:22 — Minimum Safe ORM Breached",
        "lines": [
            "Only 6 control rods remain partially inserted in the core.",
            "The positive void coefficient is now the dominant effect.",
            "Steam voids forming in coolant channels.",
            "Any power disturbance is now potentially uncontrollable.",
        ],
    },
    {
        "time": 70,
        "rods": [0.06] * 10,
        "title": "01:23:04 — Safety Test Initiated",
        "lines": [
            "The turbine rundown test begins at exactly 01:23:04.",
            "All 8 main coolant pumps running at maximum flow.",
            "Reduced coolant flow creates steam voids — positive feedback!",
            "Power beginning to climb...",
        ],
    },
    {
        "time": 88,
        "rods": [0.03] * 10,
        "title": "01:23:40 — UNCONTROLLED POWER SURGE",
        "lines": [
            "Power rising exponentially — instruments going off-scale!",
            "Steam void fraction approaching 100% in fuel channels.",
            "The positive void coefficient is amplifying itself.",
            "Leonid Toptunov presses the AZ-5 emergency shutdown button!",
        ],
    },
    {
        "time": 100,
        "rods": [0.37] * 10,
        "duration": 10,
        "title": "01:23:40 — AZ-5 SCRAM ACTIVATED",
        "lines": [
            "ALL 211 control rods ordered to full insertion.",
            "Rods begin slow descent — gravity and springs only.",
            "Graphite displacer tips (1.25 m) enter the lower core first.",
            "Boron neutron-absorbers are still above the active zone!",
        ],
    },
    {
        "time": 110,
        "rods": [0.37] * 10,
        "duration": 3,
        "title": "01:23:44 — GRAPHITE TIPS IN THE CORE",
        "lines": [
            "Rods stalled — graphite displacing coolant water in lower channels.",
            "This ADDS reactivity instead of removing it: positive scram!",
            "The emergency shutdown command is making the reactor worse.",
            "Power climbing past 30,000 MWth — 10× rated output...",
        ],
    },
    {
        "time": 115,
        "rods": [1.00] * 10,
        "duration": 9,
        "title": "01:23:45 — BORON SECTION ENTERING (TOO LATE)",
        "lines": [
            "Boron-iron absorber section finally reaches the active core.",
            "Rods still traveling — full insertion takes ~20 seconds total.",
            "But fuel temperature already exceeds 2,000 °C.",
            "The pressure vessel is failing...",
        ],
    },
    {
        "time": 120,
        "rods": [0.00] * 10,
        "duration": 3,
        "title": "01:23:47 — ☢ EXPLOSION",
        "lines": [
            "STEAM EXPLOSION shatters the reactor pressure vessel.",
            "A second explosion — possibly prompt-critical nuclear — follows.",
            "190 tonnes of radioactive material ejected into the atmosphere.",
            "The graphite moderator fire burns for 10 days.",
        ],
    },
]
