Status and AI-evidence indicators — the chips, meters and citations that surface risk and model confidence throughout Nexus.

```jsx
<StatusChip tone="critical" icon="warning">High Risk</StatusChip>
<StatusChip tone="verified">Verified</StatusChip>
<ConfidenceMeter value={94} label="Synth Confidence" />
<EvidenceCitation index={1} snippet="MRI Abdomen W/O Contrast — Jan 5" onView={fn} />
```

`StatusChip` tones: critical / warning / stable / verified / info / neutral. `ConfidenceMeter` auto-colors by value (≥90 green, ≥70 blue, ≥50 amber, else red). `EvidenceCitation` is the bordered source callout used under agent answers.
