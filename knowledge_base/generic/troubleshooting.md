# Troubleshooting Guide for UMTS Networks

## Problem Identification Framework

### Step 1: Collect Data
- Recent KPIs (RSCP, Ec/N0, BLER, throughput)
- Measurement reports (UE measurements)
- OMC alarms and events
- Drive test results (if available)
- Cell configuration parameters

### Step 2: Classify Problem
- **Coverage**: RSCP low, Ec/N0 low
- **Interference**: RSCP good, Ec/N0 poor
- **Capacity/load**: High RTWP, high throughput demand, BLER high
- **Configuration**: Neighbor missing, parameter mis-set
- **Hardware**: Alarms present, site down

---

## Problem: High Interference (Ec/N0 < -10 dB, RSCP > -85 dBm)

### Diagnosis
- Pattern: Cell-specific or area-wide?
- Time pattern: Constant or intermittent?
- Frequency: One carrier or all?
- Affected sectors: Single sector or multiple?

### Immediate Actions

#### 1. Check Co-channel Interference
- Use `RSCP` and `PSC` to identify interferers
- Check neighbor list for overlapping cells on same UARFCN
- Run `interference matrix` in OMC

**Actions:**
- Temporarily change frequency of victim cell (if flexible)
- Increase antenna tilt on interfering cell
- Reduce TX power on interfering cell (careful: may create coverage hole)

#### 2. Check Pilot Pollution
- Review active set size statistics
- Check if neighboring PSCs have similar RSCP (delta < 5 dB)
- Count number of cells with RSCP within 5 dB of best

**Actions:**
- Increase TADD parameter (harder to add neighbors)
- Increase antenna tilt on overshooting cells
- Reorient azimuth to reduce overlap
- Delete unnecessary neighbor relations

#### 3. Check External Interference
- Is problem localized to specific site?
- Time pattern: Does it correlate with external equipment operation?
- Use spectrum analyzer at site or remote scanning

**Actions:**
- Scan for out-of-band emissions
- Coordinate with other operators
- Add bandpass filters to antenna ports

#### 4. Congestion Check
- Check cell load (RTWP, throughput, active users)
- Is Ec/N0 degradation correlated with peak traffic?

**Actions:**
- Load balancing: handover users to less loaded cells
- Add carrier (if hardware available)
- Admission control: limit new connections

---

## Problem: Poor Coverage (RSCP < -95 dBm, Ec/N0 also low)

### Diagnosis
- Is it indoor/outdoor?
- Is it predictable (edge of coverage) or sudden drop?
- Check antenna configuration: tilt, azimuth, electrical tilt settings
- Check transmit power on Node B

### Immediate Actions

#### 1. Antenna Adjustment
- Verify antenna tilt (mechanical and electrical)
  - Increase downtilt to focus signal closer to tower
  - Decrease uptilt if causing overshoot into adjacent areas
- Verify azimuth: is antenna pointed correctly?
- Check VSWR (high VSWR indicates feeder fault)

#### 2. Power Increase
- Increase Node B TX power (within regulatory limits)
- Check power amplifier output
- Verify antenna gain

#### 3. Add Coverage
- If area consistently weak: consider new site or RRU (Remote Radio Unit)
- For indoor: DAS (Distributed Antenna System) or femto cell

#### 4. Check for Obstructions
- Vegetation growth blocking signal
- New construction
- Antenna panel physical damage

---

## Problem: Handover Failures (High HO Failure Rate > 5%)

### Common Causes

#### 1. Missing Neighbor Relations
- Check: Is target PSC in neighbor list of source cell?
- Check: Does target cell have source in its neighbor list (for return)?
- Verify UARFCN and PSC combinations match

**Action:** Add missing neighbor relations via OMC

#### 2. Timing/Pacing Issues
- TADD too low → frequent HO attempts → failure due to congestion
- TTT too short → HO on temporary fade → failure at target
- T_DROP inappropriate → active set size issues

**Action:** Adjust parameters:
- Increase TADD to 4-6 dB
- Set TTT to 320-640 ms
- Decrease T_DROP to 1-2 seconds

#### 3. Target Cell Not Ready
- Is target cell barred (congestion, maintenance)?
- Is target cell operational (alarm active)?
- Does target have resources (codes, power)?

**Action:** Fix target cell configuration or select different target

#### 4. Coverage Hole
- Target cell signal weak at handover point
- Drop due to failure in target

**Action:** Improve coverage overlap between cells

---

## Problem: High Call Drop Rate (> 2%)

### Investigation Steps

1. **Correlate drops by cell**: Use OMC drop reports
2. **Analyze drop causes**:
   - Radio link failure (RL Failure)
   - Handover failure
   - Terminal issues
   - Core network issues
3. **Check KPIs at drop time**:
   - Ec/N0 just before drop?
   - RSCP trend?
   - Active set size?

### Radio Link Failure
- **Symptoms**: UL/DL SIR too low, out-of-sync
- **Root causes**: Impending coverage hole, high interference
- **Action**: Improve Ec/N0 (tilt, power, frequency)

