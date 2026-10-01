# Interference in UMTS

## Types of Interference

### 1. Intra-frequency (Co-channel) Interference
- **Cause**: Neighboring cells using the same frequency carrier
- **Common in**: Dense urban areas with frequency reuse
- **Identification**:
  - RSCP is strong (-75 to -85 dBm)
  - Ec/N0 is poor (< -10 dB)
  - BLER (Block Error Rate) elevated (> 10%)
- **Solution**:
  - Frequency re-planning (assign different carriers)
  - Increase isolation via antenna tilting
  - Handover parameter optimization to move users to less loaded cells

### 2. Adjacent-channel Interference
- **Cause**: Signals from nearby frequency bands bleeding into UMTS band
- **Source**: Other carriers, GSM carriers on adjacent bands
- **Identification**: Raised noise floor across entire band
- **Solution**: Filtering, frequency coordination with other operators

### 3. External Interference
- **Cause**: Non-UMTS sources near cell site
  - Microwave links (2-42 GHz)
  - Radar systems
  - Industrial equipment (welding machines, motors)
  - Radio transmitters (broadcast, amateur)
- **Identification**:
  - Spectrum analyzer shows spurious emissions
  - Interference may be intermittent (time-based)
  - Often affects specific sectors/cells
- **Solution**: Locate and eliminate source, add filtering, site relocation

### 4. Pilot Pollution (Soft Interference)
- **Cause**: Too many cells with similar signal strength in same area
- **Mechanism**: UE cannot distinguish best server, leads to confusion
- **Identification**:
  - Multiple cells with PSCs having similar RSCP (delta < 5 dB)
  - Frequent cell reselections
  - High active set size (> 3 cells)
  - Low Ec/N0 despite good RSCP
- **Solution**:
  - Antenna tilt/azimuth adjustments
  - Power reduction on overlapping cells
  - Handover parameter tuning (increase TADD)

### 5. Congestion-induced Interference
- **Cause**: High load increases intra-cell interference (CDMA特性)
- **Mechanism**: More users → higher noise rise
- **Identification**:
  - High throughput demand
  - Ec/N0 degrades during peak hours
  - RSCP may remain stable
- **Solution**: Capacity expansion, load balancing, admission control

## Detection via KPIs

**Primary Indicators:**
- **Ec/N0 < -10 dB** sustained over multiple measurements
- **RSCP > -85 dBm** (signal is actually good) + **Ec/N0 < -10 dB** → Classic interference pattern
- **BLER > 15%** on DCH (Dedicated Channel)
- **HSDPA throughput drop** despite good RSCP

**Secondary Indicators:**
- Frequent handovers (handover failure rate > 5%)
- High transmit power from UE (uplink interference)
- Active set size anomalies
- Rapid Ec/N0 fluctuations (standard deviation > 2 dB over 5 samples)

## Troubleshooting Workflow

1. **Confirm interference**: Check if RSCP good but Ec/N0 poor
2. **Identify type**: Use spectrum analyzer, check cell load, analyze neighbor patterns
3. **Localize**: Is it cell-specific, sector-specific, or widespread?
4. **Take action**:
   - Frequency change (co-channel)
   - Antenna adjustment (pilot pollution)
   - Find external source (external interference)
   - Capacity expansion (congestion)

## Mitigation Actions

### Immediate (same-day)
- Increase antenna tilt on interfering sectors
- Adjust handover parameters (TADD + T_DROP)
- Power down overshooting cells

### Short-term (within week)
- Frequency re-planning (requires coordination)
- Add filters to external ports
- Site-level optimization

### Long-term (weeks to months)
- Build new sites for coverage
- Add carriers for capacity
- Replace faulty equipment

## Monitoring Thresholds

- **Ec/N0 < -10 dB for >5% of samples**: Investigate
- **PSC delta < 5 dB for >20% of samples**: Pilot pollution risk
- **Active set size average > 3**: Consider optimization
