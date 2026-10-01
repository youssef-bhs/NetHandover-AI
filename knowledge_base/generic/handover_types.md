# Handover in UMTS

## Handover Types

### Soft Handover
- **Definition**: UE maintains simultaneous connection with multiple Node Bs (multiple cells)
- **Mode**: Make-before-break
- **Combining**: Selection Diversity (Node B selects best frame) or Maximum Ratio Combining (RNC combines)
- **Usage**: Intra-RNC, same frequency
- **Benefit**: Macro-diversity, improved signal quality, reduced drop rate

### Softer Handover
- **Definition**: Special case of soft handover where multiple cells belong to same Node B
- **Combining**: Done at Node B (faster, less RNC load)
- **Trigger**: Multiple sectors of same site in active set

### Hard Handover
- **Definition**: Break-before-make
- **Usage**: Inter-frequency, Inter-RNC, or to GSM
- **Risk**: Potential drop if target cell not ready
- **Trigger**: Usually by network decision (RNC) based on measurements

## Handover Process

### 1. Measurement Reporting
UE measures:
- **CPICH RSCP** (Common Pilot Channel)
- **CPICH Ec/N0** (quality)
- **Path Loss** = UE TX power - CPICH RSCP
- **Interference** (ISCP - Interference Signal Code Power)

### 2. Event Triggers (3GPP TS 25.331)

#### Event 1A
- Primary CPICH enters reporting range
- Used for addition to active set
- Threshold: F1 (offset from serving cell RSCP)

#### Event 1B
- Primary CPICH leaves reporting range
- Used for removal from active set
- Threshold: F1 + hysteresis

#### Event 1C
- Neighbor CPICH becomes active set candidate
- Better than serving cell by certain threshold
- Triggers soft handover

#### Event 1D
- Path loss change significant
- Used for load balancing

#### Event 1E
- Best cell worsens beyond threshold
- Triggers fallback

#### Event 1F
- Neighbor cell becomes better than serving by offset

## Handover Parameters

### TADD (Threshold for Adding)
- **Definition**: Difference (in dB) between neighbor CPICH RSCP and serving CPICH RSCP required to add neighbor to active set
- **Typical values**: 2-6 dB
- **Low TADD** (2 dB): More aggressive, adds neighbors early → potentially more soft handovers
- **High TADD** (6 dB): Conservative, adds only when neighbor much better → fewer handovers, risk of drops

### T_DROP (Drop Timer)
- **Definition**: Time (in seconds) before removing cell from active set after it fails to meet criteria
- **Typical values**: 1-5 seconds
- **Short T_DROP**: Fast cleanup, reduces active set size, but may cause ping-pong
- **Long T_DROP**: More stable, but keeps unnecessary cells in active set (wastes resources)

### TTT (Time to Trigger)
- **Definition**: Delay before measurement report is sent after condition met
- **Purpose**: Filter out short-term fluctuations
- **Typical values**: 320-640 ms (for event 1A/1C)
- **Long TTT**: Less frequent handovers, but slower response to real degradation

### Hysteresis (HYS)
- **Definition**: Extra margin to prevent ping-pong handovers
- **Example**: Add neighbor when RSCP_neighbor > RSCP_serving + TADD + hysteresis
- **Typical**: 2-4 dB

## Handover Decision Factors

### Radio Conditions
- CPICH RSCP and Ec/N0 of serving and neighbor cells
- Path loss trends
- Signal quality degradation rate

### Neighbor Cell Status
- Is neighbor cell available (not barred)?
- Does neighbor have capacity (load < threshold)?
- Is neighbor cell's antenna correctly configured?

### UE Capabilities
- Does UE support soft handover?
- Active set size limit (typically 3-6 cells)

### Network Load
- Target cell load < admission control threshold
- Avoid handover to congested cells

## When Is Handover Needed?

### Criteria for Handover Decision:

1. **Pilot Pollution Indicator**
   - Multiple cells with |RSCP_serving - RSCP_neighbor| < 5 dB
   - Active set size > 3
   - Cannot determine best serving cell

2. **Coverage Hole**
   - Serving cell RSCP dropping rapidly (> 5 dB in 10 seconds)
   - RSCP < -95 dBm
   - Neighbor cell with RSCP > serving cell by TADD

3. **Quality Degradation**
   - Serving Ec/N0 < -10 dB
   - Neighbor cell Ec/N0 > serving Ec/N0 by threshold
   - After handover, quality may improve

4. **Load Balancing**
   - Serving cell load > 80%
   - Neighbor cell load < 60%
   - Handover to distribute traffic

## Handover Failure Causes

### Common Causes:

1. **Improper Neighbor Planning**
   - Missing neighbor relations in RNC configuration
   - Incorrect PSC/UARFCN for neighbor
   - Neighbor cell not in neighbor list

2. **Timing Issues**
   - TADD too low → ping-pong handovers
   - TTT too short → handover on temporary fade
   - T_DROP too long → active set grows

3. **Coverage Issues**
   - Coverage hole between cells
   - Overshooting cells causing interference
   - Antenna misalignment

4. **Parameter Conflicts**
   - Active set size limit reached
   - Target cell barred (congestion, maintenance)
   - UE in compressed mode (gap measurement conflict)

5. **Hardware/Transport**
   - Iub link failure
   - Node B hardware fault
   - Transport congestion

## Handover Optimization

### Step 1: Data Collection
- HO success/failure rates (per source-target pair)
- HO failure causes (from RNC logs)
- Measurement reports (UE measurements)
- Coverage maps (drive test)

### Step 2: Identify Problem Cells
- Cells with HO failure rate > 5%
- High ping-pong rate (HO → immediate HO back)
- Cells with frequent HO attempts but low success

### Step 3: Parameter Tuning
- **Increase TADD** if ping-pong is high
- **Decrease T_DROP** if active set too large
- **Adjust hysteresis** to add margin
- **Optimize TTT** (increase if HO on noise, decrease if slow to respond)

### Step 4: Antenna/Planning
- Re-orient antennas to improve coverage overlap
- Adjust electrical tilt
- Add missing neighbor relations
- Consider cell splitting if capacity issue

## KPIs to Monitor

- **Handover Success Rate**: Target > 98%
- **Handover Preparation Time**: < 200ms
- **Hard Handover Drop Rate**: < 1%
- **Ping-Pong Rate**: < 2%
- **Active Set Size**: Average 2-3 cells, max 6

## Troubleshooting Commands (Vendor-specific)

Examples for Ericsson, Huawei, Nokia:
- `RLCPC` (Ericsson): Display neighbor cell relations
- `DSP CELLHO` (Huawei): Show handover statistics
- `RXMSP` (Nokia): Measurement report analysis
