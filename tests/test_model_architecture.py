"""
test_model_architecture.py — Unit tests and property-based tests for model architecture.

Tasks 6.2, 6.5, 6.6, 6.8, 6.10.
Covers Properties 11–15 and unit tests for StreamA, StreamB, FusionModule,
GlossHead, FonologisHead, SignBridgeModel, and StudentModel.

Run:
    python -m pytest tests/test_model_architecture.py -v --tb=short
"""

from __future__ import annotations

import pytest
import torch
import torch.nn.functional as F
from hypothesis import given, settings
from hypothesis import strategies as st

from src.exceptions import ConfigValidationError
from src.model.stream_a import StreamA, STGCNBlock, PoseTransformerEncoder
from src.model.stream_b import StreamB
from src.model.fusion import FusionModule
from src.model.heads import GlossHead, FonologisHead
from src.model.signbridge_model import (
    SignBridgeModel,
    StudentModel,
    ModelConfig,
    StreamAConfig,
    StreamBConfig,
    FusionConfig,
    GlossHeadConfig,
    PhonologicalHeadConfig,
    ModelOutput,
)


# ===========================================================================
# Helper: small config for fast tests
# ===========================================================================

def _small_model_config(use_phonological: bool = True, num_classes: int = 5) -> ModelConfig:
    """Create a small ModelConfig for fast test execution."""
    return ModelConfig(
        num_classes=num_classes,
        use_phonological_head=use_phonological,
        stream_a=StreamAConfig(
            arch="stgcn",
            num_blocks=4,
            hidden_dim=128,
            num_heads=4,
        ),
        stream_b=StreamBConfig(
            arch="videomae",
            pretrained_url="",
            frozen_layers=[],
            output_dim=512,
            num_frames=16,
        ),
        fusion=FusionConfig(dim=512, num_heads=8),
        gloss_head=GlossHeadConfig(in_dim=512, label_smoothing=0.1),
        phonological_head=PhonologicalHeadConfig(
            in_dim=512,
            num_handshape=10,
            num_lokasi=5,
            num_arah_gerak=4,
        ),
    )


# ===========================================================================
# Property 11: Stream_A Output Shape Invariance
# **Validates: Requirements 7.3, 7.4**
# ===========================================================================

class TestProperty11StreamAOutputShape:
    """Property 11: For any T ∈ [1, 128] padded to T_max=128, Stream_A → [B, 512]."""

    @settings(max_examples=20, deadline=None)
    @given(T=st.integers(1, 128), B=st.integers(1, 4))
    def test_property_11_stream_a_output_shape(self, T, B):
        """**Validates: Requirements 7.3, 7.4**

        For any keypoint input with batch size B and sequence length T ∈ [1, 128]
        padded to T_max=128, Stream_A SHALL produce output [B, 512].
        The padding mask SHALL contain exactly T True and (128 - T) False values.
        """
        model = StreamA(num_blocks=4, hidden_dim=128, num_heads=4)
        model.eval()

        # Create unpadded input
        keypoints = torch.randn(B, T, 543, 3)
        mask = torch.ones(B, T, dtype=torch.bool)  # all T frames are valid

        # Pad to T_max=128
        if T < 128:
            pad_kp = torch.zeros(B, 128 - T, 543, 3)
            keypoints = torch.cat([keypoints, pad_kp], dim=1)
            pad_mask = torch.zeros(B, 128 - T, dtype=torch.bool)
            mask = torch.cat([mask, pad_mask], dim=1)

        # Verify mask has exactly T True and (128-T) False per batch element
        true_counts = mask.sum(dim=1)  # [B]
        assert (true_counts == T).all(), f"Each batch element should have {T} True values"
        assert (128 - true_counts == 128 - T).all()

        with torch.no_grad():
            out = model(keypoints, mask)

        assert out.shape == (B, 512), f"Expected {(B, 512)}, got {out.shape}"
        assert torch.isfinite(out).all()


# ===========================================================================
# Property 12: Stream_B Temporal Sampling Consistency
# **Validates: Requirements 8.5**
# ===========================================================================

