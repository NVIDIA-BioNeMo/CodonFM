## Description: <br>
Validate, prepare, or run public CodonFM Encodon masked-codon variant scoring and review compatibility of its scoring workflows. <br>

This skill is ready for commercial/non-commercial use. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
Apache 2.0 <br>
## Use Case: <br>
Developers and computational biologists who need to validate coding-sequence variant inputs, prepare masked-codon scoring commands, or run inference with public CodonFM Encodon models. <br>

### Deployment Geography for Use: <br>
Global <br>

## Requirements / Dependencies: <br>
**Requires API Key or External Credential:** [Not Specified] <br>
**Credential Type(s):** [None identified] <br>

Do not include secrets in prompts/logs/output; use least-privilege credentials; rotate keys as appropriate. <br>

## Known Risks and Mitigations: <br>
Risk: Review before execution as proposals could introduce incorrect or misleading guidance into skills. <br>
Mitigation: Review and scan skill before deployment. <br>

## Reference(s): <br>
- [NV-CodonFM-Encodon-80M-v1 (Hugging Face)](https://huggingface.co/nvidia/NV-CodonFM-Encodon-80M-v1) <br>
- [NV-CodonFM-Encodon-600M-v1 (Hugging Face)](https://huggingface.co/nvidia/NV-CodonFM-Encodon-600M-v1) <br>
- [NV-CodonFM-Encodon-1B-v1 (Hugging Face)](https://huggingface.co/nvidia/NV-CodonFM-Encodon-1B-v1) <br>
- [NV-CodonFM-Encodon-Cdwt-1B-v1 (Hugging Face)](https://huggingface.co/nvidia/NV-CodonFM-Encodon-Cdwt-1B-v1) <br>
- [CodonFM Encodon on NGC](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/clara/models/nv_codonfm_encodon) <br>
- [NVIDIA Deep Bio Research](https://research.nvidia.com/labs/dbr) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Analysis, Files] <br>
**Output Format:** [Markdown with inline bash code blocks] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [Prediction arrays in NumPy format (ref_likelihoods_merged.npy, alt_likelihoods_merged.npy, likelihood_ratios_merged.npy, ids_merged.npy)] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-5`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
3 evaluation tasks (2 positive, 1 negative), each with 3 attempts per task in isolated sandbox pods. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Checks for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Checks final-answer correctness against the reference answer. <br>
- Discoverability: Checks whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- Effectiveness: Equal-weight mean of goal completion (goal_accuracy) and expected workflow adherence (behavior_check). <br>
- Efficiency: 50% tool-call productivity (skill_efficiency) and 50% token efficiency. <br>

Underlying evaluation signals used in this run: <br>
- `security`: Unsafe operations, secret leakage, and unauthorized access. <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `skill_execution`: Whether the expected skill was selected and the workflow executed. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `skill_efficiency`: Tool-call productivity; routing is scored under Discoverability. <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Measure | Claude Code (Baseline → Skill Uplift) | Codex (Baseline → Skill Uplift) |
|---|---:|---:|
| Overall | 93.3% | 92.2% |
| Security | 100.0% → 100.0% (±0.0 pts) | 100.0% → 100.0% (±0.0 pts) |
| Correctness | 100.0% → 100.0% (±0.0 pts) | 100.0% → 100.0% (±0.0 pts) |
| Discoverability | 87.5% | 75.0% |
| Effectiveness | 96.7% → 93.3% (-3.4 pts) | 93.3% → 96.7% (+3.4 pts) |
| Efficiency | 85.6% | 89.3% |

## Skill Version(s): <br>
29194e8 (source: git SHA, committed 2026-09-18) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
