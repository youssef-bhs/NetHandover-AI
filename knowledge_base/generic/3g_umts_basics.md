# UMTS (3G) Network Basics

## Key Components

### Node B (Base Station)
- Cellular tower that transmits/receives radio signals
- One Node B serves multiple cells using different scrambling codes
- Connected to RNC via Iub interface

### RNC (Radio Network Controller)
- Manages multiple Node Bs
- Handles radio resource management, handover decisions
- Connects to core network via Iu interface

### UE (User Equipment)
- Mobile phone or device
- Communicates with Node B over Uu interface

## Important Parameters

### PSC (Primary Scrambling Code)
- 9-bit code (0-511) that identifies a cell
- Used for channelization and cell identification
- Adjacent cells should have high PSC separation to avoid confusion

### UARFCN (UMTS Absolute Radio Frequency Channel Number)
- Defines the carrier frequency
- Band 1 (2100 MHz): UARFCN 10562-10838
- Band 5 (850 MHz): UARFCN 4357-4458
- Band 8 (900 MHz): UARFCN 2927-3388

### RSCP (Received Signal Code Power)
- Measurement of signal strength in dBm
- Range: -120 to -25 dBm typically
- **Interpretation:**
  - > -75 dBm: Excellent, very close to tower
  - -75 to -85 dBm: Good quality
  - -85 to -95 dBm: Fair, may experience issues
  - < -95 dBm: Poor, likely coverage problems

### Ec/N0 (Energy per chip to Noise density)
- Signal quality metric in dB
- Ratio of signal energy to noise+interference
- **Interpretation:**
  - > -5 dB: Excellent quality
  - -5 to -10 dB: Good, normal operation
  - -10 to -14 dB: Degraded, interference likely
  - < -14 dB: Poor, severe interference

## Key Relationships

- **High RSCP + Low Ec/N0** → Interference (not coverage issue)
- **Low RSCP + Low Ec/N0** → Coverage problem (need more sites/antenna)
- **Low RSCP + High Ec/N0** → Rare, indicates hardware issue

## Measurement Points

- **Active Cell**: Currently serving cell (highest RSCP+RSCP combination)
- **Detected Cells**: Neighboring cells in active set or candidate set
- **Delta RSCP**: Active minus detected - indicates pilot pollution when small
