"""
spatial_rgb_augmenter.py — Augmentasi spasial untuk sekuens frame RGB.

Requirements: 5.3
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import zoom


class SpatialRGBAugmenter:
    """
    Augmentasi spasial untuk sekuens frame RGB.

    Input: [T, H, W, 3] numpy float32 dalam rentang [0, 1].
    """

    def __init__(
        self,
        crop_scale_range: tuple[float, float] = (0.8, 1.0),
        brightness: float = 0.2,
        contrast: float = 0.2,
        saturation: float = 0.2,
        seed: int | None = None,
    ) -> None:
        self.crop_scale_range = crop_scale_range
        self.brightness = brightness
        self.contrast = contrast
        self.saturation = saturation
        self.rng = np.random.default_rng(seed)

    # ------------------------------------------------------------------
    # Public methods
    # ------------------------------------------------------------------

    def flip(self, frames: np.ndarray) -> np.ndarray:
        """
        Horizontal flip pada sekuens frame.
        Flip pada sumbu lebar (width): frames[:, :, ::-1, :]

        Parameters
        ----------
        frames : np.ndarray
            Array frame dengan shape [T, H, W, 3].

        Returns
        -------
        np.ndarray
            Frame yang di-flip secara horizontal.
        """
        return frames[:, :, ::-1, :].copy()

    def random_crop_resize(
        self,
        frames: np.ndarray,
        scale: float | None = None,
    ) -> np.ndarray:
        """
        Crop ke scale * ukuran asli dari posisi acak, lalu resize kembali.
        Gunakan numpy slicing untuk crop, scipy.ndimage.zoom untuk resize.

        Parameters
        ----------
        frames : np.ndarray
            Array frame dengan shape [T, H, W, 3].
        scale : float | None
            Skala crop. Jika None, disample dari crop_scale_range.

        Returns
        -------
        np.ndarray
            Frame yang di-crop dan di-resize dengan shape [T, H, W, 3].
        """
        if scale is None:
            scale = float(
                self.rng.uniform(self.crop_scale_range[0], self.crop_scale_range[1])
            )

        T, H, W, C = frames.shape
        crop_h = max(1, int(H * scale))
        crop_w = max(1, int(W * scale))

        # Posisi crop acak
        max_y = H - crop_h
        max_x = W - crop_w
        y0 = int(self.rng.integers(0, max_y + 1)) if max_y > 0 else 0
        x0 = int(self.rng.integers(0, max_x + 1)) if max_x > 0 else 0

        cropped = frames[:, y0 : y0 + crop_h, x0 : x0 + crop_w, :]

        # Resize kembali ke (T, H, W, C)
        zoom_factors = (1.0, H / crop_h, W / crop_w, 1.0)
        resized = zoom(cropped, zoom_factors, order=1)

        # Pastikan shape tepat karena zoom bisa menghasilkan off-by-one
        if resized.shape != (T, H, W, C):
            # Crop atau pad agar sesuai
            out = np.zeros((T, H, W, C), dtype=frames.dtype)
            rh = min(resized.shape[1], H)
            rw = min(resized.shape[2], W)
            out[:, :rh, :rw, :] = resized[:, :rh, :rw, :]
            resized = out

        return np.clip(resized.astype(frames.dtype), 0.0, 1.0)

    def color_jitter(
        self,
        frames: np.ndarray,
        rng: np.random.Generator | None = None,
    ) -> np.ndarray:
        """
        Terapkan brightness ±0.2 dan contrast ±0.2. Clip ke [0, 1].

        Parameters
        ----------
        frames : np.ndarray
            Array frame dengan shape [T, H, W, 3] dalam [0, 1].
        rng : np.random.Generator | None
            Generator acak opsional.

        Returns
        -------
        np.ndarray
            Frame dengan color jitter diterapkan.
        """
        _rng = rng if rng is not None else self.rng

        out = frames.astype(np.float32)

        # Brightness: tambahkan delta
        brightness_delta = float(_rng.uniform(-self.brightness, self.brightness))
        out = out + brightness_delta

        # Contrast: scaling sekitar mean
        contrast_factor = float(_rng.uniform(
            max(0.0, 1.0 - self.contrast),
            1.0 + self.contrast,
        ))
        mean = out.mean()
        out = (out - mean) * contrast_factor + mean

        return np.clip(out, 0.0, 1.0).astype(frames.dtype)

    def augment(
        self,
        frames: np.ndarray,
        was_keypoint_flipped: bool = False,
        rng: np.random.Generator | None = None,
    ) -> np.ndarray:
        """
        Jika was_keypoint_flipped: flip frame. Kemudian terapkan crop + color_jitter.

        Parameters
        ----------
        frames : np.ndarray
            Array frame dengan shape [T, H, W, 3].
        was_keypoint_flipped : bool
            Jika True, terapkan horizontal flip untuk sinkronisasi dengan keypoint.
        rng : np.random.Generator | None
            Generator acak opsional.

        Returns
        -------
        np.ndarray
            Frame yang di-augmentasi dengan shape [T, H, W, 3].
        """
        _rng = rng if rng is not None else self.rng

        out = frames
        if was_keypoint_flipped:
            out = self.flip(out)

        out = self.random_crop_resize(out)
        out = self.color_jitter(out, rng=_rng)

        return out