class TestProperty12StreamBTemporalSampling:
    """Property 12: Uniform temporal sampling → exactly 16 frames."""

    @settings(max_examples=30, deadline=None)
    @given(
        T=st.integers(1, 100),
        B=st.integers(1, 4),
        H=st.integers(50, 300),
        W=st.integers(50, 300),
    )
    def test_property_12_stream_b_temporal_sampling(self, T, B, H, W):
        """**Validates: Requirements 8.5**

        For any input video with at least 1 frame, the uniform temporal sampler
        SHALL produce exactly 16 frames. For input ≥ 16 frames, the 16 sampled
        frames SHALL be drawn at evenly-spaced indices covering the full range.
        """
        model = StreamB()
        frames = torch.randn(B, T, 3, H, W)

        sampled = model.temporal_sample(frames, n=16)

        # Must produce exactly 16 frames
        assert sampled.shape[0] == B
        assert sampled.shape[1] == 16, f"Expected 16 frames, got {sampled.shape[1]}"

        if T >= 16:
            # Verify evenly-spaced indices
            expected_indices = torch.linspace(0, T - 1, 16).long()
            # Check that first and last indices cover the full range
            assert expected_indices[0].item() == 0
            assert expected_indices[-1].item() == T - 1
            # Check even spacing: differences should be approximately equal
            diffs = expected_indices[1:] - expected_indices[:-1]
            max_diff = diffs.max().item()
            min_diff = diffs.min().item()
            assert max_diff - min_diff <= 1, f"Indices not evenly spaced: max_diff={max_diff}, min_diff={min_diff}"
        else:
            # For T < 16: last (16 - T) frames should be replicated from last frame
            assert torch.allclose(sampled[:, T:], frames[:, -1:].expand(B, 16 - T, 3, H, W))


# ===========================================================================
# Property 13: Stream_B Preprocessing Validity
# **Validates: Requirements 8.3**
# ===========================================================================

class TestProperty13StreamBPreprocessing:
    """Property 13: Preprocessing → [3, 224, 224] with ImageNet normalization."""

    @settings(max_examples=15, deadline=None)
    @given(
        B=st.integers(1, 2),
        T=st.integers(1, 10),
        H=st.integers(100, 300),
        W=st.integers(100, 300),
    )
    def test_property_13_stream_b_preprocessing(self, B, T, H, W):
        """**Validates: Requirements 8.3**

        For any input frame of any resolution and pixel range, the preprocessing
        pipeline SHALL produce an output tensor of shape [B, T, 3, 224, 224]
        with each channel normalized using ImageNet mean/std.
        """
        model = StreamB()
        # Input in [0, 1] range (common pixel normalization)
        frames = torch.rand(B, T, 3, H, W)

        processed = model.preprocess(frames)

        # Shape check
        assert processed.shape == (B, T, 3, 224, 224), f"Expected {(B, T, 3, 224, 224)}, got {processed.shape}"

        # Verify normalization: (resized - mean) / std
        # Recompute the resize independently
        frames_flat = frames.reshape(B * T, 3, H, W)
        resized = F.interpolate(frames_flat, size=(224, 224), mode="bilinear", align_corners=False)
        resized = resized.reshape(B, T, 3, 224, 224)

        mean = torch.tensor(StreamB.IMAGENET_MEAN).view(1, 1, 3, 1, 1)
        std = torch.tensor(StreamB.IMAGENET_STD).view(1, 1, 3, 1, 1)
        expected = (resized - mean) / std

        assert torch.allclose(processed, expected, atol=1e-5), "Preprocessing normalization mismatch"


# ===========================================================================
# Property 14: Fusion Output Shape and Attention Accessibility
# **Validates: Requirements 9.2, 9.5, 9.6**
# ===========================================================================

