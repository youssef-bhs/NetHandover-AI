# UMTS KPI Thresholds

## Signal Quality Metrics

### RSCP (Received Signal Code Power)

| Level | Range (dBm) | Interpretation | Action |
|-------|-------------|----------------|--------|
| Excellent | > -75 | Strong signal, very good quality | None |
| Good | -75 to -85 | Acceptable for most services | Monitor |
| Fair | -85 to -95 | Marginal, may see degradation | Investigate if persistent |
| Poor | < -95 | Weak coverage, likely drops | Coverage expansion needed |
| Critical | < -110 | Near outage, emergency | Immediate action |

**Usage**:
- Coverage planning: RSCP ≥ -95 dBm in 95% of area
- Cell reselection threshold: typically -115 dBm (S_criteria)
- Handover trigger: RSCP_neighbor > RSCP_serving + TADD

### Ec/N0 (Energy per chip to Noise density)

| Level | Range (dB) | Interpretation | Action |
|-------|------------|----------------|--------|
| Excellent | > -5 | Very good quality | None |
| Good | -5 to -10 | Normal operation | None |
| Degraded | -10 to -14 | Interference likely | Investigate |
| Poor | < -14 | Severe interference | Immediate action |
| Critical | < -18 | Near unusable | Emergency measures |

**Usage**:
- Call quality threshold: Ec/N0 ≥ -10 dB for voice
- HSDPA scheduling: prefer Ec/N0 > -8 dB
- Soft handover combining benefit: Ec/N0 improvement 1-3 dB

### Combined RSCP + Ec/N0 Assessment

| RSCP | Ec/N0 | Diagnosis | Likely Cause |
|------|-------|-----------|--------------|
| > -80 | > -5 | Optimal | None |
| > -80 | -5 to -10 | Good | Normal operations |
| > -80 | < -10 | **Interference** | Check antennas, frequencies |
| -80 to -90 | > -5 | Good coverage | None |
| -80 to -90 | -5 to -10 | Fair | Monitor |
| -80 to -90 | < -10 | Interference + coverage mix | Both |
| < -90 | > -5 | Rare | Check hardware |
| < -90 | < -10 | **Coverage hole** | Add site/RRU |

## Block Error Rate (BLER)

| Metric | Target | Alert | Critical |
|--------|--------|-------|----------|
| DCH BLER | < 10% | 10-15% | > 15% |
| HS-DSCH BLER | < 15% | 15-25% | > 25% |

**Causes of high BLER:**
- Low Ec/N0 (interference)
- Low RSCP (coverage)
- Hardware issues (faulty amplifiers, cables)
- Transport issues (synchronization)

## Throughput KPIs

### HSDPA (High-Speed Downlink Packet Access)

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Max throughput (theoretical) | 14.4 Mbps | 3.6 Mbps | < 1 Mbps |
| Average user throughput | > 2 Mbps | 1-2 Mbps | < 1 Mbps |
| HSDPA CQI (Channel Quality Indicator) | > 20 | 15-20 | < 15 |

### HSUPA (High-Speed Uplink Packet Access)

| Metric | Good | Acceptable | Poor |
|--------|------|------------|------|
| Max throughput (theoretical) | 5.76 Mbps | 2 Mbps | < 1 Mbps |
| Uplink BLER | < 10% | 10-20% | > 20% |

## Handover KPIs

| KPI | Target | Alert | Critical |
|-----|--------|-------|----------|
| Soft HO success rate | > 99% | 95-99% | < 95% |
| Hard HO success rate | > 98% | 90-98% | < 90% |
| HO preparation time | < 200 ms | 200-500 ms | > 500 ms |
| Ping-pong rate | < 2% | 2-5% | > 5% |
| Active set size (avg) | 2-3 | 3-4 | > 4 |

## Load Metrics

### RTWP (Received Total Wideband Power)
- **Definition**: Total uplink power received by Node B across entire band
- **Indicates**: Uplink interference/cell load
- **Thresholds**:
  - Normal: < -102 dBm
  - High load: -102 to -98 dBm
  - Congested: > -98 dBm

### CSSR (Call Setup Success Rate)
- **Target**: > 98%
- **Below 95%**: Investigate immediately

### Call Drop Rate
- **Target**: < 2%
- **Above 3%**: Immediate investigation

### Availability
- **Target**: > 99.9% (annual downtime < 8.8 hours)
- **99.99%**: < 52.6 minutes/year (carrier-grade)

## Temporal Thresholds

### Persistent Degradation
- **Ec/N0 < -10 dB for ≥ 5 of last 10 samples** → interference alert
- **RSCP drop > 5 dB within 30 seconds** → coverage degradation
- **Active set size > 4 for > 2 minutes** → pilot pollution risk

### Rate of Change Thresholds
- **RSCP decrease rate > 2 dB/second** → rapid fading/edge of coverage
- **Ec/N0 standard deviation > 3 dB over 20 samples** → volatile channel
- **Blind HO attempts > 3/minute** → neighbor planning issue

## Measurement Window Guidelines

| KPI | Measurement Period | Reporting Frequency |
|-----|-------------------|--------------------|
| Ec/N0, RSCP | 1 sample = 100-200ms | Every 1-5 seconds |
| BLER | Over 1000-5000 bits | Every 5-10 seconds |
| HO success rate | 15-min average | 15-min intervals |
| RTWP | 500ms avg | 1-minute average |

## Threshold Adjustment Guidelines

### By Area Type:
- **Urban dense**: Higher RTWP thresholds (more users)
- **Rural**: Lower RSCP thresholds acceptable (-100 dBm may be OK)
- **Indoor**: Amplify thresholds by 3-5 dB (penetration loss)

### By Time:
- **Peak hours**: Allow 10-15% higher BLER, lower Ec/N0 tolerance
- **Off-peak**: Return to standard thresholds

### By Band:
- **Band 1 (2100 MHz)**: Higher attenuation, expect 5-10 dB lower RSCP vs Band 5
- **Band 5 (850 MHz)**: Better propagation, higher RSCP typical

## Alarm Thresholds (OMC Configuration)

Example alarm thresholds:
```
- Critical: Ec/N0 < -14 dB for > 60 seconds
- Major: RSCP < -100 dBm for > 120 seconds
- Minor: Active set size > 4 for > 300 seconds
- Warning: HO failure rate > 5% over 15 minutes
```

## References
- 3GPP TS 25.215: Physical layer; Measurements (FDD)
- 3GPP TS 25.331: RRC protocol
- 3GPP TS 45.008: Mobile radio interface
- Vendor-specific: Ericsson OSS, Huawei U2020, Nokia NMS
