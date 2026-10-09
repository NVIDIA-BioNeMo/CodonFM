# SPDX-FileCopyrightText: Copyright (c) 2025 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from unittest.mock import MagicMock

import pytest

import src.tasks as tasks


def _mock_runtime(monkeypatch):
    trainer = MagicMock()
    model = MagicMock()
    data = MagicMock()
    monkeypatch.setattr(tasks, "Trainer", MagicMock(return_value=trainer))
    monkeypatch.setattr(tasks, "seed_everything", lambda *args, **kwargs: None)
    monkeypatch.setattr(tasks, "create_strategy_from_config", lambda kwargs: kwargs)
    config = {
        "log": None,
        "data": data,
        "trainer": {},
        "model": model,
        "callbacks": {},
    }
    return config, trainer, model, data


def test_train_resumes_trusted_checkpoint(tmp_path, monkeypatch):
    config, trainer, model, _ = _mock_runtime(monkeypatch)
    checkpoint_path = tmp_path / "resume.ckpt"
    checkpoint_path.write_bytes(b"checkpoint")
    state = {"state_dict": {"weight": "value"}}
    loader = MagicMock(return_value=state)
    aliases = MagicMock()
    monkeypatch.setattr(tasks, "load_trusted_checkpoint", loader)
    monkeypatch.setattr(tasks, "install_legacy_checkpoint_aliases", aliases)

    tasks.train(
        config,
        ckpt_path=str(checkpoint_path),
        seed=1,
        config_dict={},
        out_dir=str(tmp_path / "train"),
    )

    loader.assert_called_once_with(str(checkpoint_path))
    model.configure_model.assert_called_once_with(state_dict=state["state_dict"])
    assert trainer.fit.call_args.kwargs["ckpt_path"] == str(checkpoint_path)
    assert trainer.fit.call_args.kwargs["weights_only"] is False
    aliases.assert_called_once_with()


def test_finetune_preserves_safetensors_loading(tmp_path, monkeypatch):
    config, trainer, model, _ = _mock_runtime(monkeypatch)
    pretrained_path = tmp_path / "pretrained.safetensors"
    pretrained_path.write_bytes(b"safetensors")
    checkpoint_path = tmp_path / "finetuned.ckpt"
    state = {"weight": "value"}
    safetensors_loader = MagicMock(return_value=state)
    trusted_loader = MagicMock()
    aliases = MagicMock()
    monkeypatch.setattr(tasks, "load_file", safetensors_loader)
    monkeypatch.setattr(tasks, "load_trusted_checkpoint", trusted_loader)
    monkeypatch.setattr(tasks, "install_legacy_checkpoint_aliases", aliases)

    tasks.finetune(
        config,
        pretrained_ckpt_path=str(pretrained_path),
        seed=1,
        resume_trainer_state=False,
        config_dict={},
        out_dir=str(tmp_path / "finetune"),
        ckpt_path=str(checkpoint_path),
    )

    safetensors_loader.assert_called_once_with(str(pretrained_path))
    trusted_loader.assert_not_called()
    model.configure_model.assert_called_once_with(state_dict=state)
    assert trainer.fit.call_args.kwargs["ckpt_path"] is None
    assert "weights_only" not in trainer.fit.call_args.kwargs
    aliases.assert_not_called()