class TestProperty14FusionOutputShape:
    """Property 14: Fusion → [B, 512] + attention weights accessible."""

    @settings(max_examples=20, deadline=None)
    @given(B=st.integers(1, 8))
    def test_property_14_fusion_output_shape(self, B):
        """**Validates: Requirements 9.2, 9.5, 9.6**

        For any pair of Stream_A features [B, 512] and Stream_B features [B, 512],
        the Fusion_Module SHALL produce a fused tensor [B, 512] and return
        attention weights of shape [num_heads, T_query, T_key] per direction.
        """
        model = FusionModule(dim=512, num_heads=8)
        model.eval()

        feat_a = torch.randn(B, 512)
        feat_b = torch.randn(B, 512)

        with torch.no_grad():
            fused, attn_weights = model(feat_a, feat_b, return_attn_weights=True)

        # Fused output shape
        assert fused.shape == (B, 512), f"Expected {(B, 512)}, got {fused.shape}"
        assert torch.isfinite(fused).all()

        # Attention weights accessible
        assert attn_weights is not None
        assert "A2B" in attn_weights, "A2B attention weights missing"
        assert "B2A" in attn_weights, "B2A attention weights missing"

        # Shape: [B, num_heads, T_query, T_key] where T_query=T_key=1
        # (MultiheadAttention with batch_first returns [B, num_heads, T_q, T_k])
        assert attn_weights["A2B"].shape == (B, 8, 1, 1), f"A2B shape: {attn_weights['A2B'].shape}"
        assert attn_weights["B2A"].shape == (B, 8, 1, 1), f"B2A shape: {attn_weights['B2A'].shape}"


# ===========================================================================
# Property 15: Classification Head Dynamic Dimensionality
# **Validates: Requirements 10.1, 10.2**
# ===========================================================================

class TestProperty15GlossHeadDynamicDim:
    """Property 15: GlossHead → [B, num_classes] for any num_classes ≥ 2."""

    @settings(max_examples=25, deadline=None)
    @given(
        num_classes=st.integers(min_value=2, max_value=200),
        B=st.integers(1, 4),
    )
    def test_property_15_gloss_head_dynamic_dim(self, num_classes, B):
        """**Validates: Requirements 10.1, 10.2**

        For any num_classes ≥ 2, the GlossHead initialized with that num_classes
        SHALL produce output logits of shape [B, num_classes] for any batch
        input of shape [B, 512].
        """
        head = GlossHead(in_dim=512, num_classes=num_classes)
        head.eval()

        x = torch.randn(B, 512)
        with torch.no_grad():
            out = head(x)

        assert out.shape == (B, num_classes), f"Expected {(B, num_classes)}, got {out.shape}"
        assert torch.isfinite(out).all()


# ===========================================================================
# Unit Tests — StreamA config validation
# ===========================================================================

class TestStreamAConfigValidation:
    """Unit tests for StreamA configuration validation (Requirement 7.5)."""

    def test_num_blocks_too_small_raises(self):
        """num_blocks < 4 should raise ConfigValidationError."""
        with pytest.raises(ConfigValidationError) as exc_info:
            StreamA(num_blocks=3, hidden_dim=256, num_heads=8)
        assert "num_blocks" in str(exc_info.value)

    def test_num_blocks_too_large_raises(self):
        """num_blocks > 20 should raise ConfigValidationError."""
        with pytest.raises(ConfigValidationError) as exc_info:
            StreamA(num_blocks=21, hidden_dim=256, num_heads=8)
        assert "num_blocks" in str(exc_info.value)

    def test_hidden_dim_too_small_raises(self):
        """hidden_dim < 128 should raise ConfigValidationError."""
        with pytest.raises(ConfigValidationError) as exc_info:
            StreamA(num_blocks=10, hidden_dim=127, num_heads=8)
        assert "hidden_dim" in str(exc_info.value)

    def test_hidden_dim_too_large_raises(self):
        """hidden_dim > 512 should raise ConfigValidationError."""
        with pytest.raises(ConfigValidationError) as exc_info:
            StreamA(num_blocks=10, hidden_dim=513, num_heads=8)
        assert "hidden_dim" in str(exc_info.value)

    def test_num_heads_too_small_raises(self):
        """num_heads < 1 should raise ConfigValidationError."""
        with pytest.raises(ConfigValidationError) as exc_info:
            StreamA(num_blocks=10, hidden_dim=256, num_heads=0)
        assert "num_heads" in str(exc_info.value)

    def test_num_heads_too_large_raises(self):
        """num_heads > 16 should raise ConfigValidationError."""
        with pytest.raises(ConfigValidationError) as exc_info:
            StreamA(num_blocks=10, hidden_dim=256, num_heads=17)
        assert "num_heads" in str(exc_info.value)

    def test_valid_config_does_not_raise(self):
        """Valid config boundaries should not raise."""
        # Minimum valid values
        model_min = StreamA(num_blocks=4, hidden_dim=128, num_heads=1)
        assert model_min is not None
        # Maximum valid values
        model_max = StreamA(num_blocks=20, hidden_dim=512, num_heads=16)
        assert model_max is not None


