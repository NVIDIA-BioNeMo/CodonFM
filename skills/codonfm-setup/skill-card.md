## Description: <br>
Set up the public CodonFM v1 repository and download public Encodon checkpoints. <br>

This skill is ready for commercial/non-commercial use. <br>

## Owner
NVIDIA <br>

### License/Terms of Use: <br>
Apache 2.0 <br>
## Use Case: <br>
Developers and engineers who need to set up the CodonFM development environment, build or launch the CodonFM development container, configure local data and checkpoint mounts, verify GPU access, or download public Encodon 80M, 600M, 1B, or Cdwt-1B weights. <br>

### Deployment Geography for Use: <br>
Global <br>

## Requirements / Dependencies: <br>
**Requires API Key or External Credential:** [No] <br>
**Credential Type(s):** [None] <br>

Do not include secrets in prompts/logs/output; use least-privilege credentials; rotate keys as appropriate. <br>

## Known Risks and Mitigations: <br>
Risk: Review before execution as proposals could introduce incorrect or misleading guidance into skills. <br>
Mitigation: Review and scan skill before deployment. <br>

## Reference(s): <br>
- [CodonFM Encodon 80M on Hugging Face](https://huggingface.co/nvidia/NV-CodonFM-Encodon-80M-v1) <br>
- [CodonFM Encodon 600M on Hugging Face](https://huggingface.co/nvidia/NV-CodonFM-Encodon-600M-v1) <br>
- [CodonFM Encodon 1B on Hugging Face](https://huggingface.co/nvidia/NV-CodonFM-Encodon-1B-v1) <br>
- [CodonFM Encodon Cdwt-1B on Hugging Face](https://huggingface.co/nvidia/NV-CodonFM-Encodon-Cdwt-1B-v1) <br>
- [CodonFM Encodon on NGC](https://catalog.ngc.nvidia.com/orgs/nvidia/teams/clara/models/nv_codonfm_encodon) <br>
- [Hugging Face CLI Documentation](https://huggingface.co/docs/huggingface_hub/en/guides/cli) <br>
- [NVIDIA CUDA Compatibility Guide](https://docs.nvidia.com/deploy/cuda-compatibility/minor-version-compatibility.html) <br>
- [PyTorch 24.10 Release Notes](https://docs.nvidia.com/deeplearning/frameworks/pytorch-release-notes/rel-24-10.html#driver-requirements) <br>
- [NVIDIA DBR Research](https://research.nvidia.com/labs/dbr) <br>


## Skill Output: <br>
**Output Type(s):** [Shell commands, Configuration instructions, Analysis] <br>
**Output Format:** [Markdown with inline bash code blocks] <br>
**Output Parameters:** [1D] <br>
**Other Properties Related to Output:** [None] <br>

## Evaluation Agents Used: <br>
- Claude Code (`aws/anthropic/bedrock-claude-opus-5`) <br>
- Codex (`openai/openai/gpt-5.5`) <br>



## Evaluation Tasks: <br>
Evaluated against 3 positive evaluation tasks, each attempted 3 times in isolated sandbox pods. <br>

## Evaluation Metrics Used: <br>
Reported benchmark dimensions: <br>
- Security: Checks for unsafe operations, secret leakage, and unauthorized access. <br>
- Correctness: Checks final-answer correctness against the reference answer. <br>
- Discoverability: Checks whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- Effectiveness: Checks whether the skill helped complete the user's goal (50% goal accuracy + 50% expected workflow adherence). <br>
- Efficiency: Checks tool-call productivity (50%) and token efficiency (50%). <br>

Underlying evaluation signals used in this run: <br>
- `security`: Unsafe operations, secret leakage, and unauthorized access. <br>
- `accuracy`: Final-answer correctness against the reference answer. <br>
- `skill_execution`: Whether the expected skill was selected, decoys were avoided, and the workflow executed. <br>
- `goal_accuracy`: Whether the user's goal was achieved. <br>
- `behavior_check`: Whether the expected workflow behavior was followed. <br>
- `skill_efficiency`: Tool-call productivity. <br>
- `token_efficiency`: Actual uncached prompt plus completion token usage. <br>



## Evaluation Results: <br>
| Measure | Claude Code (Baseline → Skill Uplift) | Codex (Baseline → Skill Uplift) |
|---|---:|---:|
| Overall | 94.9% | 91.8% |
| Security | 100.0% → 100.0% (±0.0 points) | 50.0% → 100.0% (+50.0 points) |
| Correctness | 100.0% → 100.0% (±0.0 points) | 100.0% → 100.0% (±0.0 points) |
| Discoverability | 98.3% | 80.0% |
| Effectiveness | 91.7% → 87.5% (-4.2 points) | 89.2% → 87.5% (-1.7 points) |
| Efficiency | 88.6% | 91.7% |

## Skill Version(s): <br>
29194e8 (source: git SHA, committed 2026-09-18) <br>

## Ethical Considerations: <br>
NVIDIA believes Trustworthy AI is a shared responsibility and we have established policies and practices to enable development for a wide array of AI applications. When downloaded or used in accordance with our terms of service, developers should work with their internal team to ensure this skill meets requirements for the relevant industry and use case and addresses unforeseen product misuse. <br>

(For Release on NVIDIA Platforms Only) <br>
Please report quality, risk, security vulnerabilities or NVIDIA AI Concerns [here](https://app.intigriti.com/programs/nvidia/nvidiavdp/detail). <br>