def test_finetune_resumes_trusted_lightning_checkpoint(tmp_path, monkeypatch):
    config, trainer, model, _ = _mock_runtime(monkeypatch)
    pretrained_path = tmp_path / "pretrained.ckpt"
    pretrained_path.write_bytes(b"checkpoint")
    checkpoint_path = tmp_path / "finetuned.ckpt"
    state = {"state_dict": {"weight": "value"}}
    loader = MagicMock(return_value=state)
    aliases = MagicMock()
    monkeypatch.setattr(tasks, "load_trusted_checkpoint", loader)
    monkeypatch.setattr(tasks, "install_legacy_checkpoint_aliases", aliases)

    tasks.finetune(
        config,
        pretrained_ckpt_path=str(pretrained_path),
        seed=1,
        resume_trainer_state=True,
        config_dict={},
        out_dir=str(tmp_path / "finetune"),
        ckpt_path=str(checkpoint_path),
    )

    loader.assert_called_once_with(str(pretrained_path))
    model.configure_model.assert_called_once_with(state_dict=state["state_dict"])
    assert trainer.fit.call_args.kwargs["ckpt_path"] == str(pretrained_path)
    assert trainer.fit.call_args.kwargs["weights_only"] is False
    aliases.assert_called_once_with()


def test_evaluate_restores_datamodule_state_from_trusted_checkpoint(
    tmp_path, monkeypatch
):
    config, trainer, model, data = _mock_runtime(monkeypatch)
    checkpoint_path = tmp_path / "model.ckpt"
    checkpoint_path.write_bytes(b"checkpoint")
    datamodule_state = {"consumed_samples": 8, "global_step": 2}
    state = {"MagicMock": datamodule_state}
    loader = MagicMock(return_value=state)
    monkeypatch.setattr(tasks, "load_trusted_checkpoint", loader)
    data.init_global_step = 2

    tasks.evaluate(
        config,
        config_dict={},
        model_ckpt_path=str(checkpoint_path),
        out_dir=str(tmp_path / "eval"),
    )

    loader.assert_called_once_with(str(checkpoint_path))
    data.load_state_dict.assert_called_once_with(datamodule_state)
    assert model.prediction_counter == 2
    trainer.predict.assert_called_once_with(
        model,
        datamodule=data,
        return_predictions=False,
    )


def test_evaluate_does_not_unpickle_safetensors(tmp_path, monkeypatch):
    config, _, _, data = _mock_runtime(monkeypatch)
    checkpoint_path = tmp_path / "model.safetensors"
    checkpoint_path.write_bytes(b"safetensors")
    loader = MagicMock()
    monkeypatch.setattr(tasks, "load_trusted_checkpoint", loader)

    tasks.evaluate(
        config,
        config_dict={},
        model_ckpt_path=str(checkpoint_path),
        out_dir=str(tmp_path / "eval"),
    )

    loader.assert_not_called()
    data.load_state_dict.assert_not_called()


def test_finetune_without_pretrained_checkpoint_starts_from_scratch(
    tmp_path, monkeypatch
):
    config, trainer, model, _ = _mock_runtime(monkeypatch)
    aliases = MagicMock()
    monkeypatch.setattr(tasks, "install_legacy_checkpoint_aliases", aliases)

    tasks.finetune(
        config,
        pretrained_ckpt_path=None,
        seed=1,
        resume_trainer_state=False,
        config_dict={},
        out_dir=str(tmp_path / "finetune"),
        ckpt_path=str(tmp_path / "finetuned.ckpt"),
    )

    model.configure_model.assert_called_once_with()
    assert trainer.fit.call_args.kwargs["ckpt_path"] is None
    assert "weights_only" not in trainer.fit.call_args.kwargs
    aliases.assert_not_called()


def test_finetune_rejects_unknown_checkpoint_format(tmp_path, monkeypatch):
    config, _, _, _ = _mock_runtime(monkeypatch)
    pretrained_path = tmp_path / "pretrained.pt"
    pretrained_path.write_bytes(b"checkpoint")
    loader = MagicMock()
    monkeypatch.setattr(tasks, "load_trusted_checkpoint", loader)

    with pytest.raises(ValueError, match=r"\.ckpt or \.safetensors"):
        tasks.finetune(
            config,
            pretrained_ckpt_path=str(pretrained_path),
            seed=1,
            resume_trainer_state=False,
            config_dict={},
            out_dir=str(tmp_path / "finetune"),
            ckpt_path=str(tmp_path / "finetuned.ckpt"),
        )

    loader.assert_not_called()