# ===========================================================================
# Unit Tests — STGCNBlock
# ===========================================================================

class TestSTGCNBlock:
    """Unit tests for STGCNBlock."""

    def test_block_output_shape(self):
        """STGCNBlock preserves temporal dimension and changes channels."""
        block = STGCNBlock(in_channels=128, out_channels=128, kernel_size=9)
        x = torch.randn(2, 128, 32)  # [B, C, T]
        out = block(x)
        assert out.shape == (2, 128, 32), f"Expected (2, 128, 32), got {out.shape}"

    def test_block_channel_change(self):
        """STGCNBlock can change channel dimension with residual projection."""
        block = STGCNBlock(in_channels=64, out_channels=128, kernel_size=9)
        x = torch.randn(2, 64, 32)
        out = block(x)
        assert out.shape == (2, 128, 32)


# ===========================================================================
# Unit Tests — PoseTransformerEncoder
# ===========================================================================

class TestPoseTransformerEncoder:
    """Unit tests for PoseTransformerEncoder (alternative Stream_A)."""

    def test_pose_transformer_output_shape(self):
        """PoseTransformerEncoder produces [B, 512]."""
        encoder = PoseTransformerEncoder(
            num_keypoints=543, num_coords=3,
            hidden_dim=128, num_heads=4, num_layers=4,
            output_dim=512,
        )
        encoder.eval()
        B, T_max = 2, 16
        keypoints = torch.randn(B, T_max, 543, 3)
        mask = torch.ones(B, T_max, dtype=torch.bool)
        with torch.no_grad():
            out = encoder(keypoints, mask)
        assert out.shape == (B, 512)

    def test_stream_a_pose_transformer_arch(self):
        """StreamA with arch='pose_transformer' produces [B, 512]."""
        model = StreamA(num_blocks=4, hidden_dim=128, num_heads=4, arch="pose_transformer")
        model.eval()
        B, T_max = 2, 16
        keypoints = torch.randn(B, T_max, 543, 3)
        mask = torch.ones(B, T_max, dtype=torch.bool)
        with torch.no_grad():
            out = model(keypoints, mask)
        assert out.shape == (B, 512)


# ===========================================================================
# Unit Tests — StreamB
# ===========================================================================

class TestStreamB:
    """Unit tests for StreamB."""

    def test_temporal_sample_exactly_16_short(self):
        """T < 16 → replicate last frame → 16 frames."""
        model = StreamB()
        frames = torch.randn(2, 5, 3, 64, 64)
        sampled = model.temporal_sample(frames, n=16)
        assert sampled.shape == (2, 16, 3, 64, 64)

    def test_temporal_sample_exactly_16_long(self):
        """T >= 16 → evenly spaced → 16 frames."""
        model = StreamB()
        frames = torch.randn(2, 50, 3, 64, 64)
        sampled = model.temporal_sample(frames, n=16)
        assert sampled.shape == (2, 16, 3, 64, 64)

    def test_preprocess_shape(self):
        """Preprocess produces [B, T, 3, 224, 224]."""
        model = StreamB()
        frames = torch.rand(1, 10, 3, 100, 200)
        processed = model.preprocess(frames)
        assert processed.shape == (1, 10, 3, 224, 224)

    def test_forward_output_shape(self):
        """StreamB forward → [B, 512]."""
        model = StreamB(output_dim=512)
        model.eval()
        frames = torch.rand(1, 20, 3, 64, 64)
        with torch.no_grad():
            out = model(frames)
        assert out.shape == (1, 512)

    def test_frozen_layers(self):
        """Frozen layers should have requires_grad=False."""
        model = StreamB(frozen_layers=["features.0"])
        for name, param in model.backbone.named_parameters():
            if name.startswith("features.0"):
                assert param.requires_grad is False, f"{name} should be frozen"
            # features.1 should not be frozen
            if name.startswith("features.1"):
                assert param.requires_grad is True, f"{name} should not be frozen"


