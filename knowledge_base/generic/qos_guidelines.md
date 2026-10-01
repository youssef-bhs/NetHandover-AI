# QoS Prediction Guidance

## QoS Classes (Heuristic Ranges)

These ranges provide a practical interpretation for QoS outputs using common KPIs.
They are indicative and should be calibrated to your network.

| Class | RSRP (dBm) | RSRQ (dB) | DL Throughput | Interpretation |
|------|------------|-----------|---------------|----------------|
| Tres bonne | > -80 | > -7 | > 20 Mbps | Excellent user experience |
| Acceptable | -80 to -95 | -7 to -11 | 5-20 Mbps | Usable with some limits |
| Assez bien | -95 to -105 | -11 to -15 | 1-5 Mbps | Fair, watch for congestion |
| Mauvaise | < -105 | < -15 | < 1 Mbps | Poor, likely user impact |

## Common QoS Degradations

- Low RSRP: coverage hole or excessive path loss
- Low RSRQ with decent RSRP: interference or high load
- Low throughput: congestion, scheduling limits, backhaul constraints

## Recommended Actions

1. Validate PCI and band configuration for overshoot or interference sources
2. Check RSRP/RSRQ trends across time to isolate interference vs coverage
3. For persistent Mauvaise QoS, consider tilt/power adjustments or capacity relief
4. If throughput is the main issue, review scheduler limits and backhaul utilization

## Notes

QoS is multi-factor. Use RSRP/RSRQ thresholds together with throughput to identify
whether the primary issue is coverage, interference, or capacity.