### Handover-related Drops
- **Symptoms**: Drop during or after HO attempt
- **Check**: HO success rate, HO timing
- **Action**: Fix HO parameters, neighbors

---

## Problem: Low Throughput (HSDPA < 1 Mbps average)

### Check Order

1. **RSCP and Ec/N0**: Must be adequate (RSCP > -85, Ec/N0 > -8)
2. **CQI**: Channel Quality Indicator should be > 15 for good rates
3. **BLER**: High BLER indicates PHY problems
4. **Node B Load**: Check how many users sharing codes/ power
5. **Iub Interface**: Is backhaul saturated (≥ 80% utilization)?

### Actions

- Improve RF conditions (antenna, power)
- Reduce cell load (handover users out)
- Verify HSDPA configuration (TTI, modulation/coding)
- Check Iub capacity (upgrade if needed)

---

## Problem: Rapid Cell Reselections (Ping-Pong)

### Symptoms
- UE frequently changing serving cell (every few seconds)
- High handover attempts and failures
- Unstable connection

### Causes
- Two cells with very similar RSCP (delta < 3 dB)
- Handover parameters too sensitive (low TADD, short TTT)
- Antennas overlapping excessively

### Solutions
- Increase TADD (4-6 dB)
- Increase hysteresis (HYS = 3-4 dB)
- Increase TTT (640 ms)
- Physically separate cells via antenna tilt/azimuth

---

## Problem: High Uplink Interference (RTWP > -98 dBm)

### Causes
- Many UEs transmitting at high power (cell edge)
- External uplink interferer
- Faulty UE (stuck at max power)
- Antenna mismatch (high VSWR)

### Diagnosis
- Check distribution of UE TX power
- Is it time-dependent (peak hours)?
- Is it site-specific or network-wide?
- Check for alarms on RX paths

### Actions
- Load balancing: move UEs to less loaded cells
- Antenna tuning: improve downlink so UE can reduce power
- Check and replace faulty antenna/feeder
- Identify and remove external source

---

## Parameter Adjustment Checklist

### Before Changing Parameters:
- [ ] Document current values
- [ ] Check impact on other cells
- [ ] Schedule during low-traffic period
- [ ] Have rollback plan
- [ ] Notify NOC/operations

### Common Parameter Ranges:

| Parameter | Typical Range | Default | When to Adjust |
|-----------|---------------|---------|----------------|
| TADD | 3-6 dB | 4 dB | Increase for pilot pollution |
| T_DROP | 1-5 sec | 2 sec | Decrease if active set too large |
| TTT (Event 1A) | 320-640 ms | 640 ms | Decrease for faster HO |
| Hysteresis | 2-4 dB | 2 dB | Increase to prevent ping-pong |
| Max Active Set | 3-6 | 3 | Increase only if capacity allows |

---

## Tools and Commands

### Ericsson (OSS)
- `RLCPC`: Display cell parameters
- `RXTCP`: Display transceiver status
- `ALGXP`: Alarm list
- `RETM`: Retry measurements
- `MCTR`: Cell trace

### Huawei (U2020)
- `DSP CELLHO`: Handover statistics
- `DSP CELLALG`: Cell algorithms
- `LST CELL`: Cell parameters
- `DSP ALM`: Alarms

### Nokia (NMS)
- `RXMSP`: Measurement report display
- `RADP`: Radio analysis
- `ALMS`: Alarm status

### Generic (via MM telnet)
- Read OMC database
- Execute vendor-specific commands
- Export performance counters

---

## Emergency Procedures

### Cell Completely Out of Service
1. Check site power and transport
2. Check alarms on Node B and RNC
3. If needed, perform fast restart (Node B reboot)
4. Redirect traffic to neighboring cells

### Sudden High Interference at Multiple Sites
- Suspect external interference
- Contact spectrum monitoring team
- Scan with portable spectrum analyzer
- Coordinate with regulator if needed

### Widespread Outage
- Check MSC/RNC connectivity
- Verify core network elements (SGSN, GGSN)
- Check Iub links (E1/T1, ATM, IP)

---

## Prevention

### Daily:
- Review KPIs (CSSR, HO rate, BLER)
- Check alarm list for new critical alarms

### Weekly:
- Analyze top cells by interference/handover rate
- Review HO success rate per cell pair
- Check RTWP trends

### Monthly:
- Drive test for coverage validation
- Parameter audit
- Neighbor relation review (add missing, delete unnecessary)
- Antenna tilt/azimuth verification

### Quarterly:
- Capacity planning review
- Frequency plan optimization
- Hardware maintenance (filters, amplifiers)

---

## References

- 3GPP TS 25.215: Physical layer measurements (FDD)
- 3GPP TS 25.331: RRC protocol specification
- Vendor-specific OSS manuals
- ITU-T Recommendations for mobile networks
- Operator SOPs (Standard Operating Procedures)