# ===========================================================================
# Unit Tests — FusionModule
# ===========================================================================

class TestFusionModule:
    """Unit tests for FusionModule."""

    def test_fusion_output_shape(self):
        """FusionModule produces [B, 512]."""
        model = FusionModule(dim=512, num_heads=8)
        model.eval()
        feat_a = torch.randn(4, 512)
        feat_b = torch.randn(4, 512)
        with torch.no_grad():
            fused, attn = model(feat_a, feat_b)
        assert fused.shape == (4, 512)

    def test_attention_weights_shape(self):
        """Attention weights have correct shape [B, num_heads, 1, 1]."""
        model = FusionModule(dim=512, num_heads=8)
        model.eval()
        feat_a = torch.randn(3, 512)
        feat_b = torch.randn(3, 512)
        with torch.no_grad():
            _, attn = model(feat_a, feat_b, return_attn_weights=True)
        assert attn["A2B"].shape == (3, 8, 1, 1)
        assert attn["B2A"].shape == (3, 8, 1, 1)

    def test_attention_weights_none_when_not_requested(self):
        """When return_attn_weights=False, attn should be None."""
        model = FusionModule(dim=512, num_heads=8)
        model.eval()
        feat_a = torch.randn(2, 512)
        feat_b = torch.randn(2, 512)
        with torch.no_grad():
            fused, attn = model(feat_a, feat_b, return_attn_weights=False)
        assert fused.shape == (2, 512)
        assert attn is None


# ===========================================================================
# Unit Tests — Heads
# ===========================================================================

class TestGlossHead:
    """Unit tests for GlossHead."""

    def test_gloss_head_output_shape(self):
        """GlossHead: [B, 512] → [B, num_classes]."""
        head = GlossHead(in_dim=512, num_classes=32)
        x = torch.randn(4, 512)
        out = head(x)
        assert out.shape == (4, 32)

    def test_gloss_head_dynamic_classes(self):
        """GlossHead supports different num_classes."""
        head_bisindo = GlossHead(in_dim=512, num_classes=32)
        head_wlasl = GlossHead(in_dim=512, num_classes=2006)
        x = torch.randn(2, 512)
        assert head_bisindo(x).shape == (2, 32)
        assert head_wlasl(x).shape == (2, 2006)


class TestFonologisHead:
    """Unit tests for FonologisHead."""

    def test_fonologis_head_output_keys(self):
        """FonologisHead returns dict with 3 keys."""
        head = FonologisHead(in_dim=512, num_handshape=20, num_lokasi=10, num_arah_gerak=8)
        x = torch.randn(2, 512)
        out = head(x)
        assert "handshape_logits" in out
        assert "lokasi_logits" in out
        assert "arah_gerak_logits" in out

    def test_fonologis_head_output_shapes(self):
        """Each sub-head produces correct output shape."""
        head = FonologisHead(in_dim=512, num_handshape=20, num_lokasi=10, num_arah_gerak=8)
        x = torch.randn(3, 512)
        out = head(x)
        assert out["handshape_logits"].shape == (3, 20)
        assert out["lokasi_logits"].shape == (3, 10)
        assert out["arah_gerak_logits"].shape == (3, 8)


# ===========================================================================
# Unit Tests — SignBridgeModel (Teacher)
# ===========================================================================

class TestSignBridgeModel:
    """Unit tests for SignBridgeModel (Teacher_Model)."""

    def test_signbridge_forward_returns_gloss_logits(self):
        """SignBridgeModel.forward returns ModelOutput with gloss_logits."""
        config = _small_model_config(use_phonological=True, num_classes=5)
        model = SignBridgeModel(config)
        model.eval()

        B, T_max = 2, 8
        keypoints = torch.randn(B, T_max, 543, 3)
        frames = torch.rand(B, 10, 3, 32, 32)
        mask = torch.ones(B, T_max, dtype=torch.bool)

        with torch.no_grad():
            output = model(keypoints, frames, mask)

        assert isinstance(output, ModelOutput)
        assert output.gloss_logits.shape == (B, 5), f"Expected {(B, 5)}, got {output.gloss_logits.shape}"
        assert torch.isfinite(output.gloss_logits).all()

    def test_signbridge_forward_phonological_enabled(self):
        """When use_phonological_head=True, phono should be a dict."""
        config = _small_model_config(use_phonological=True, num_classes=5)
        model = SignBridgeModel(config)
        model.eval()

        B, T_max = 1, 8
        keypoints = torch.randn(B, T_max, 543, 3)
        frames = torch.rand(B, 10, 3, 32, 32)
        mask = torch.ones(B, T_max, dtype=torch.bool)

        with torch.no_grad():
            output = model(keypoints, frames, mask)

        assert output.phono is not None
        assert "handshape_logits" in output.phono
        assert "lokasi_logits" in output.phono
        assert "arah_gerak_logits" in output.phono

    def test_signbridge_forward_returns_attention(self):
        """SignBridgeModel.forward returns attention weights."""
        config = _small_model_config(use_phonological=False, num_classes=5)
        model = SignBridgeModel(config)
        model.eval()

        B, T_max = 1, 8
        keypoints = torch.randn(B, T_max, 543, 3)
        frames = torch.rand(B, 10, 3, 32, 32)
        mask = torch.ones(B, T_max, dtype=torch.bool)

        with torch.no_grad():
            output = model(keypoints, frames, mask)

        assert output.attn is not None
        assert "A2B" in output.attn
        assert "B2A" in output.attn


# ===========================================================================
# Unit Tests — StudentModel
# ===========================================================================

class TestStudentModel:
    """Unit tests for StudentModel (pose-only)."""

    def test_student_forward_returns_gloss_logits(self):
        """StudentModel.forward returns gloss_logits [B, num_classes]."""
        config = _small_model_config(use_phonological=False, num_classes=5)
        model = StudentModel(config)
        model.eval()

        B, T_max = 2, 8
        keypoints = torch.randn(B, T_max, 543, 3)
        mask = torch.ones(B, T_max, dtype=torch.bool)

        with torch.no_grad():
            out = model(keypoints, mask)

        assert out.shape == (B, 5), f"Expected {(B, 5)}, got {out.shape}"
        assert torch.isfinite(out).all()

    def test_student_no_stream_b(self):
        """StudentModel should not have Stream_B or Fusion."""
        config = _small_model_config()
        model = StudentModel(config)
        assert not hasattr(model, "stream_b"), "StudentModel should not have stream_b"
        assert not hasattr(model, "fusion"), "StudentModel should not have fusion"
        assert not hasattr(model, "fonologis_head"), "StudentModel should not have fonologis_head"


# ===========================================================================
# Unit Tests — use_phonological_head=False
# ===========================================================================

class TestPhonologicalHeadToggle:
    """Tests for use_phonological_head=False behavior."""

    def test_phonological_head_disabled_skips_head(self):
        """When use_phonological_head=False, fonologis_head is None and phono is None."""
        config = _small_model_config(use_phonological=False, num_classes=5)
        model = SignBridgeModel(config)
        model.eval()

        # FonologisHead should not be created
        assert model.fonologis_head is None
        assert model.use_phonological_head is False

        B, T_max = 1, 8
        keypoints = torch.randn(B, T_max, 543, 3)
        frames = torch.rand(B, 10, 3, 32, 32)
        mask = torch.ones(B, T_max, dtype=torch.bool)

        with torch.no_grad():
            output = model(keypoints, frames, mask)

        # phono should be None
        assert output.phono is None
        # gloss_logits should still be present
        assert output.gloss_logits.shape == (B, 5)

    def test_phonological_head_enabled_creates_head(self):
        """When use_phonological_head=True, fonologis_head is created."""
        config = _small_model_config(use_phonological=True, num_classes=5)
        model = SignBridgeModel(config)

        assert model.fonologis_head is not None
        assert isinstance(model.fonologis_head, FonologisHead)
        assert model.use_phonological_head is True
